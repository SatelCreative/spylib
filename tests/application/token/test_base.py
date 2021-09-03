from unittest.mock import AsyncMock

import pytest

from spylib.store import Store
from spylib.token import (
    AssociatedUser,
    OfflineToken,
    OfflineTokenResponse,
    OnlineToken,
    OnlineTokenResponse,
)

from ..shared import MockHTTPResponse


@pytest.mark.asyncio
async def test_online_token():
    """
    This checks to see if the Store object has been initialized with the proper
    information for the online token.
    """

    user = AssociatedUser(
        **{
            "id": 902541635,
            "first_name": "John",
            "last_name": "Smith",
            "email": "john@example.com",
            "email_verified": True,
            "account_owner": True,
            "locale": "en",
            "collaborator": False,
        }
    )

    store_name = 'test-store'
    access_token = '123'
    scope = ['permission', 'permission2']
    user_scope = ['permission3']
    expires_in = 10000
    url = f'https://{store_name}.myshopify.com/admin/oauth/access_token'

    # We first save the token
    token = OnlineToken(
        store_name=store_name,
        access_token=access_token,
        scope=scope,
        associated_user_scope=user_scope,
        associated_user=user,
        expires_in=expires_in,
    )

    assert token.url == url
    assert token.store_name == store_name
    assert token.access_token == access_token
    assert token.scope == scope
    assert token.associated_user_scope == user_scope
    assert token.associated_user == user


@pytest.mark.asyncio
async def test_offline_token():
    """
    This check to be sure that the offline token builds the information properly
    when generated directly.
    """

    store_name = 'test-store'
    access_token = '123'
    scope = ['permission', 'permission2']

    # We first save the token
    token = OfflineToken(
        store_name=store_name,
        access_token=access_token,
        scope=scope,
    )

    assert token.store_name == store_name
    assert token.access_token == access_token
    assert token.scope == scope


@pytest.mark.asyncio
async def test_add_online_token():
    """
    This check to be sure that the online token builds the information properly
    when generated directly.
    """

    user = AssociatedUser(
        **{
            "id": 902541635,
            "first_name": "John",
            "last_name": "Smith",
            "email": "john@example.com",
            "email_verified": True,
            "account_owner": True,
            "locale": "en",
            "collaborator": False,
        }
    )

    # We first save the token
    store = Store(store_name='test-store')
    await store.add_online_token(token='123', associated_user=user, expires_in=10000)

    assert store.store_name == 'test-store'
    assert user.id in store.online_access_tokens
    assert store.online_access_tokens[user.id].access_token == "123"
    assert store.online_access_tokens[user.id].associated_user == user


@pytest.mark.asyncio
async def test_add_offline_token():
    """
    This checks to see if the Store object has been initialized with the proper
    information for an offline token.
    """
    # We first save the token
    store = Store(store_name='test-store')
    await store.add_offline_token(token='123')

    assert store.store_name == 'test-store'
    assert store.offline_access_token.access_token == "123"


@pytest.mark.asyncio
async def test_new_online_token(mocker):
    """
    This check to be sure that we can request a new online token from the URL
    using the .new() syntax.
    """

    client_id = 1
    client_secret = 1
    code = "random_code"
    store_name = 'test-store'

    onlineTokenData = OnlineTokenResponse(
        access_token='ONLINETOKEN',
        scope=','.join(['permission', 'permission2']),
        expires_in=86399,
        associated_user_scope=','.join(['permission', 'permission2']),
        associated_user={
            "id": 902541635,
            "first_name": "John",
            "last_name": "Smith",
            "email": "john@example.com",
            "email_verified": True,
            "account_owner": True,
            "locale": "en",
            "collaborator": False,
        },
    )

    # This sets up a fake endpoint for the online and offline tokens
    shopify_request_mock = mocker.patch('httpx.AsyncClient.request', new_callable=AsyncMock)
    shopify_request_mock.side_effect = [
        MockHTTPResponse(status_code=200, jsondata=onlineTokenData),
    ]

    url = f'https://{store_name}.myshopify.com/admin/oauth/access_token'

    # We first save the token
    token = await OnlineToken.new(
        store_name=store_name,
        client_id=client_id,
        client_secret=client_secret,
        code=code,
    )

    assert token.url == url
    assert token.store_name == store_name
    assert token.access_token == onlineTokenData.access_token
    assert token.scope == onlineTokenData.scope.split(",")
    assert token.associated_user_scope == onlineTokenData.associated_user_scope.split(",")
    assert token.associated_user == onlineTokenData.associated_user


@pytest.mark.asyncio
async def test_new_offline_token(mocker):
    """
    This check to be sure that we can request a new offline token from the URL
    using the .new() syntax.
    """

    client_id = 1
    client_secret = 1
    code = "random_code"
    store_name = 'test-store'
    url = f'https://{store_name}.myshopify.com/admin/oauth/access_token'

    offlineTokenData = OfflineTokenResponse(
        access_token='OFFLINETOKEN',
        scope=','.join(['permission', 'permission2']),
    )

    # This sets up a fake endpoint for the online and offline tokens
    shopify_request_mock = mocker.patch('httpx.AsyncClient.request', new_callable=AsyncMock)
    shopify_request_mock.side_effect = [
        MockHTTPResponse(status_code=200, jsondata=offlineTokenData),
    ]

    # We first save the token
    token = await OfflineToken.new(
        store_name=store_name,
        client_id=client_id,
        client_secret=client_secret,
        code=code,
    )

    assert token.url == url
    assert token.store_name == store_name
    assert token.access_token == offlineTokenData.access_token
    assert token.scope == offlineTokenData.scope.split(",")
