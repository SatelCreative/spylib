from typing import List
from unittest.mock import AsyncMock
from urllib.parse import ParseResult, parse_qs, urlencode, urlparse

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic.dataclasses import dataclass
from requests import Response  # type: ignore

from spylib.oauth import init_oauth_router
from spylib.utils import hmac, now_epoch
from tests.token_classes import (
    OfflineToken,
    OnlineToken,
    offline_token_data,
    online_token_data,
    test_information,
)


@dataclass
class MockHTTPResponse:
    status_code: int
    jsondata: dict
    headers: dict = None  # type: ignore

    def json(self):
        return self.jsondata


@pytest.mark.asyncio
async def test_oauth(mocker):

    app = FastAPI()

    # Python doesn't store Classes as variables within a class, rather as a nested class.
    oauth_router = init_oauth_router(
        test_information.app_scopes,
        test_information.user_scopes,
        test_information.public_domain,
        test_information.private_key,
        test_information.app_handle,
        test_information.api_key,
        test_information.api_secret_key,
        OfflineToken,
        OnlineToken,
    )

    app.include_router(oauth_router)
    client = TestClient(app)

    # --------- Test the initiTEST_DATA.alization endpoint -----------

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

    # Happy path
    response = client.get(
        '/shopify/auth', params=dict(shop=test_information.store), allow_redirects=False
    )
    query = check_oauth_redirect_url(
        response=response,
        client=client,
        path='/admin/oauth/authorize',
        scope=test_information.app_scopes,
    )
    state = check_oauth_redirect_query(query=query, scope=test_information.app_scopes)

    # Callback calls to get tokens
    shopify_request_mock = mocker.patch('httpx.AsyncClient.request', new_callable=AsyncMock)
    shopify_request_mock.side_effect = [
        MockHTTPResponse(status_code=200, jsondata=offline_token_data),
        MockHTTPResponse(status_code=200, jsondata=online_token_data),
    ]
    # --------- Test the callback endpoint for installation -----------
    query_str = urlencode(
        dict(shop=test_information.store, state=state, timestamp=now_epoch(), code='INSTALLCODE')
    )
    hmac_arg = hmac.calculate_from_message(
        secret=test_information.api_secret_key, message=query_str
    )
    query_str += '&hmac=' + hmac_arg

    response = client.get('/callback', params=query_str, allow_redirects=False)
    query = check_oauth_redirect_url(
        response=response,
        client=client,
        path='/admin/oauth/authorize',
        scope=test_information.user_scopes,
    )
    state = check_oauth_redirect_query(
        query=query,
        scope=test_information.user_scopes,
        query_extra={'grant_options[]': ['per-user']},
    )

    assert await shopify_request_mock.called_with(
        method='post',
        url=f'https://{test_information.store}/admin/oauth/access_token',
        json={
            'client_id': test_information.api_key,
            'client_secret': test_information.api_secret_key,
            'code': 'INSTALLCODE',
        },
    )

    # --------- Test the callback endpoint for login -----------
    query_str = urlencode(
        dict(shop=test_information.store, state=state, timestamp=now_epoch(), code='LOGINCODE'),
        safe='=,&/[]:',
    )
    hmac_arg = hmac.calculate_from_message(
        secret=test_information.api_secret_key, message=query_str
    )
    query_str += '&hmac=' + hmac_arg

    response = client.get('/callback', params=query_str, allow_redirects=False)
    state = check_oauth_redirect_url(
        response=response,
        client=client,
        path=f'/admin/apps/{test_information.app_handle}',
        scope=test_information.user_scopes,
    )

    assert await shopify_request_mock.called_with(
        method='post',
        url=f'https://{test_information.store}/admin/oauth/access_token',
        json={
            'client_id': test_information.api_key,
            'client_secret': test_information.api_secret_key,
            'code': 'LOGINCODE',
        },
    )


def check_oauth_redirect_url(response: Response, client, path: str, scope: List[str]) -> str:
    assert response.status_code == 307

    parsed_url = urlparse(client.get_redirect_target(response))

    expected_parsed_url = ParseResult(
        scheme='https',
        netloc=test_information.store,
        path=path,
        query=parsed_url.query,  # We check that separately
        params='',
        fragment='',
    )
    assert parsed_url == expected_parsed_url

    return parsed_url.query


def check_oauth_redirect_query(query: str, scope: List[str], query_extra: dict = {}) -> str:
    parsed_query = parse_qs(query)
    state = parsed_query.pop('state', [''])[0]

    expected_query = dict(
        client_id=[test_information.api_key],
        redirect_uri=[f'https://{test_information.public_domain}/callback'],
        scope=[','.join(scope)],
    )
    expected_query.update(query_extra)

    assert parsed_query == expected_query

    return state
