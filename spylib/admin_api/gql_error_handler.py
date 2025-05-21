import logging
from asyncio import sleep
from json.decoder import JSONDecodeError
from math import ceil
from typing import NoReturn, Optional, Union

from spylib.constants import (
    MAX_COST_EXCEEDED_ERROR_CODE,
    OPERATION_NAME_REQUIRED_ERROR_MESSAGE,
    THROTTLED_ERROR_CODE,
    WRONG_OPERATION_NAME_ERROR_MESSAGE,
)
from spylib.exceptions import (
    ShopifyCallInvalidError,
    ShopifyExceedingMaxCostError,
    ShopifyGQLError,
    ShopifyIntermittentError,
    ShopifyInvalidResponseBody,
    ShopifyThrottledError,
)


class GQLErrorHandler:
    """Handle the bad status codes and errors codes
    https://shopify.dev/api/admin-graphql#status_and_error_codes
    """

    def __init__(
        self,
        store_name: str,
        graphql_bucket_max: int,
        suppress_errors: bool,
        operation_name: Optional[str],
    ):
        self.store_name = store_name
        self.graphql_bucket_max = graphql_bucket_max
        self.suppress_errors = suppress_errors
        self.operation_name = operation_name

    async def check(self, response) -> dict:
        if response.status_code != 200:
            self._handle_non_200_status_codes(response=response)

        jsondata = self._extract_jsondata_from(response=response)

        errors: Union[list, str] = jsondata.get('errors', [])
        if errors:
            await self._check_errors_field(errors=errors, jsondata=jsondata)

        return jsondata

    def _handle_non_200_status_codes(self, response) -> NoReturn:
        if response.status_code >= 500:
            raise ShopifyIntermittentError(
                f'The Shopify API returned an intermittent error: {response.status_code}.'
            )

        try:
            jsondata = response.json()
            error_msg = f'{response.status_code}. {jsondata["errors"]}'
        except JSONDecodeError:
            error_msg = f'{response.status_code}.'

        raise ShopifyGQLError(f'GQL query failed, status code: {error_msg}')

    @staticmethod
    def _extract_jsondata_from(response) -> dict:
        try:
            jsondata = response.json()
        except JSONDecodeError as exc:
            raise ShopifyInvalidResponseBody from exc

        if not isinstance(jsondata, dict):
            raise ValueError('JSON data is not a dictionary')

        return jsondata

    async def _check_errors_field(self, errors: Union[list, str], jsondata: dict):
        has_data_field = 'data' in jsondata
        if has_data_field and not self.suppress_errors:
            raise ShopifyGQLError(jsondata)

        if isinstance(errors, str):
            self._handle_invalid_access_token(errors)
            raise ShopifyGQLError(f'Unknown errors string: {jsondata}')

        await self._handle_errors_list(jsondata=jsondata, errors=errors)

        errorlist = '\n'.join([err['message'] for err in jsondata['errors'] if 'message' in err])
        raise ValueError(f'GraphQL query is incorrect:\n{errorlist}')

    async def _handle_errors_list(self, jsondata: dict, errors: list) -> None:
        # Only report on the first error just to simplify: We will raise an exception anyway.
        err = errors[0]

        if 'extensions' in err and 'code' in err['extensions']:
            error_code = err['extensions']['code']
            self._handle_max_cost_exceeded_error_code(error_code=error_code)
            await self._handle_throttled_error_code(error_code=error_code, jsondata=jsondata)

        if 'message' in err:
            self._handle_operation_name_required_error(error_message=err['message'])
            self._handle_wrong_operation_name_error(error_message=err['message'])

    def _handle_invalid_access_token(self, errors: str) -> None:
        if 'Invalid API key or access token' in errors:
            self.access_token_invalid = True
            logging.warning(
                f'Store {self.store_name}: The Shopify API token is invalid. '
                'Flag the access token as invalid.'
            )
            raise ConnectionRefusedError

    def _handle_max_cost_exceeded_error_code(self, error_code: str) -> None:
        if error_code != MAX_COST_EXCEEDED_ERROR_CODE:
            return

        raise ShopifyExceedingMaxCostError(
            f'Store {self.store_name}: This query was rejected by the Shopify'
            f' API, and will never run as written, as the query cost'
            f' is larger than the max possible query size (>{self.graphql_bucket_max})'
            ' for Shopify.'
        )

    async def _handle_throttled_error_code(self, error_code: str, jsondata: dict) -> None:
        if error_code != THROTTLED_ERROR_CODE:
            return

        cost = jsondata['extensions']['cost']
        query_cost = cost['requestedQueryCost']
        available = cost['throttleStatus']['currentlyAvailable']
        rate = cost['throttleStatus']['restoreRate']
        sleep_time = ceil((query_cost - available) / rate)
        await sleep(sleep_time)
        raise ShopifyThrottledError

    def _handle_operation_name_required_error(self, error_message: str) -> None:
        if error_message != OPERATION_NAME_REQUIRED_ERROR_MESSAGE:
            return

        raise ShopifyCallInvalidError(
            f'Store {self.store_name}: Operation name was required for this query.'
            'This likely means you have multiple queries within one call '
            'and you must specify which to run.'
        )

    def _handle_wrong_operation_name_error(self, error_message: str) -> None:
        if error_message != WRONG_OPERATION_NAME_ERROR_MESSAGE.format(self.operation_name):
            return

        raise ShopifyCallInvalidError(
            f'Store {self.store_name}: Operation name {self.operation_name}'
            'does not exist in the query.'
        )
