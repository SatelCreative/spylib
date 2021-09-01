from typing import Tuple
from spylib.store import Store
from spylib.application import ShopifyApplication
from unittest.mock import AsyncMock
from urllib.parse import ParseResult, parse_qs, urlencode, urlparse

import pytest
from pydantic.dataclasses import dataclass
from requests import Response

from spylib.token import OfflineToken, OfflineTokenResponse, OnlineTokenResponse
from spylib.utils import hmac, now_epoch

from .shared import initialize_store


@dataclass
class MockHTTPResponse:
    status_code: int
    jsondata: dict
    headers: dict = None  # type: ignore

    def json(self):
        return self.jsondata


def check_oauth_redirect_url(
    shop_name: str,
    response: Response,
    client,
    path: str,
) -> str:
    assert response.text == ''
    assert response.status_code == 307

    redirect_target = urlparse(client.get_redirect_target(response))

    expected_parsed_url = ParseResult(
        scheme='https',
        netloc=shop_name,
        path=path,
        query=redirect_target.query,  # We check that separately
        params='',
        fragment='',
    )
    assert redirect_target == expected_parsed_url

    return redirect_target.query


def check_oauth_redirect_query(
    shopify_app: ShopifyApplication,
    query: str,
    query_extra: dict = {},
) -> str:
    parsed_query = parse_qs(query)
    state = parsed_query.pop('state', [''])[0]

    expected_query = dict(
        client_id=[shopify_app.client_id],
        redirect_uri=[f'https://{shopify_app.app_domain}/callback'],
        scope=[",".join(shopify_app.app_scopes)],
    )
    expected_query.update(query_extra)

    assert parsed_query == expected_query

    return state


