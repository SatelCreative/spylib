from unittest.mock import AsyncMock
import pytest
from ..shared import (
    MockHTTPResponse,
    OfflineToken,
    store_name,
    api_version,
    client_id,
    client_secret,
    code,
    database,
    offline_token_data,
)


@pytest.mark.asyncio
async def test_token(mocker):
    # Create a new token
    offline_token = OfflineToken(
        store_name=store_name,
        access_token=offline_token_data.access_token,
        scope=offline_token_data.scope.split(','),
    )

    assert offline_token.access_token == offline_token_data.access_token
    assert offline_token.scope == offline_token_data.scope.split(',')
    assert offline_token.store_name == store_name
    assert not offline_token.access_token_invalid
    assert offline_token.api_url == f'https://{store_name}.myshopify.com/admin/api/{api_version}'
    assert (
        offline_token.oauth_url == f'https://{store_name}.myshopify.com/admin/oauth/access_token'
    )


@pytest.mark.asyncio
async def test_new_token(mocker):
    """
    This tests the ability to generate a new token from the endpoint using the
    client_id, client_secret, and code.
    """
    # Generating the object callback with the token information
    shopify_request_mock = mocker.patch('httpx.AsyncClient.request', new_callable=AsyncMock)
    shopify_request_mock.side_effect = [
        MockHTTPResponse(status_code=200, jsondata=offline_token_data),
    ]

    # Create a new token
    offline_token = await OfflineToken.new(
        store_name,
        client_id,
        client_secret,
        code,
    )

    assert offline_token.access_token == offline_token_data.access_token
    assert offline_token.scope == offline_token_data.scope.split(',')
    assert offline_token.store_name == store_name
    assert not offline_token.access_token_invalid
    assert offline_token.api_url == f'https://{store_name}.myshopify.com/admin/api/{api_version}'
    assert (
        offline_token.oauth_url == f'https://{store_name}.myshopify.com/admin/oauth/access_token'
    )


@pytest.mark.asyncio
async def test_save_token(mocker):
    # Create a new token
    offline_token = OfflineToken(
        store_name=store_name,
        access_token=offline_token_data.access_token,
        scope=offline_token_data.scope.split(','),
    )

    await offline_token.save_token()

    new_offline_token = database['offline'][offline_token.store_name]

    # Check to see if the saved token is the same as the original
    assert new_offline_token == offline_token


@pytest.mark.asyncio
async def test_load_token(mocker):
    # Create a new token
    offline_token = OfflineToken(
        store_name=store_name,
        access_token=offline_token_data.access_token,
        scope=offline_token_data.scope.split(','),
    )

    database['offline'][store_name] = offline_token

    new_offline_token = await offline_token.load_token(store_name)

    # Check to see if the loaded token is the same as the original
    assert new_offline_token == offline_token
