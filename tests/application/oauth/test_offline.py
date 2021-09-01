from unittest.mock import AsyncMock
from urllib.parse import urlencode

import pytest

from spylib.utils import hmac, now_epoch

from ..shared import MockHTTPResponse
from .shared import (
    check_oauth_redirect_query,
    check_oauth_redirect_url,
    generate_token_data,
    initialize_store,
    post_login,
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