def generate_token_data(
    shopify_app: ShopifyApplication,
) -> Tuple[OfflineTokenResponse, OnlineTokenResponse]:

    offlineTokenData = OfflineTokenResponse(
        access_token='OFFLINETOKEN',
        scope=','.join(shopify_app.app_scopes),
    )

    onlineTokenData = OnlineTokenResponse(
        access_token='ONLINETOKEN',
        scope=','.join(shopify_app.app_scopes),
        expires_in=86399,
        associated_user_scope=','.join(shopify_app.app_scopes),
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

    return offlineTokenData, onlineTokenData


@pytest.mark.asyncio
async def test_initialization_endpoint_missing_shop_argument(mocker):
    """
    Tests the initialization endpoint to be sure we only redirect if we have the app handle
    """
    shopify_app, app, client, store_name = initialize_store()

    # Missing shop argument
    response = client.get('/shopify/auth')
    assert response.status_code == 422
    body = response.json()
    assert body == {
        'detail': [
            {
                'loc': ['query', 'shop'],
                'msg': 'field required',
                'type': 'value_error.missing',
            }
        ],
    }


@pytest.mark.asyncio
async def test_initialization_endpoint_happy_path(mocker):
    """
    Tests to be sure that the initial redirect is working and is going to the right
    location.
    """
    shopify_app, app, client, shop_name = initialize_store()
    response = client.get(
        '/shopify/auth',
        params=dict(shop=shop_name),
        allow_redirects=False,
    )
    query = check_oauth_redirect_url(
        shop_name=shop_name,
        response=response,
        client=client,
        path='/admin/oauth/authorize',
    )
    check_oauth_redirect_query(
        shopify_app=shopify_app,
        query=query,
    )


@pytest.mark.asyncio
async def test_get_offline_tokens_happy_path(mocker):
    """
    Test to attempt to obtain a token for the user.
    """

    # Initialize the variables
    shopify_app, app, client, shop_name = initialize_store()
    offlineTokenData, onlineTokenData = generate_token_data(shopify_app)

    # First we run the redirection, allowing us to get the state
    response = client.get(
        '/shopify/auth',
        params=dict(shop=shop_name),
        allow_redirects=False,
    )
    query = check_oauth_redirect_url(
        shop_name=shop_name,
        response=response,
        client=client,
        path='/admin/oauth/authorize',
    )
    state = check_oauth_redirect_query(
        shopify_app=shopify_app,
        query=query,
    )

    # This sets up a fake endpoint for the online and offline tokens
    shopify_request_mock = mocker.patch('httpx.AsyncClient.request', new_callable=AsyncMock)
    shopify_request_mock.side_effect = [
        MockHTTPResponse(status_code=200, jsondata=offlineTokenData),
        MockHTTPResponse(status_code=200, jsondata=onlineTokenData),
    ]

    #
    query_str = urlencode(
        dict(
            shop=shop_name,
            state=state,
            timestamp=now_epoch(),
            code='INSTALLCODE',
        )
    )
    hmac_arg = hmac.calculate_from_message(secret=shopify_app.client_secret, message=query_str)
    query_str += '&hmac=' + hmac_arg

    response = client.get('/callback', params=query_str, allow_redirects=False)
    query = check_oauth_redirect_url(
        shop_name=shop_name,
        response=response,
        client=client,
        path='/admin/oauth/authorize',
    )
    state = check_oauth_redirect_query(
        shopify_app=shopify_app,
        query=query,
        query_extra={'grant_options[]': ['per-user']},
    )

    assert await shopify_request_mock.called_with(
        method='post',
        url=f'https://{shop_name}/admin/oauth/access_token',
        json={
            'client_id': shopify_app.client_id,
            'client_secret': shopify_app.client_secret,
            'code': 'INSTALLCODE',
        },
    )

    shopify_app.post_install.assert_called_once()
    shopify_app.post_install.assert_called_with(
        shopify_app,
        shopify_app.stores[shop_name].offline_access_token,
    )


@pytest.mark.asyncio
async def test_oauth(mocker):

    shopify_app, app, client = initialize_store()
    offlineTokenData, onlineTokenData = generate_token_data(shopify_app)

    response = client.get(
        '/shopify/auth',
        params=dict(shop=shopify_app.shopify_handle),
        allow_redirects=False,
    )

    query = check_oauth_redirect_url(
        shopify_app=shopify_app,
        response=response,
        client=client,
        path='/admin/oauth/authorize',
    )
    state = check_oauth_redirect_query(
        query=query,
        scope=shopify_app.app_scopes,
    )

    # Callback calls to get tokens
    shopify_request_mock = mocker.patch('httpx.AsyncClient.request', new_callable=AsyncMock)
    shopify_request_mock.side_effect = [
        MockHTTPResponse(status_code=200, jsondata=offlineTokenData),
        MockHTTPResponse(status_code=200, jsondata=onlineTokenData),
    ]
    # --------- Test the callback endpoint for installation -----------
    query_str = urlencode(
        dict(
            shop=shopify_app.shopify_handle,
            state=state,
            timestamp=now_epoch(),
            code='INSTALLCODE',
        )
    )
    hmac_arg = hmac.calculate_from_message(secret=shopify_app.client_secret, message=query_str)
    query_str += '&hmac=' + hmac_arg

    response = client.get('/callback', params=query_str, allow_redirects=False)
    query = check_oauth_redirect_url(
        shopify_app=shopify_app,
        response=response,
        client=client,
        path='/admin/oauth/authorize',
    )
    state = check_oauth_redirect_query(
        query=query,
        scope=shopify_app.user_scopes,
        query_extra={'grant_options[]': ['per-user']},
    )

    assert await shopify_request_mock.called_with(
        method='post',
        url=f'https://{shopify_app.shopify_handle}/admin/oauth/access_token',
        json={
            'client_id': shopify_app.shopify_handle,
            'client_secret': shopify_app.client_secret,
            'code': 'INSTALLCODE',
        },
    )

    shopify_app.post_install.assert_called_once()
    shopify_app.post_install.assert_called_with('test', offlineTokenData)

    # --------- Test the callback endpoint for login -----------
    query_str = urlencode(
        dict(
            shop=shopify_app.shopify_handle,
            state=state,
            timestamp=now_epoch(),
            code='LOGINCODE',
        ),
        safe='=,&/[]:',
    )
    hmac_arg = hmac.calculate_from_message(
        secret=shopify_app.client_secret,
        message=query_str,
    )
    query_str += '&hmac=' + hmac_arg

    response = client.get('/callback', params=query_str, allow_redirects=False)
    state = check_oauth_redirect_url(
        shopify_app=shopify_app,
        response=response,
        client=client,
        path=f'/admin/apps/{shopify_app.shopify_handle}',
    )

    assert await shopify_request_mock.called_with(
        method='post',
        url=f'https://{shopify_app.shopify_handle}/admin/oauth/access_token',
        json={
            'client_id': shopify_app.client_id,
            'client_secret': shopify_app.client_secret,
            'code': 'LOGINCODE',
        },
    )

    shopify_app.post_login.assert_called_once()
    shopify_app.post_login.assert_called_with('test', OnlineTokenResponse(**onlineTokenData))
