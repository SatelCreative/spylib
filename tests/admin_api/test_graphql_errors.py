from unittest.mock import AsyncMock

from pytest import mark, param, raises

from spylib.constants import API_CALL_NUMBER_RETRY_ATTEMPTS
from spylib.exceptions import ShopifyGQLError, ShopifyInvalidResponseBody

from ..token_classes import MockHTTPResponse, OfflineToken, test_information

NO_RETRY_ATTEMPTS = 1


scenarios = [
    param(
        dict(status_code=200, jsondata={'data': {}, 'errors': [{'message': 'any error'}]}),
        NO_RETRY_ATTEMPTS,
        ShopifyGQLError,
        id='Any error message from GraphQL',
    ),
    param(
        dict(status_code=200, jsondata=None),
        API_CALL_NUMBER_RETRY_ATTEMPTS,
        ShopifyInvalidResponseBody,
        id='Weird Shopify intermittent error returning HTML instead of a JSON in the response body',
    ),
]


@mark.asyncio
@mark.parametrize('gql_response, number_attempts, expected_exception', scenarios)
async def test_store_graphql_surface_errors(gql_response, number_attempts, expected_exception, mocker):
    token = await OfflineToken.load(store_name=test_information.store_name)

    query = """
    {
      something {
        name
      }
    }"""

    shopify_request_mock = mocker.patch(
        'httpx.AsyncClient.request',
        new_callable=AsyncMock,
        return_value=MockHTTPResponse(**gql_response),
    )
    with raises(expected_exception):
        await token.execute_gql(query=query, suppress_errors=False)

    assert shopify_request_mock.call_count == number_attempts
