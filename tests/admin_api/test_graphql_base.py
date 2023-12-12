from unittest.mock import AsyncMock

import pytest

from spylib.exceptions import ShopifyGQLError

from ..token_classes import MockHTTPResponse, OfflineToken, test_information


@pytest.mark.asyncio
async def test_store_graphql_happypath(mocker):
    token = await OfflineToken.load(store_name=test_information.store_name)

    query = """
    {
      shop {
        name
      }
    }"""
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

    jsondata = await token.execute_gql(query=query)

    shopify_request_mock.assert_called_once()

    assert jsondata == data


@pytest.mark.asyncio
async def test_store_graphql_badquery(mocker):
    token = await OfflineToken.load(store_name=test_information.store_name)

    query = """
    {
      shopp {
        name
      }
    }
    """

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
        await token.execute_gql(query=query)

    shopify_request_mock.assert_called_once()


@pytest.mark.asyncio
async def test_store_graphql_tokeninvalid(mocker):
    token = await OfflineToken.load(store_name=test_information.store_name)

    query = """
    {
      shop {
        name
      }
    }"""
    gql_response = {
        'errors': '[API] Invalid API key or access token (unrecognized login or wrong password)'
    }

    shopify_request_mock = mocker.patch(
        'httpx.AsyncClient.request',
        new_callable=AsyncMock,
        return_value=MockHTTPResponse(status_code=200, jsondata=gql_response),
    )

    with pytest.raises(ConnectionRefusedError):
        await token.execute_gql(query=query)

    shopify_request_mock.assert_called_once()


@pytest.mark.asyncio
async def test_store_graphql_non_200(mocker):
    token = await OfflineToken.load(store_name=test_information.store_name)

    query = """
    {
      shop {
        name
      }
    }"""
    data = {'errors': 'An unexpected error occurred'}
    gql_response = {'errors': 'An unexpected error occurred'}

    shopify_request_mock = mocker.patch(
        'httpx.AsyncClient.request',
        new_callable=AsyncMock,
        return_value=MockHTTPResponse(status_code=500, jsondata=gql_response),
    )
    with pytest.raises(Exception):
        jsondata = await token.execute_gql(query=query)
        assert jsondata == data

    shopify_request_mock.assert_called_once()


@pytest.mark.asyncio
async def test_store_graphql_non_503(mocker):
    token = await OfflineToken.load(store_name=test_information.store_name)

    query = """
    {
      shop {
        name
      }
    }"""

    shopify_request_mock = mocker.patch(
        'httpx.AsyncClient.request',
        new_callable=AsyncMock,
        return_value=MockHTTPResponse(status_code=503, jsondata=None),
    )
    with pytest.raises(ShopifyGQLError, match='GQL query failed, status code: 503.'):
        await token.execute_gql(query=query)

    shopify_request_mock.assert_called_once()
