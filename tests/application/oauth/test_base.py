from typing import Tuple
from spylib.store import Store
from spylib.application import ShopifyApplication
from unittest.mock import AsyncMock, patch
from urllib.parse import ParseResult, parse_qs, urlencode, urlparse

import pytest
from pydantic.dataclasses import dataclass
from requests import Response

from spylib.token import OfflineToken, OfflineTokenResponse, OnlineToken, OnlineTokenResponse
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


def post_login(self: ShopifyApplication, token: OnlineToken):
    self.stores[token.store_name].online_access_tokens[token.associated_user.id] = token


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
async def test_initialization_endpoint(mocker):
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
async def test_offline_token(mocker):
    """
    Test to attempt to obtain a token for the user. This tests the case where
    the app is only using offline tokens.
    """

    # Initialize the variables
    shopify_app, app, client, shop_name = initialize_store()
    offlineTokenData, onlineTokenData = generate_token_data(shopify_app)

    # First we run the redirection, allowing us to get the state which is
    # a JWT token which can verify if the user is logged in, the store name,
    # and the nonce

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

    # This is mocking the callback from the Shopify server, which should
    # send the authentication code `code` to the callback endpoint which
    # can then be exchanged for a long term auth code
    query_str = urlencode(
        dict(
            shop=shop_name,
            state=state,
            timestamp=now_epoch(),
            code='INSTALLCODE',
        )
    )

    # The HMAC is a check to be sure the message hasn't been changed
    hmac_arg = hmac.calculate_from_message(secret=shopify_app.client_secret, message=query_str)
    query_str += '&hmac=' + hmac_arg

    response = client.get('/callback', params=query_str, allow_redirects=False)

    # As the Token object triggers the request for the code we can check to see
    # if it redirects back to the app location on the shopify store
    query = check_oauth_redirect_url(
        shop_name=shop_name,
        response=response,
        client=client,
        path=f'/admin/apps/{shopify_app.shopify_handle}',
    )

    # Check to see if the endpoint got called to obtain the token
    assert await shopify_request_mock.called_with(
        method='post',
        url=f'https://{shop_name}/admin/oauth/access_token',
        json={
            'client_id': shopify_app.client_id,
            'client_secret': shopify_app.client_secret,
            'code': 'INSTALLCODE',
        },
    )


@pytest.mark.asyncio
async def test_offline_token_redirect_online(mocker):
    """
    Test to attempt to obtain a token for the user. This tests the case where
    the app is using an offline token, but also would like to request that a
    user login to their personal account for frontend actions.
    """

    # Initialize the variables
    shopify_app, app, client, shop_name = initialize_store(post_login=post_login)
    offlineTokenData, onlineTokenData = generate_token_data(shopify_app)

    # First we run the redirection, allowing us to get the state which is
    # a JWT token which can verify if the user is logged in, the store name,
    # and the nonce

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

    # This is mocking the callback from the Shopify server, which should
    # send the authentication code `code` to the callback endpoint which
    # can then be exchanged for a long term auth code
    query_str = urlencode(
        dict(
            shop=shop_name,
            state=state,
            timestamp=now_epoch(),
            code='INSTALLCODE',
        )
    )

    # The HMAC is a check to be sure the message hasn't been changed
    hmac_arg = hmac.calculate_from_message(secret=shopify_app.client_secret, message=query_str)
    query_str += '&hmac=' + hmac_arg

    response = client.get('/callback', params=query_str, allow_redirects=False)

    # As the Token object triggers the request for the code we can check to see
    # if it redirects back to the proper location.
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

    # Check to see if the endpoint got called to obtain the token
    assert await shopify_request_mock.called_with(
        method='post',
        url=f'https://{shop_name}/admin/oauth/access_token',
        json={
            'client_id': shopify_app.client_id,
            'client_secret': shopify_app.client_secret,
            'code': 'INSTALLCODE',
        },
    )


@pytest.mark.asyncio
async def test_online_token(mocker):
    """
    Test to attempt to obtain an online token for the user. We must trigger the
    whole auth process to achieve this.
    """

    # Initialize the variables
    shopify_app, app, client, shop_name = initialize_store(post_login=post_login)
    offlineTokenData, onlineTokenData = generate_token_data(shopify_app)

    # First we run the redirection, allowing us to get the state which is
    # a JWT token which can verify if the user is logged in, the store name,
    # and the nonce

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

    # This is mocking the callback from the Shopify server, which should
    # send the authentication code `code` to the callback endpoint which
    # can then be exchanged for a long term auth code
    query_str = urlencode(
        dict(
            shop=shop_name,
            state=state,
            timestamp=now_epoch(),
            code='INSTALLCODE',
        )
    )

    # The HMAC is a check to be sure the message hasn't been changed
    hmac_arg = hmac.calculate_from_message(secret=shopify_app.client_secret, message=query_str)
    query_str += '&hmac=' + hmac_arg

    response = client.get('/callback', params=query_str, allow_redirects=False)

    # As the Token object triggers the request for the code we can check to see
    # if it redirects back to the proper location.
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

    # Now we can trigger the callback based on a user logging into the app and
    # approving an online token
    query_str = urlencode(
        dict(
            shop=shop_name,
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

    # We can then check to see if redirected with appropriate info
    state = check_oauth_redirect_url(
        shop_name=shop_name,
        response=response,
        client=client,
        path=f'/admin/apps/{shopify_app.shopify_handle}',
    )

    assert await shopify_request_mock.called_with(
        method='post',
        url=f'https://{shop_name}/admin/oauth/access_token',
        json={
            'client_id': shopify_app.client_id,
            'client_secret': shopify_app.client_secret,
            'code': 'LOGINCODE',
        },
    )
