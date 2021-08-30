from spylib.store import Store
from typing import Callable, List, Optional
from pydantic.main import BaseModel
from .oauth import Auth, init_oauth_router
from fastapi.routing import APIRouter


class ShopifyApplication(BaseModel):
    """
    This class contains the logic for an app. This includes the oauth authentication
    along with the set of stores that are registered for the application.
    """

    def __init__(
        self,
        app_domain: str,
        app_scopes: List[str],
        client_id: str,
        client_secret: str,
        shopify_handle: str,
        post_install: Optional[Callable],
        post_login: Optional[Callable],
        user_scopes: Optional[List[str]] = None,
        install_init_path: Optional[str] = '/callback',
        callback_path: Optional[str] = '/shopify/auth',
        stores: Optional[Store] = [],
    ) -> None:
        """
        - `app_domain` - This is the domain of the app where the application is hosted
        - `app_scopes` - The required scopes for shopify for our shopify app
        - `client_id` - This is the identifier for the application used in OAuth flow
            also occasionally refereed to as the api_key
        - `client_secret` - This is the secret for the application used in OAuth flow
        - `shopify_handle` -
        - `post_install` - This is a function that gets called after the app is installed
        - `post_login` - This is a function that gets called after a user logs into the app
        - `callback_path` - This is the location of the calback endpoint for OAuth
        - `install_init_path` - This is the location of the initial request to trigger OAuth
        """

        # Assign all constants for the application
        self.app_domain = app_domain
        self.callback_path = callback_path
        self.install_init_path = install_init_path
        self.app_scopes = app_scopes
        self.user_scopes = user_scopes
        self.client_id = client_id
        self.client_secret = client_secret
        self.shopify_handle = shopify_handle
        self.post_install = post_install
        self.post_login = post_login

        # Generates the OAuth object for this application using the Auth class
        # passed into this function
        self.auth = Auth(
            self.app_domain,
            self.app_scopes,
            self.user_scopes,
            self.client_id,
            self.client_secret,
            self.shopify_handle,
            self.post_install,
            self.post_login,
        )

        # Associate all of the stores with this current application
        self.stores = {}

        for store in stores:
            if store.store_name not in self.stores:
                self.stores[store.store_name] = store

    def get_store(self, name: str) -> Optional[Store]:
        if name not in self.stores:
            raise ValueError(f"Store {name} does not exist. Is it spelled properly?")
        return self.stores[name]

    def remove_store(self, name: str) -> None:
        if name not in self.stores:
            raise ValueError(f"Store {name} does not exist. Is it spelled properly?")
        del self.stores[name]

    def get_all_stores(self) -> dict:
        return self.stores

    def generate_oauth_routes(self) -> APIRouter:
        """
        Generates the OAuth authentication routes for this application.
        """
        return init_oauth_router(self.auth)
