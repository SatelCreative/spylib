import pytest

from ..token_classes import (
    OfflineToken,
    OnlineToken,
    PrivateToken,
    VersionOfflineToken,
    offline_token_data,
    online_token_data,
    test_information,
)


@pytest.mark.asyncio
async def test_online_token():
    # Create a new token
    online_token = await OnlineToken.load(
        store_name=test_information.store_name,
        user_id=str(online_token_data.associated_user.id),
    )

    assert online_token.access_token == online_token_data.access_token
    assert not online_token.access_token_invalid
    assert online_token.scope == online_token_data.scope
    assert online_token.associated_user_id == online_token_data.associated_user.id
    assert online_token.api_url == f'https://{test_information.store_name}.myshopify.com/admin'
    assert (
        online_token.oauth_url
        == f'https://{test_information.store_name}.myshopify.com/admin/oauth/access_token'
    )


@pytest.mark.asyncio
async def test_offline_token():
    # Create a new token
    offline_token = await OfflineToken.load(store_name=test_information.store_name)

    assert offline_token.access_token == offline_token_data.access_token
    assert offline_token.scope == offline_token_data.scope
    assert offline_token.store_name == test_information.store_name
    assert not offline_token.access_token_invalid
    assert offline_token.api_url == f'https://{test_information.store_name}.myshopify.com/admin'
    assert (
        offline_token.oauth_url
        == f'https://{test_information.store_name}.myshopify.com/admin/oauth/access_token'
    )


@pytest.mark.asyncio
async def test_private_token():
    # Create a new token
    private_token = await PrivateToken.load(store_name=test_information.store_name)

    assert private_token.access_token == offline_token_data.access_token
    assert private_token.scope == offline_token_data.scope
    assert private_token.store_name == test_information.store_name
    assert not private_token.access_token_invalid
    assert private_token.api_url == f'https://{test_information.store_name}.myshopify.com/admin'
    assert (
        private_token.oauth_url
        == f'https://{test_information.store_name}.myshopify.com/admin/oauth/access_token'
    )


@pytest.mark.asyncio
async def test_version_offline_token():
    offline_token = await VersionOfflineToken.load(store_name=test_information.store_name)
    assert offline_token.api_version == test_information.api_version
    assert (
        offline_token.api_url
        == f'https://{test_information.store_name}'
        + f'.myshopify.com/admin/api/{test_information.api_version}'
    )
