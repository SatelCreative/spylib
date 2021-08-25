from abc import ABC, abstractclassmethod
from asyncio import sleep
from math import ceil, floor
from time import monotonic
from typing import Any, Dict, Optional

from httpx import AsyncClient, Response
from loguru import logger
from tenacity import retry
from tenacity.retry import retry_if_exception, retry_if_exception_type
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_random

from .constants import (
    API_VERSION,
    GRAPH_MAX,
    MAX_COST_EXCEEDED_ERROR_CODE,
    MAX_TOKENS,
    OPERATION_NAME_REQUIRED_ERROR_MESSAGE,
    RATE,
    THROTTLED_ERROR_CODE,
    WRONG_OPERATION_NAME_ERROR_MESSAGE,
)
from .exceptions import (
    ShopifyCallInvalidError,
    ShopifyError,
    ShopifyExceedingMaxCostError,
    ShopifyThrottledError,
    not_our_fault,
)


class Store(ABC):
    """
    This is the store abstract class, the class contains a static class variable for
    the instances that exist.
    """

    _instances: dict = {}

    def __init__(self, store_name: str, access_token: str, staff_id: Optional[str] = None):
        self.store_name = store_name
        self.url = f'https://{store_name}.myshopify.com/admin/api/{API_VERSION}'

        self.client = AsyncClient()
        self.updated_at = monotonic()

        self.reset_access_token(access_token=access_token, staff_id=staff_id)

    @classmethod
    def load(cls, store_name: str, staff_id: Optional[str]):
        """
        Load the store from memory to reuse the tokens. If a staff ID is provided,
        it assumes that you are creating an online token not an offline token.

        WARNING: the name will not be changed here after the first initialization
        """

        access_token = cls.load_offline_token()
        if store_name not in Store._instances:
            if access_token is None:
                message = 'Store {name} ({store_id}) initialized without an access_token'
                logger.error(message)
                raise ValueError(message)
            # Online token if staff_id is specified, else offline
            if staff_id:
                Store._instances[store_name] = Store(
                    store_name=store_name,
                    access_token=access_token,
                    staff_id=staff_id,
                )
            else:
                Store._instances[store_name] = Store(
                    store_name=store_name,
                    access_token=access_token,
                )

        else:
            # Verify if the access token has changed
            if (
                access_token is not None
                and Store._instances[store_name].access_token != access_token
            ):
                if staff_id:
                    Store._instances[store_name].reset_access_token(
                        access_token=access_token,
                        staff_id=staff_id,
                    )
                else:
                    Store._instances[store_name].reset_access_token(
                        access_token=access_token,
                    )
        return Store._instances[store_name]

    @abstractclassmethod
    def save_online_token(self, store_name: str, key: str):
        """
        A method that can be called at the end of the OAuth process to store
        the online token in a location that can be retrieved.
        """
        pass

    @abstractclassmethod
    def save_offline_token(self, store_name: str, key: str):
        """
        A method that can be called at the end of the OAuth process to store
        the offline token in a location that can be retrieved.
        """
        pass

    @abstractclassmethod
    def load_online_token(self, store_name: str):
        """
        Any time the load method is called, this can be used to initialize a store.
        """
        pass

    @abstractclassmethod
    def load_offline_token(self, store_name: str):
        """
        Any time the load method is called, this can be used to initialize a store.
        """
        pass

    def reset_access_token(self, access_token: str, staff_id: Optional[str]):
        """Use this function to initialize a new access token for this store"""
        self.access_token = access_token
        self.access_token_invalid = False
        self.tokens = MAX_TOKENS
        self.max_tokens = MAX_TOKENS
        self.rate = RATE

        # This handles all of the token related information
        if staff_id:
            self.staff_id = staff_id

    async def __wait_for_token(self):
        self.__add_new_tokens()
        while self.tokens <= 1:
            await sleep(1)
            self.__add_new_tokens()
        self.tokens -= 1

    def __add_new_tokens(self):
        now = monotonic()
        time_since_update = now - self.updated_at
        new_tokens = floor(time_since_update * self.rate)
        if new_tokens > 1:
            self.tokens = min(self.tokens + new_tokens, self.max_tokens)
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
            await self.__wait_for_token()
            kwargs['url'] = f'{self.url}{endpoint}'
            kwargs['headers'] = {'X-Shopify-Access-Token': self.access_token}

            response = await self.client.request(**kwargs)
            if response.status_code == 429:
                # We hit the limit, we are out of tokens
                self.tokens = 0
                continue
            elif 400 <= response.status_code or response.status_code != goodstatus:
                # All errors are handled here
                await self.__handle_error(debug=debug, endpoint=endpoint, response=response)
            else:
                jresp = response.json()
                # Recalculate the rate to be sure we have the right one.
                calllimit = response.headers['X-Shopify-Shop-Api-Call-Limit']
                self.max_tokens = int(calllimit.split('/')[1])
                # In Shopify the bucket is emptied after 20 seconds
                # regardless of the bucket size.
                self.rate = int(self.max_tokens / 20)

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

        url = f'{self.url}/graphql.json'
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
                    f' is larger than the max possible query size (>{GRAPH_MAX})'
                    ' for Shopify.'
                )
            elif THROTTLED_ERROR_CODE in error_code_list:  # This should be the last condition
                query_cost = jsondata['extensions']['cost']['requestedQueryCost']
                available = jsondata['extensions']['cost']['throttleStatus']['currentlyAvailable']
                rate = jsondata['extensions']['cost']['throttleStatus']["restoreRate"]
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


class UniqueStore(Store):
    __instance = None

    def __new__(cls):
        if UniqueStore.__instance is None:
            raise ValueError('The unique store was not initialized')
        return UniqueStore.__instance

    @staticmethod
    def init(store_id, name, access_token):
        UniqueStore.__instance = Store(store_id, name, access_token)
