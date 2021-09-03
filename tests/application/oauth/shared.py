from typing import Callable, Dict, Optional, Tuple
from urllib.parse import ParseResult, parse_qs, urlparse

from fastapi import FastAPI
from fastapi.testclient import TestClient
from requests import Response

from spylib.application import ShopifyApplication
from spylib.store import Store
from spylib.token import OfflineTokenResponse, OnlineToken, OnlineTokenResponse


def check_oauth_redirect_url(
    shop_domain: str,
    response: Response,
    client,
    path: str,
) -> str:
    assert response.text == ''
    assert response.status_code == 307

    redirect_target = urlparse(client.get_redirect_target(response))

    expected_parsed_url = ParseResult(
        scheme='https',
        netloc=shop_domain,
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
    if token.associated_user:
        self.stores[token.store_name].online_access_tokens[token.associated_user.id] = token


def initialize_store(
    post_install: Optional[Callable] = None,
    post_login: Optional[Callable] = None,
) -> Tuple[ShopifyApplication, FastAPI, TestClient, str]:
    tokens: Dict[str, str] = {}

    # These are the methods passed into the store to save the tokens
    def save_token(self, store_name: str, key: str):
        tokens[store_name] = key

    def load_token(self, store_name: str):
        return tokens[store_name]

    # Create a store that we will be accessing

    store_name = 'test'

    store = Store(
        store_name=store_name,
        save_token=save_token,
        load_token=load_token,
    )

    # Generate our application which includes the store
    shopify_app = ShopifyApplication(
        app_domain='test.testing.com',
        shopify_handle='HANDLE',
        app_scopes=['write_products', 'read_customers'],
        client_id='API_KEY',
        client_secret='TESTPRIVATEKEY',
        post_install=post_install,
        post_login=post_login,
        stores=[store],
    )

    # Generating the fastAPI routes, and the client for testing
    app = FastAPI()

    oauth_router = shopify_app.generate_oauth_routes()

    app.include_router(oauth_router)

    client = TestClient(app)

    return (shopify_app, app, client, store_name)
