from spylib.store import Store
from spylib.application import ShopifyApplication
from typing import Dict, List, Tuple
from unittest.mock import AsyncMock
from urllib.parse import ParseResult, parse_qs, urlencode, urlparse

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic.dataclasses import dataclass
from requests import Response

from spylib.token import OfflineTokenResponse, OnlineTokenResponse
from spylib.utils import hmac, now_epoch


@dataclass
class MockHTTPResponse:
    status_code: int
    jsondata: dict
    headers: dict = None  # type: ignore

    def json(self):
        return self.jsondata


def check_oauth_redirect_url(
    shopify_app: ShopifyApplication,
    response: Response,
    client,
    path: str,
) -> str:
    print(response.text)
    assert response.status_code == 307

    parsed_url = urlparse(client.get_redirect_target(response))

    expected_parsed_url = ParseResult(
        scheme='https',
        netloc=shopify_app.shopify_handle,
        path=path,
        query=parsed_url.query,  # We check that separately
        params='',
        fragment='',
    )
    assert parsed_url == expected_parsed_url

    return parsed_url.query


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
        scope=shopify_app.app_scopes,
    )
    expected_query.update(query_extra)

    assert parsed_query == expected_query

    return state


def initialize_store() -> Tuple[ShopifyApplication, FastAPI, TestClient]:
    tokens: Dict[str, str] = {}

    # These are the methods passed into the store to save the tokens
    def save_token(self, store_name: str, key: str):
        tokens[store_name] = key

    def load_token(self, store_name: str):
        return tokens[store_name]

    # Create a store that we will be accessing
    store = Store(
        store_name='test-store',
        save_token=save_token,
        load_token=load_token,
    )

    # Generate our application which includes the store
    shopify_app = ShopifyApplication(
        app_domain='test.testing.com',
        shopify_handle='test.myshopify.com',
        app_scopes=['write_products', 'read_customers'],
        client_id='test.testing.com',
        client_secret='TESTPRIVATEKEY',
        stores=[store],
    )

    # Generating the fastAPI routes, and the client for testing
    app = FastAPI()

    oauth_router = shopify_app.generate_oauth_routes()

    app.include_router(oauth_router)

    client = TestClient(app)

    return (shopify_app, app, client)


@pytest.mark.asyncio
async def test_oauth(mocker):
    """
    Tests the initialization endpoint to be sure we only redirect if we have the app handle
    """

    shopify_app, app, client = initialize_store()

    offlineTokenData = OfflineTokenResponse(
        access_token='OFFLINETOKEN',
        scope=','.join(shopify_app.app_scopes),
    )

    onlineTokenData = OnlineTokenResponse(
        access_token='ONLINETOKEN',
        scope=','.join(shopify_app.app_scopes),
        expires_in=86399,
        associated_user_scope=','.join(shopify_app.user_scopes),
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
    # --------- Test the initialization endpoint -----------

    # Missing shop argument
    response = client.get('/shopify/auth')
    assert response.status_code == 422
    assert response.json() == {
        'detail': [
            {
                'loc': ['query', 'shop'],
                'msg': 'field required',
                'type': 'value_error.missing',
            }
        ],
    }

    """
    Check to see if we are able to initialize the redirect to oauth
    """
    response = client.get(
        '/shopify/auth',
        params=dict(shop=shopify_app.shopify_handle),
        allow_redirects=False,
    )

    query = check_oauth_redirect_url(
        response=response,
        client=client,
        path='/admin/oauth/authorize',
        scope=shopify_app.app_scopes,
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
        response=response,
        client=client,
        path='/admin/oauth/authorize',
        scope=shopify_app.user_scopes,
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
    shopify_app.post_install.assert_called_with('test', OfflineTokenResponse(**offlineTokenData))

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
        response=response,
        client=client,
        path=f'/admin/apps/{shopify_app.shopify_handle}',
        scope=shopify_app.user_scopes,
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
