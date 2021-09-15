import pytest

from spylib import Token
from spylib.token import OfflineTokenResponse, OnlineTokenResponse
from tests.token.conftest import AppInformation


@pytest.mark.asyncio
async def test_token(
    offline_token_data: OfflineTokenResponse,
    app_information: AppInformation,
):
    # Create a new token
    token = Token(
        store_name=app_information.store_name,
        access_token=offline_token_data.access_token,
        scope=offline_token_data.scope.split(','),
    )

    assert token.access_token == offline_token_data.access_token
    assert not token.access_token_invalid
    assert token.scope == offline_token_data.scope.split(',')
    assert token.api_url == (
        f'https://{app_information.store_name}.myshopify.com/admin/'
        + f'api/{app_information.api_version}'
    )
    assert (
        token.oauth_url
        == f'https://{app_information.store_name}.myshopify.com/admin/oauth/access_token'
    )


@pytest.mark.asyncio
async def test_online_token(
    OnlineToken,
    online_token_data: OnlineTokenResponse,
    app_information: AppInformation,
):
    # Create a new token
    online_token = OnlineToken(
        store_name=app_information.store_name,
        access_token=online_token_data.access_token,
        scope=online_token_data.scope.split(','),
        expires_in=online_token_data.expires_in,
        associated_user_scope=online_token_data.associated_user_scope.split(','),
        associated_user=online_token_data.associated_user,
    )

    assert online_token.access_token == online_token_data.access_token
    assert not online_token.access_token_invalid
    assert online_token.scope == online_token_data.scope.split(',')
    assert online_token.associated_user == online_token_data.associated_user
    assert online_token.associated_user_scope == online_token_data.associated_user_scope.split(',')
    assert online_token.api_url == (
        f'https://{app_information.store_name}.myshopify.com/admin/'
        + f'api/{app_information.api_version}'
    )
    assert (
        online_token.oauth_url
        == f'https://{app_information.store_name}.myshopify.com/admin/oauth/access_token'
    )


@pytest.mark.asyncio
async def test_save_token(
    OnlineToken,
    online_token_data: OnlineTokenResponse,
    app_information: AppInformation,
    database,
):

    # Create a new token
    online_token = OnlineToken(
        store_name=app_information.store_name,
        access_token=online_token_data.access_token,
        scope=online_token_data.scope.split(','),
        expires_in=online_token_data.expires_in,
        associated_user_scope=online_token_data.associated_user_scope.split(','),
        associated_user=online_token_data.associated_user,
    )

    await online_token.save_token()

    new_online_token = database['online'][online_token.store_name][online_token.associated_user.id]

    # Check to see if the saved token is the same as the original
    assert new_online_token == online_token


@pytest.mark.asyncio
async def test_load_token(
    OnlineToken,
    online_token_data: OnlineTokenResponse,
    app_information: AppInformation,
    database,
):

    # Create a new token
    online_token = OnlineToken(
        store_name=app_information.store_name,
        access_token=online_token_data.access_token,
        scope=online_token_data.scope.split(','),
        expires_in=online_token_data.expires_in,
        associated_user_scope=online_token_data.associated_user_scope.split(','),
        associated_user=online_token_data.associated_user,
    )

    database['online'][app_information.store_name] = {}
    database['online'][app_information.store_name][online_token.associated_user.id] = online_token

    new_online_token = await online_token.load_token(
        app_information.store_name, online_token_data.associated_user.id
    )

    # Check to see if the saved token is the same as the original
    assert new_online_token == online_token


@pytest.mark.asyncio
async def test_offline_token(
    OfflineToken,
    offline_token_data: OfflineTokenResponse,
    app_information: AppInformation,
):
    # Create a new token
    offline_token = OfflineToken(
        store_name=app_information.store_name,
        access_token=offline_token_data.access_token,
        scope=offline_token_data.scope.split(','),
    )

    assert offline_token.access_token == offline_token_data.access_token
    assert offline_token.scope == offline_token_data.scope.split(',')
    assert offline_token.store_name == app_information.store_name
    assert not offline_token.access_token_invalid
    assert offline_token.api_url == (
        f'https://{app_information.store_name}.myshopify.com/admin/'
        + f'api/{app_information.api_version}'
    )
    assert (
        offline_token.oauth_url
        == f'https://{app_information.store_name}.myshopify.com/admin/oauth/access_token'
    )


@pytest.mark.asyncio
async def test_save_offline_token(
    OfflineToken,
    offline_token_data: OfflineTokenResponse,
    app_information: AppInformation,
    database,
):
    # Create a new token
    offline_token = OfflineToken(
        store_name=app_information.store_name,
        access_token=offline_token_data.access_token,
        scope=offline_token_data.scope.split(','),
    )

    await offline_token.save_token()

    new_offline_token = database['offline'][offline_token.store_name]

    # Check to see if the saved token is the same as the original
    assert new_offline_token == offline_token


@pytest.mark.asyncio
async def test_load_offline_token(
    OfflineToken,
    offline_token_data: OfflineTokenResponse,
    app_information: AppInformation,
    database,
):
    # Create a new token
    offline_token = OfflineToken(
        store_name=app_information.store_name,
        access_token=offline_token_data.access_token,
        scope=offline_token_data.scope.split(','),
    )

    database['offline'][app_information.store_name] = offline_token

    new_offline_token = await offline_token.load_token(app_information.store_name)

    # Check to see if the loaded token is the same as the original
    assert new_offline_token == offline_token
