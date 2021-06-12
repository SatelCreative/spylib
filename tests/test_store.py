from unittest.mock import AsyncMock

import pytest
from pydantic import validator
from pydantic.dataclasses import dataclass

from satel_shopify import Store
from satel_shopify.exceptions import ShopifyCallInvalidError


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
    gql_response = {
        'errors': [
            {
                'message': "Field 'shopp' doesn't exist on type 'QueryRoot'",
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

    with pytest.raises(ValueError):
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
