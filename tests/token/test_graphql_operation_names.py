from typing import Any
from unittest.mock import AsyncMock

import pytest

from spylib.exceptions import ShopifyCallInvalidError

from ..token_classes import MockHTTPResponse, OfflineToken, test_information

graphql_operation_name_query = """
    query query1 {
        shop {
            name
        }
    }

    query query2 {
        shop {
            domains {
                id
            }
        }
    }
    """

params = [
    pytest.param(
        graphql_operation_name_query,
        'query1',
        'shop1',
        ['shop', 'name'],
        {'shop': {'name': 'shop1'}},
        id='Testing Basic Query - Query 1',
    ),
    pytest.param(
        graphql_operation_name_query,
        'query2',
        'gid://shopify/Domain/33896136726',
        ['shop', 'domains', 0, 'id'],
        {'shop': {'domains': [{'id': 'gid://shopify/Domain/33896136726'}]}},
        id='Testing Basic Query - Query 2',
    ),
]


@pytest.mark.parametrize('query, operation_name, expected_result, result_location, data', params)
@pytest.mark.asyncio
async def test_store_graphql_operation_name_happypath(
    query,
    operation_name,
    expected_result,
    result_location,
    data,
    mocker,
):
    """
    Checks to see if passing an operation name works as expected.
    There is 3 possible outcomes when you pass in operation_name:

    1. It succeeds, resolving properly with the name.
    2. It fails because the operation_name you specified doesn't exist.
    3. It fails because you didn't specify an operation_name (null) when \
        one should have been specified (2 named queries)

    This checks just the successful queries.
    """
    token = await OfflineToken.load(store_name=test_information.store_name)

    gql_response = {
        'extensions': {
            'cost': {
                'requestedQueryCost': 1,
                'actualQueryCost': 1,
                'throttleStatus': {
                    'maximumAvailable': 1000,
                    'currentlyAvailable': 999,
                    'restoreRate': 50,
                },
            }
        },
        'data': data,
    }

    shopify_request_mock = mocker.patch(
        'httpx.AsyncClient.request',
        new_callable=AsyncMock,
        return_value=MockHTTPResponse(status_code=200, jsondata=gql_response),
    )

    # Checks to see if it is properly handling inputs properly
    real_result: Any = await token.execute_gql(query=query, operation_name=operation_name)
    for name in result_location:
        if isinstance(real_result, list):
            real_result = real_result[name]
        elif isinstance(real_result, dict):
            real_result = real_result.get(name)

    assert expected_result == real_result

    assert shopify_request_mock.call_count == 1


params = [
    pytest.param(
        graphql_operation_name_query,
        None,
        [{'message': 'An operation name is required'}],
        id='Testing Failed Query - Operation name = none when required',
    ),
    pytest.param(
        graphql_operation_name_query,
        'foobar',
        [{'message': 'No operation named "foobar"'}],
        id='Testing Failed Query - Operation name does not exist in query',
    ),
]


@pytest.mark.parametrize('query, operation_name, error', params)
@pytest.mark.asyncio
async def test_store_graphql_operation_name_badquery(
    query,
    operation_name,
    error,
    mocker,
):
    """
    Checks to see if passing an operation name works as expected.
    There is 3 possible outcomes when you pass in operation_name:

    1. It succeeds, resolving properly with the name.
    2. It fails because the operation_name you specified doesn't exist.
    3. It fails because you didn't specify an operation_name (null) when \
        one should have been specified (2 named queries)

    This tests the error cases.

    """
    token = await OfflineToken.load(store_name=test_information.store_name)

    gql_response = {
        'extensions': {
            'cost': {
                'requestedQueryCost': 1,
                'actualQueryCost': 1,
                'throttleStatus': {
                    'maximumAvailable': 1000,
                    'currentlyAvailable': 999,
                    'restoreRate': 50,
                },
            }
        },
        'errors': error,
    }

    shopify_request_mock = mocker.patch(
        'httpx.AsyncClient.request',
        new_callable=AsyncMock,
        return_value=MockHTTPResponse(status_code=200, jsondata=gql_response),
    )
    # Checks to see if it fails properly
    with pytest.raises(ShopifyCallInvalidError):
        await token.execute_gql(query=query, operation_name=operation_name)

    assert shopify_request_mock.call_count == 1
