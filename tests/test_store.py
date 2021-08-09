from time import monotonic
from unittest.mock import AsyncMock

import pytest
from pydantic import validator
from pydantic.dataclasses import dataclass

from spylib import Store
from spylib.exceptions import ShopifyCallInvalidError


@dataclass
class MockHTTPResponse:
    status_code: int
    jsondata: dict
    headers: dict = None  # type: ignore

    @validator('headers', pre=True, always=True)
    def set_id(cls, fld):
        return fld or {'X-Shopify-Shop-Api-Call-Limit': '39/40'}

    def json(self):
        return self.jsondata


@pytest.mark.asyncio
async def test_store_rest_happypath(mocker):
    store = Store(store_id='TEST', name='test-store', access_token='Te5tM3')

    shopify_request_mock = mocker.patch(
        'httpx.AsyncClient.request',
        new_callable=AsyncMock,
        return_value=MockHTTPResponse(status_code=200, jsondata={'success': True}),
    )

    jsondata = await store.shoprequest(
        goodstatus=200, debug='Test failed', endpoint='/test.json', method='get'
    )

    shopify_request_mock.assert_called_once()

    assert jsondata == {'success': True}

    # 80 from assuming Shopify plus then 1 used just now.
    assert store.tokens == 79


@pytest.mark.asyncio
async def test_store_rest_badrequest(mocker):
    store = Store(store_id='TEST', name='test-store', access_token='Te5tM3')

    shopify_request_mock = mocker.patch(
        'httpx.AsyncClient.request',
        new_callable=AsyncMock,
        return_value=MockHTTPResponse(
            status_code=422, jsondata={'errors': {'title': ["can't be blank"]}}
        ),
    )

    with pytest.raises(ShopifyCallInvalidError):
        await store.shoprequest(
            goodstatus=201,
            debug='Test failed',
            endpoint='/products.json',
            method='post',
            json={'product': {'body_html': 'A mystery!'}},
        )

    shopify_request_mock.assert_called_once()


params = [
    pytest.param(0, 1000, 79, id='Last call hit rate limit, long time ago'),
    pytest.param(0, 20, 79, id='Last call hit rate limit, 20s ago'),
    pytest.param(0, 10, 39, id='Last call hit rate limit, 10s ago'),
    # Wait 1 second to get 4 then use 1 so 3
    pytest.param(0, 0, 3, id='Last call that hit rate limit just happened'),
]


@pytest.mark.parametrize('init_tokens, time_passed, expected_tokens', params)
@pytest.mark.asyncio
async def test_store_rest_ratetokens(init_tokens, time_passed, expected_tokens, mocker):
    store = Store(store_id='TEST', name='test-store', access_token='Te5tM3')

    # Simulate that there is only 2 calls available before hitting the rate limit.
    # If we set this to zero, then the code will wait 1 sec which is not great to keep the tests
    # fast
    store.tokens = init_tokens
    store.updated_at = monotonic() - time_passed  # A looooong time ago

    shopify_request_mock = mocker.patch(
        'httpx.AsyncClient.request',
        new_callable=AsyncMock,
        return_value=MockHTTPResponse(status_code=200, jsondata={'success': True}),
    )
    await store.shoprequest(
        goodstatus=200, debug='Test failed', endpoint='/test.json', method='get'
    )

    shopify_request_mock.assert_called_once()

    assert store.tokens == expected_tokens


@pytest.mark.asyncio
async def test_store_graphql_happypath(mocker):
    store = Store(store_id='TEST', name='test-store', access_token='Te5tM3')

    query = '''
    {
      shop {
        name
      }
    }'''
    data = {'shop': {'name': 'graphql-admin'}}
    gql_response = {
        'data': data,
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
    }

    shopify_request_mock = mocker.patch(
        'httpx.AsyncClient.request',
        new_callable=AsyncMock,
        return_value=MockHTTPResponse(status_code=200, jsondata=gql_response),
    )

    jsondata = await store.execute_gql(query=query)

    shopify_request_mock.assert_called_once()

    assert jsondata == data


