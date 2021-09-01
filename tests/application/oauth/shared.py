from typing import Callable, Dict, Optional, Tuple

from fastapi import FastAPI
from fastapi.testclient import TestClient

from spylib.application import ShopifyApplication
from spylib.store import Store


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

    store_name = 'test.myshopify.com'

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
