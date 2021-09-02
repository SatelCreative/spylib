from copy import deepcopy
from dataclasses import dataclass
from inspect import isawaitable
from operator import itemgetter
from types import MethodType
from typing import Any, Callable, List, Optional, Tuple
from urllib.parse import parse_qsl

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from starlette.requests import Request
from starlette.responses import RedirectResponse

from spylib.exceptions import UndefinedStoreError
from spylib.store import Store
from spylib.token import OfflineToken, OnlineToken, Token

from .utils.hmac import validate as validate_hmac
from .utils.JWT import JWT


@dataclass
class Callback:
    code: str = Query(...)
    hmac: str = Query(...)
    timestamp: int = Query(...)
    state: str = Query(...)
    shop: str = Query(...)


class OAuthJWT(JWT):

    is_login: bool
    storename: str
    nonce: Optional[str] = None


class ShopifyApplication:
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
        post_install: Optional[Callable] = None,
        post_login: Optional[Callable] = None,
        user_scopes: Optional[List[str]] = None,
        install_init_path: str = '/shopify/auth',
        callback_path: str = '/callback',
        stores: List[Store] = [],
    ) -> None:
        """
        - `app_domain` - This is the domain of the app where the application is hosted
        - `app_scopes` - The required scopes for shopify for our shopify app
        - `client_id` - This is the identifier for the application used in OAuth flow
            also occasionally referred to as the api_key
        - `client_secret` - This is the secret for the application used in OAuth flow
        - `shopify_handle` - Name of the app on shopify, this is where it is accessed in admin
        - `post_install` - This is a function that gets called after the app is installed
        - `post_login` - This is a function that gets called after a user logs into the app
        - `user_scopes` - Scopes for the users if not the same as the application scopes
        - `install_init_path` - This is the location of the initial request to trigger OAuth
        - `callback_path` - This is the location of the calback endpoint for OAuth
        - `stores` - This is an array of all of the stores that will be initialized in this
            application
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

        # Binds the functions to the instance of the object
        if post_install:
            self.post_install = MethodType(post_install, self)  # type: ignore

        # We don't redirect if the person is logged in
        if post_login:
            self.post_login: Optional[MethodType] = MethodType(post_login, self)
        else:
            self.post_login = None

        # Associate all of the stores with this current application
        self.stores: dict[str, Store] = {}

        for store in stores:
            if store.store_name not in self.stores:
                store.scopes = self.app_scopes
                self.stores[store.store_name] = store

    def get_store(self, name: str) -> Store:
        if name not in self.stores:
            raise UndefinedStoreError(store=name)
        return self.stores[name]

    def remove_store(self, name: str) -> None:
        if name not in self.stores:
            raise UndefinedStoreError(store=name)
        del self.stores[name]

    def generate_oauth_routes(self) -> APIRouter:
        """
        Generates the OAuth authentication routes for this application.
        """
        return init_oauth_router(self)

    def post_install(self, token: OfflineToken):
        """
        This is a function that is called after the installation of the app on a store
        This by default just runs and stores the token in the store.
        """
        self.stores[token.store_name].offline_access_token = token

    def oauth_init_url(self, store_domain: str, is_login: bool) -> str:
        """
        Create the URL and the parameters needed to start the oauth process to
        install an app or to log a user in.

        Parameters:

        - `store_domain`: The domain of the requesting store.
        - `is_login`: Specify if the oauth is to install the app or a user logging in

        Returns:

        - `string`: Redirect URL to trigger the oauth process
        """

        # Gets the scopes for the application in string format
        scopes = ','.join(self.app_scopes)
        # We figure out the callback path for the application
        redirect_uri = f'https://{self.app_domain}{self.callback_path}'

        oauthjwt = OAuthJWT(
            is_login=is_login,
            storename=Store.domain_to_storename(store_domain),
            nonce=Token.get_unique_id(),
        )
        oauth_token = oauthjwt.encode_token(key=self.client_secret)
        access_mode = 'per-user' if is_login else ''

        return (
            f'https://{store_domain}/admin/oauth/authorize?client_id={self.client_id}&'
            f'scope={scopes}&redirect_uri={redirect_uri}&state={oauth_token}&'
            f'grant_options[]={access_mode}'
        )

    def app_redirect(self, jwtoken: Optional[JWT], store_domain: str) -> RedirectResponse:
        """
        Redirects the app based on the type of request. If we are using the offline
        token, the app is constantly auth'ed until it is revoked. If it is Online
        then we encode and send the JWT token along.
        """
        if jwtoken is None:
            return RedirectResponse(f'https://{store_domain}/admin/apps/{self.shopify_handle}')

        jwtarg, signature = jwtoken.encode_hp_s(key=self.client_secret)

        redir = RedirectResponse(
            f'https://{store_domain}/admin/apps/{self.shopify_handle}?jwt={jwtarg}'
        )

        # TODO set 'expires'
        redir.set_cookie(
            key=jwtoken.cookie_key,
            value=signature,
            domain=self.app_domain,
            httponly=True,
            secure=True,
        )

        return redir

    def _validate_callback_args(self, args: List[Tuple[str, str]]) -> None:
        # We assume here that the arguments were validated prior to calling
        # this function.
        hmac_arg = [arg[1] for arg in args if arg[0] == 'hmac'][0]
        message = '&'.join([f'{arg[0]}={arg[1]}' for arg in args if arg[0] != 'hmac'])
        # Check HMAC
        validate_hmac(secret=self.client_secret, sent_hmac=hmac_arg, message=message)

    def validate_callback(self, shop: str, timestamp: int, query_string: Any) -> None:
        q_str = query_string.decode('utf-8')

        # 1) Check that the shop is a valid Shopify URL
        Store.domain_to_storename(shop)

        # 2) Check the timestamp. Must not be more than 5min old
        if JWT.now_epoch() - timestamp > 300:
            raise ValueError('Timestamp is too old')

        # 3) Check the hmac
        # Extract HMAC
        args = parse_qsl(q_str)
        original_args = deepcopy(args)
        try:
            # Let's assume alphabetical sorting to avoid issues with scrambled
            # args when using bonnette
            args.sort(key=itemgetter(0))
            self._validate_callback_args(args=args)
        except ValueError:
            # Try with the original ordering
            self._validate_callback_args(args=original_args)

    def validate_oauthjwt(self, token: str, shop: str) -> OAuthJWT:
        oauthjwt = OAuthJWT.decode_token(token=token, key=self.client_secret)

        storename = Store.domain_to_storename(shop)
        if oauthjwt.storename != storename:
            raise ValueError('Token storename and query shop don\'t match')

        return oauthjwt


def init_oauth_router(app: ShopifyApplication) -> APIRouter:
    """
    This generates the routing functions for the Shopify OAuth endpoint. This
    can then be bound to the FastAPI object.
    """
    router = APIRouter()

    if not app.install_init_path.startswith('/'):
        raise ValueError('The install_init_path argument must start with "/"')
    if not app.callback_path.startswith('/'):
        raise ValueError('The callback_path argument must start with "/"')

    @router.get(app.install_init_path, include_in_schema=False)
    async def shopify_auth(shop: str):
        """Endpoint initiating the OAuth process on a Shopify store"""
        domain = Store.store_domain(shop)
        redirect_url = app.oauth_init_url(
            store_domain=domain,
            is_login=False,
        )
        return RedirectResponse(redirect_url)

    @router.get(app.callback_path, include_in_schema=False)
    async def shopify_callback(request: Request, args: Callback = Depends(Callback)):
        """
        REST endpoint called by Shopify during the OAuth process for installation
        and login
        """
        # Checks the validity of the token
        try:
            app.validate_callback(
                shop=args.shop,
                timestamp=args.timestamp,
                query_string=request.scope['query_string'],
            )
            oauthjwt: OAuthJWT = app.validate_oauthjwt(
                token=args.state,
                shop=args.shop,
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f'Validation failed: {e}')

        # If we are generating an offline token
        if not oauthjwt.is_login:
            # Generate a new offline token, which is stored in the apps store
            try:
                offline_token = await OfflineToken.new(
                    store_name=args.shop,
                    client_id=app.client_id,
                    client_secret=app.client_secret,
                    code=args.code,
                )
            except Exception as e:
                logger.exception(f'Could not retrieve offline token for shop {args.shop}')
                raise HTTPException(status_code=400, detail=str(e))

            # We then call the callback on the offline token
            result = app.post_install(offline_token)
            if isawaitable(result):
                await result

            if app.post_login is None:
                return app.app_redirect(store_domain=args.shop, jwtoken=None)

            return RedirectResponse(app.oauth_init_url(args.shop, is_login=True))

        # Else we are generating an online token
        online_token = await OnlineToken.new(
            store_name=args.shop,
            client_id=app.client_id,
            client_secret=app.client_secret,
            code=args.code,
        )

        # Await if the provided function is async
        jwtoken = None
        if app.post_login:
            pl_return = app.post_login(online_token)
        if isawaitable(pl_return):
            jwtoken = await pl_return  # type: ignore
        else:
            jwtoken = pl_return

        # Redirect to the app in Shopify admin
        return app.app_redirect(store_domain=args.shop, jwtoken=jwtoken)

    return router
