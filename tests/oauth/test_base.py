from typing import List
from unittest.mock import AsyncMock
from urllib.parse import ParseResult, parse_qs, urlencode, urlparse

import pytest
from box import Box  # type: ignore
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic.dataclasses import dataclass
from requests import Response  # type: ignore

from spylib.oauth import OfflineToken, OnlineToken, conf, init_oauth_router
from spylib.utils import JWTBaseModel, hmac, now_epoch

TEST_STORE = 'test.myshopify.com'
TEST_DATA = Box(
    dict(
        app_scopes=['write_products', 'read_customers'],
        user_scopes=['write_orders', 'read_products'],
        public_domain='test.testing.com',
        private_key='TESTPRIVATEKEY',
        post_install=AsyncMock(return_value=JWTBaseModel()),
        post_login=AsyncMock(return_value=None),
    )
)

OFFLINETOKEN_DATA = dict(access_token='OFFLINETOKEN', scope=','.join(TEST_DATA.app_scopes))
ONLINETOKEN_DATA = dict(
    access_token='ONLINETOKEN',
    scope=','.join(TEST_DATA.app_scopes),
    expires_in=86399,
    associated_user_scope=','.join(TEST_DATA.user_scopes),
    associated_user={
        'id': 902541635,
        'first_name': 'John',
        'last_name': 'Smith',
        'email': 'john@example.com',
        'email_verified': True,
        'account_owner': True,
        'locale': 'en',
        'collaborator': False,
    },
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

    oauth_router = init_oauth_router(**TEST_DATA)

    app.include_router(oauth_router)
    client = TestClient(app)

    # --------- Test the initialization endpoint -----------

    # Missing shop argument
    response = client.get('/shopify/auth')
    assert response.status_code == 422
    assert response.json() == {
        'detail': [
            {'loc': ['query', 'shop'], 'msg': 'field required', 'type': 'value_error.missing'}
        ],
    }

    # Happy path
    response = client.get('/shopify/auth', params=dict(shop=TEST_STORE), allow_redirects=False)
    query = check_oauth_redirect_url(
        response=response, client=client, path='/admin/oauth/authorize', scope=TEST_DATA.app_scopes
    )
    state = check_oauth_redirect_query(query=query, scope=TEST_DATA.app_scopes)

    # Callback calls to get tokens
    shopify_request_mock = mocker.patch('httpx.AsyncClient.request', new_callable=AsyncMock)
    shopify_request_mock.side_effect = [
        MockHTTPResponse(status_code=200, jsondata=OFFLINETOKEN_DATA),
        MockHTTPResponse(status_code=200, jsondata=ONLINETOKEN_DATA),
    ]
    # --------- Test the callback endpoint for installation -----------
    query_str = urlencode(
        dict(shop=TEST_STORE, state=state, timestamp=now_epoch(), code='INSTALLCODE')
    )
    hmac_arg = hmac.calculate_from_message(secret=conf.secret_key, message=query_str)
    query_str += '&hmac=' + hmac_arg

    response = client.get('/callback', params=query_str, allow_redirects=False)
    query = check_oauth_redirect_url(
        response=response,
        client=client,
        path='/admin/oauth/authorize',
        scope=TEST_DATA.user_scopes,
    )
    state = check_oauth_redirect_query(
        query=query,
        scope=TEST_DATA.user_scopes,
        query_extra={'grant_options[]': ['per-user']},
    )

    assert await shopify_request_mock.called_with(
        method='post',
        url=f'https://{TEST_STORE}/admin/oauth/access_token',
        json={'client_id': conf.api_key, 'client_secret': conf.secret_key, 'code': 'INSTALLCODE'},
    )

    TEST_DATA.post_install.assert_called_once()
    TEST_DATA.post_install.assert_called_with('test', OfflineToken(**OFFLINETOKEN_DATA))

    # --------- Test the callback endpoint for login -----------
    query_str = urlencode(
        dict(shop=TEST_STORE, state=state, timestamp=now_epoch(), code='LOGINCODE'), safe='=,&/[]:'
    )
    hmac_arg = hmac.calculate_from_message(secret=conf.secret_key, message=query_str)
    query_str += '&hmac=' + hmac_arg

    response = client.get('/callback', params=query_str, allow_redirects=False)
    state = check_oauth_redirect_url(
        response=response,
        client=client,
        path=f'/admin/apps/{conf.handle}',
        scope=TEST_DATA.user_scopes,
    )

    assert await shopify_request_mock.called_with(
        method='post',
        url=f'https://{TEST_STORE}/admin/oauth/access_token',
        json={'client_id': conf.api_key, 'client_secret': conf.secret_key, 'code': 'LOGINCODE'},
    )

    TEST_DATA.post_login.assert_called_once()
    TEST_DATA.post_login.assert_called_with('test', OnlineToken(**ONLINETOKEN_DATA))


def check_oauth_redirect_url(response: Response, client, path: str, scope: List[str]) -> str:
    print(response.text)
    assert response.status_code == 307

    parsed_url = urlparse(client.get_redirect_target(response))

    expected_parsed_url = ParseResult(
        scheme='https',
        netloc=TEST_STORE,
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
        client_id=[conf.api_key],
        redirect_uri=[f'https://{TEST_DATA.public_domain}/callback'],
        scope=[','.join(scope)],
    )
    expected_query.update(query_extra)

    assert parsed_query == expected_query

    return state