@pytest.mark.asyncio
async def test_store_graphql_badquery(mocker):
    store = Store(store_id='TEST', name='test-store', access_token='Te5tM3')

    query = '''
    {
      shopp {
        name
      }
    }'''
    error_msg = "Field 'shopp' doesn't exist on type 'QueryRoot'"
    gql_response = {
        'errors': [
            {
                'message': error_msg,
                'locations': [{'line': 2, 'column': 3}],
                'path': ['query', 'shopp'],
                'extensions': {
                    'code': 'undefinedField',
                    'typeName': 'QueryRoot',
                    'fieldName': 'shopp',
                },
            }
        ]
    }

    shopify_request_mock = mocker.patch(
        'httpx.AsyncClient.request',
        new_callable=AsyncMock,
        return_value=MockHTTPResponse(status_code=200, jsondata=gql_response),
    )

    with pytest.raises(ValueError, match=f'^GraphQL query is incorrect:\n{error_msg}$'):
        await store.execute_gql(query=query)

    shopify_request_mock.assert_called_once()


@pytest.mark.asyncio
async def test_store_graphql_tokeninvalid(mocker):
    store = Store(store_id='TEST', name='test-store', access_token='INVALID')

    query = '''
    {
      shop {
        name
      }
    }'''
    gql_response = {
        'errors': '[API] Invalid API key or access token (unrecognized login or wrong password)'
    }

    shopify_request_mock = mocker.patch(
        'httpx.AsyncClient.request',
        new_callable=AsyncMock,
        return_value=MockHTTPResponse(status_code=200, jsondata=gql_response),
    )

    with pytest.raises(ConnectionRefusedError):
        await store.execute_gql(query=query)

    shopify_request_mock.assert_called_once()


graphql_operation_name_query = '''
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
    '''

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
    query, operation_name, expected_result, result_location, data, mocker
):
    '''
    Checks to see if passing an operation name works as expected.
    There is 3 possible outcomes when you pass in operation_name:

    1. It succeeds, resolving properly with the name.
    2. It fails because the operation_name you specified doesn't exist.
    3. It fails because you didn't specify an operation_name (null) when \
        one should have been specified (2 named queries)

    This checks just the successful queries.
    '''
    store = Store(store_id='TEST', name='test-store', access_token='Te5tM3')

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
    real_result = await store.execute_gql(query=query, operation_name=operation_name)
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
async def test_store_graphql_operation_name_badquery(query, operation_name, error, mocker):
    '''
    Checks to see if passing an operation name works as expected.
    There is 3 possible outcomes when you pass in operation_name:

    1. It succeeds, resolving properly with the name.
    2. It fails because the operation_name you specified doesn't exist.
    3. It fails because you didn't specify an operation_name (null) when \
        one should have been specified (2 named queries)

    This tests the error cases.

    '''
    store = Store(store_id='TEST', name='test-store', access_token='Te5tM3')

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
        await store.execute_gql(query=query, operation_name=operation_name)

    assert shopify_request_mock.call_count == 1


@pytest.mark.asyncio
async def test_store_graphql_throttling(mocker):
    store = Store(store_id='TEST', name='test-store', access_token='Te5tM3')

    query = '''
    {
      shop {
        name
      }
    }'''
    extensions = {
        "cost": {
            "requestedQueryCost": 752,
            "actualQueryCost": None,
            "throttleStatus": {
                "maximumAvailable": 1000,
                "currentlyAvailable": 662,
                "restoreRate": 50,
            },
        }
    }

    gql_response_throttled = {
        "errors": [
            {
                "message": "Throttled",
                "extensions": {
                    "code": "THROTTLED",
                    "documentation": "https://help.shopify.com/api/graphql-admin-api/"
                    "graphql-admin-api-rate-limits",
                },
            }
        ],
        "extensions": extensions,
    }
    data = {'shop': {'name': 'graphql-admin'}}
    gql_response = {'data': data, 'extensions': extensions}

    shopify_request_mock = mocker.patch(
        'httpx.AsyncClient.request',
        new_callable=AsyncMock,
        side_effect=[
            MockHTTPResponse(status_code=200, jsondata=gql_response_throttled),
            MockHTTPResponse(status_code=200, jsondata=gql_response),
        ],
    )

    assert 'shop' in await store.execute_gql(query=query)
    shopify_request_mock.call_count == 2
