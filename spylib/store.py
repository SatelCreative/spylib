from asyncio import sleep
from math import ceil, floor
from re import search
from time import monotonic
from types import MethodType
from typing import Any, Callable, Dict, List, Optional

from httpx import AsyncClient, Response
from loguru import logger
from tenacity import retry
from tenacity.retry import retry_if_exception, retry_if_exception_type
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_random

from .constants import (
    MAX_COST_EXCEEDED_ERROR_CODE,
    OPERATION_NAME_REQUIRED_ERROR_MESSAGE,
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
from .token import AssociatedUser, OfflineToken, OnlineToken


class Store:
    """
    This is an instance of a store, this contains the core logic for
    manipulating the shopifyAPI.
    """

    def __init__(
        self,
        store_name: str,
        scopes: List[str] = [],
        api_version: str = '2021-04',
        max_rest_bucket: int = 80,
        rest_refill_rate: int = 4,
        max_graphql_bucket: int = 1000,
        graphql_refill_rate: int = 50,
        save_token: Optional[Callable] = None,
        load_token: Optional[Callable] = None,
    ) -> None:
        """
        Creates a new instance of a store. Takes in:

        - `store_name` - The name of the store specified by shopify.
        - `scopes` - The scopes required by the app for this store.
        - `api_version` - The version of the shopify API that the store is using
        - `max_rest_bucket` - This is the max number of rest tokens allowed by the store.
        - `rest_refill_rate` - The rate at which the tokens refill (per second)
        - `max_graphql_bucket` - This is the max size of the graphql bucket
        - `graphql_refill_rate` - This is how much the graphql bucket refills per second
        - `save_token` - Function that saves the tokens for this store, must start
            with self as a parameter.
        - `load_token` - Function that loads the tokens for this store, must start
            with self as a parameter.
        """

        self.online_access_tokens: Dict[int, OnlineToken] = {}
        self.offline_access_token: Optional[OfflineToken] = None
        self.load_token = None
        self.save_token = None

        self.store_name = store_name
        self.api_version = api_version
        self.scopes = scopes

        if load_token:
            self.load_token = MethodType(load_token, self)
        if save_token:
            self.save_token = MethodType(save_token, self)

        # API tokens represent the amount of calls you can make
        self.rest_bucket: int = max_rest_bucket
        self.max_rest_bucket: int = max_rest_bucket
        self.rest_refill_rate: int = rest_refill_rate

        # Unused right now, but defines the graphql bucket
        self.graphql_bucket = max_graphql_bucket
        self.max_graphql_bucket = max_graphql_bucket
        self.graphql_refill_rate = graphql_refill_rate

        self.api_url = f'https://{store_name}.myshopify.com/admin/api/{api_version}'
        self.client: AsyncClient = AsyncClient()
        self.updated_at: float = monotonic()

    async def add_offline_token(self, token: str):
        """
        Adds an offline token to the store. There can only be `1` offline token.
        """
        self.offline_access_token = OfflineToken(
            self.store_name,
            self.scopes,
            token,
            self.save_token,
            self.load_token,
        )

    async def add_online_token(self, token: str, associated_user: AssociatedUser, expires_in: int):
        """
        Adds an online token to the store. There can be `n` online tokens. A token
        can be retrieved based on an associated user as there should only be one
        token per user that is valid.
        """
        self.online_access_tokens[associated_user.id] = OnlineToken(
            store_name=self.store_name,
            scope=self.scopes,
            associated_user=associated_user,
            expires_in=expires_in,
            access_token=token,
            save_token=self.save_token,
            load_token=self.load_token,
        )

    async def __wait_for_token(self):
        self.__add_new_tokens()
        while self.rest_bucket <= 1:
            await sleep(1)
            self.__add_new_tokens()
        self.rest_bucket -= 1

    def __add_new_tokens(self):
        now = monotonic()
        time_since_update = now - self.updated_at
        new_tokens = floor(time_since_update * self.rest_refill_rate)
        if new_tokens > 1:
            self.rest_bucket = min(self.rest_bucket + new_tokens, self.max_rest_bucket)
            self.updated_at = now

    async def __handle_error(self, debug: str, endpoint: str, response: Response):
        """Handle any error that occurred when calling Shopify

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

    @classmethod
    def store_domain(cls, shop: str) -> str:
        """Very flexible conversion of a shop's subdomain or complete or incomplete url into a
        complete url"""
        result = search(r'^(https:\/\/)?([a-z1-9\-]+)(\.myshopify\.com[\/]?)?$', shop.lower())
        if not result:
            raise ValueError(f'{shop} is not a shopify shop')

        domain = result.group(3) or '.myshopify.com'
        storename = result.group(2)

        return f'{storename}{domain}'

    @classmethod
    def domain_to_storename(cls, domain: str) -> str:
        result = search(r'(https:\/\/)?([^.]+)\.myshopify\.com[\/]?', domain)
        if result:
            return result.group(2)

        raise ValueError(f'{domain} is not a shopify domain')

    async def execute_rest_online(self, goodstatus, debug, endpoint, user_id, **kwargs):
        """
        Makes a request to the REST endpoint using an online token for the store.
        """
        return await self.__execute_rest(
            goodstatus, debug, endpoint, self.online_access_tokens[user_id], **kwargs
        )

    async def execute_rest_offline(self, goodstatus, debug, endpoint, **kwargs):
        """
        Makes a request to the REST endpoint using the offline token for the store.
        """
        return await self.__execute_rest(
            goodstatus, debug, endpoint, self.offline_access_token, **kwargs
        )

    @retry(
        reraise=True,
        wait=wait_random(min=1, max=2),
        stop=stop_after_attempt(5),
        retry=retry_if_exception(not_our_fault),
    )
    async def __execute_rest(
        self, goodstatus, debug, endpoint, access_token, **kwargs
    ) -> Dict[str, Any]:
        if not access_token:
            raise NameError(
                (
                    "Access token has not been defined. Are you sure the"
                    "token is valid for this store?"
                )
            )
        while True:
            await self.__wait_for_token()
            kwargs['url'] = f'{self.api_url}{endpoint}'
            kwargs['headers'] = {'X-Shopify-Access-Token': access_token}

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
                self.max_rest_bucket = int(calllimit.split('/')[1])
                # In Shopify the bucket is emptied after 20 seconds
                # regardless of the bucket size.
                self.rest_refill_rate = int(self.max_rest_bucket / 20)

            return jresp

    async def execute_gql_online(
        self,
        user_id: int,
        query: str,
        variables: Dict[str, Any] = {},
        operation_name: Optional[str] = None,
        **kwargs,
    ):
        """
        Makes a request to the GQL endpoint using an online token for the store.
        """
        return await self.__execute_gql(
            self.online_access_tokens[user_id].access_token,
            query,
            variables,
            operation_name,
        )

    async def execute_gql_offline(
        self,
        query: str,
        variables: Dict[str, Any] = {},
        operation_name: Optional[str] = None,
    ):
        """
        Makes a request to the GQL endpoint using the offline token for the store.
        """
        if not self.offline_access_token:
            raise NameError(
                (
                    "Access token has not been defined. Are you sure the"
                    "token is valid for this store?"
                )
            )
        return await self.__execute_gql(
            self.offline_access_token.access_token,
            query,
            variables,
            operation_name,
        )

    @retry(
        reraise=True,
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(ShopifyThrottledError),
    )
    async def __execute_gql(
        self,
        access_token: Optional[str],
        query: str,
        variables: Dict[str, Any] = {},
        operation_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Simple graphql query executor because python has no decent graphql client"""

        if not access_token:
            raise NameError(
                (
                    "Access token has not been defined. Are you sure the"
                    "token is valid for this store?"
                )
            )

        url = f'{self.api_url}/graphql.json'
        headers = {
            'Content-type': 'application/json',
            'X-Shopify-Access-Token': access_token,
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
                    f' is larger than the max possible query size (>{self.max_graphql_bucket})'
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
