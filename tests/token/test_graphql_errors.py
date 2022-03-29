from unittest.mock import AsyncMock

import pytest

from spylib.exceptions import ShopifyGQLError

from ..token_classes import MockHTTPResponse, OfflineToken, test_information


@pytest.mark.asyncio
async def test_store_graphql_happypath(mocker):
    token = await OfflineToken.load(store_name=test_information.store_name)

    query = """
    {
      something {
        name
      }
    }"""

    gql_response = {
        'data': {},
        'errors': []
    }

    shopify_request_mock = mocker.patch(
        'httpx.AsyncClient.request',
        new_callable=AsyncMock,
        return_value=MockHTTPResponse(status_code=200, jsondata=gql_response),
    )
    with pytest.raises(ShopifyGQLError):
        await token.execute_gql(query=query, suppress_errors=False)

    assert shopify_request_mock.call_count == 1
