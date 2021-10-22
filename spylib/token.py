from abc import ABC, abstractclassmethod, abstractmethod
from asyncio import sleep
from datetime import datetime, timedelta
from math import ceil, floor
from time import monotonic
from typing import Any, ClassVar, Dict, List, Optional

from httpx import AsyncClient, Response
from loguru import logger
from pydantic import BaseModel
from tenacity import retry
from tenacity.retry import retry_if_exception, retry_if_exception_type
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_random

from spylib.constants import (
    MAX_COST_EXCEEDED_ERROR_CODE,
    OPERATION_NAME_REQUIRED_ERROR_MESSAGE,
    THROTTLED_ERROR_CODE,
    WRONG_OPERATION_NAME_ERROR_MESSAGE,
)
from spylib.exceptions import (
    ShopifyCallInvalidError,
    ShopifyError,
    ShopifyExceedingMaxCostError,
    ShopifyThrottledError,
    not_our_fault,
)


class AssociatedUser(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    email_verified: bool
    account_owner: bool
    locale: str
    collaborator: bool


class OfflineTokenResponse(BaseModel):
    access_token: str
    scope: str


class OnlineTokenResponse(BaseModel):
    access_token: str
    scope: str
    expires_in: int
    associated_user_scope: str
    associated_user: AssociatedUser


class Token(ABC, BaseModel):
    """
    Abstract class for token objects. This should never be extended, as you
    should either be using the OfflineTokenABC or the OnlineTokenABC.
    """

    store_name: str
    scope: List[str] = []
    access_token: Optional[str]
    access_token_invalid: bool = False

    api_version: ClassVar[str] = '2021-04'

    rest_bucket_max: int = 80
    rest_bucket: int = rest_bucket_max
    rest_leak_rate: int = 4

    graphql_bucket_max: int = 1000
    graphql_bucket: int = graphql_bucket_max
    graphql_leak_rate: int = 50

    updated_at: float = monotonic()

    client: ClassVar[AsyncClient] = AsyncClient()

    @property
    def oauth_url(self) -> str:
        return f'https://{self.store_name}.myshopify.com/admin/oauth/access_token'

    @property
    def api_url(self) -> str:
        return f'https://{self.store_name}.myshopify.com/admin/api/{self.api_version}'

    class Config:
        arbitrary_types_allowed = True

    # Methods for querying the store

    async def __await_rest_bucket_refill(self):
        self.__fill_rest_bucket()
        while self.rest_bucket <= 1:
            await sleep(1)
            self.__fill_rest_bucket()
        self.rest_bucket -= 1

    def __fill_rest_bucket(self):
        now = monotonic()
        time_since_update = now - self.updated_at
        new_tokens = floor(time_since_update * self.rest_leak_rate)
        if new_tokens > 1:
            self.rest_bucket = min(self.rest_bucket + new_tokens, self.rest_bucket_max)
            self.updated_at = now

    async def __handle_error(self, debug: str, endpoint: str, response: Response):
        """Handle any error that occured when calling Shopify

        If the response has a valid json then return it too.
        """
        msg = (
            f'ERROR in store {self.store_name}: {debug}\n'
            f'API response code: {response.status_code}\n'
            f'API endpoint: {endpoint}\n'
        )
        try:
            jresp = response.json()
        except Exception:
            pass
        else:
            msg += f'API response json: {jresp}\n'

        if 400 <= response.status_code < 500:
            # This appears to be our fault
            raise ShopifyCallInvalidError(msg)

        raise ShopifyError(msg)

    @retry(
        reraise=True,
        wait=wait_random(min=1, max=2),
        stop=stop_after_attempt(5),
        retry=retry_if_exception(not_our_fault),
    )
    async def execute_rest(self, goodstatus, debug, endpoint, **kwargs) -> Dict[str, Any]:
        while True:
            await self.__await_rest_bucket_refill()
            kwargs['url'] = f'{self.api_url}{endpoint}'
            kwargs['headers'] = {'X-Shopify-Access-Token': self.access_token}

            response = await self.client.request(**kwargs)
            if response.status_code == 429:
                # We hit the limit, we are out of tokens
                self.rest_bucket = 0
                continue
            elif 400 <= response.status_code or response.status_code != goodstatus:
                # All errors are handled here
                await self.__handle_error(debug=debug, endpoint=endpoint, response=response)
            else:
                jresp = response.json()
                # Recalculate the rate to be sure we have the right one.
                calllimit = response.headers['X-Shopify-Shop-Api-Call-Limit']
                self.rest_bucket_max = int(calllimit.split('/')[1])
                # In Shopify the bucket is emptied after 20 seconds
                # regardless of the bucket size.
                self.rest_leak_rate = int(self.rest_bucket_max / 20)

            return jresp

    @retry(
        reraise=True,
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(ShopifyThrottledError),
    )
    async def execute_gql(
        self, query: str, variables: Dict[str, Any] = {}, operation_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Simple graphql query executor because python has no decent graphql client"""

        if not self.access_token:
            raise ValueError('Token Undefined')

        url = f'{self.api_url}/graphql.json'

        headers = {
            'Content-type': 'application/json',
            'X-Shopify-Access-Token': self.access_token,
        }

        body = {'query': query, 'variables': variables, 'operationName': operation_name}

        resp = await self.client.post(
            url=url,
            json=body,
            headers=headers,
        )
        jsondata = resp.json()
        if type(jsondata) is not dict:
            raise ValueError('JSON data is not a dictionary')
        if 'Invalid API key or access token' in jsondata.get('errors', ''):
            self.access_token_invalid = True
            logger.warning(
                f'Store {self.store_name}: The Shopify API token is invalid. '
                'Flag the access token as invalid.'
            )
            raise ConnectionRefusedError
        if 'data' not in jsondata and 'errors' in jsondata:
            errorlist = '\n'.join(
                [err['message'] for err in jsondata['errors'] if 'message' in err]
            )
            error_code_list = '\n'.join(
                [
                    err['extensions']['code']
                    for err in jsondata['errors']
                    if 'extensions' in err and 'code' in err['extensions']
                ]
            )
            if MAX_COST_EXCEEDED_ERROR_CODE in error_code_list:
                raise ShopifyExceedingMaxCostError(
                    f'Store {self.store_name}: This query was rejected by the Shopify'
                    f' API, and will never run as written, as the query cost'
                    f' is larger than the max possible query size (>{self.graphql_bucket_max})'
                    ' for Shopify.'
                )
            elif THROTTLED_ERROR_CODE in error_code_list:  # This should be the last condition
                query_cost = jsondata['extensions']['cost']['requestedQueryCost']
                available = jsondata['extensions']['cost']['throttleStatus']['currentlyAvailable']
                rate = jsondata['extensions']['cost']['throttleStatus']['restoreRate']
                sleep_time = ceil((query_cost - available) / rate)
                await sleep(sleep_time)
                raise ShopifyThrottledError
            elif OPERATION_NAME_REQUIRED_ERROR_MESSAGE in errorlist:
                raise ShopifyCallInvalidError(
                    f'Store {self.store_name}: Operation name was required for this query.'
                    'This likely means you have multiple queries within one call '
                    'and you must specify which to run.'
                )
            elif WRONG_OPERATION_NAME_ERROR_MESSAGE.format(operation_name) in errorlist:
                raise ShopifyCallInvalidError(
                    f'Store {self.store_name}: Operation name {operation_name}'
                    'does not exist in the query.'
                )
            else:
                raise ValueError(f'GraphQL query is incorrect:\n{errorlist}')

        return jsondata['data']


class OfflineTokenABC(Token, ABC):
    """
    Offline tokens are used for long term access, and do not have a set expiry.
    """

    @abstractmethod
    async def save(self):
        pass

    @abstractclassmethod
    def load(cls, store_name: str):
        pass


class OnlineTokenABC(Token, ABC):
    """
    Online tokens are used to implement applications that are authenticated with
    a specific user's credentials. These extend on the original token, adding
    in a user, its scope and an expiry time.
    """

    associated_user_id: int
    expires_in: int = 0
    expires_at: datetime = datetime.now() + timedelta(days=0, seconds=expires_in)

    @abstractmethod
    async def save(self):
        """
        This method handles saving the token. By default this does nothing,
        therefore the developer should override this.
        """

    @abstractclassmethod
    def load(cls, store_name: str, associated_user: str):
        """
        This method handles loading the token. By default this does nothing,
        therefore the developer should override this.
        """
