from copy import deepcopy
from dataclasses import dataclass
from urllib.parse import parse_qsl
from starlette.responses import RedirectResponse
from spylib.token import OfflineToken, OnlineToken, Token
from types import MethodType
from spylib.store import Store
from typing import Any, Callable, List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query
from inspect import isawaitable
from operator import itemgetter

from loguru import logger
from starlette.requests import Request


from .utils import get_unique_id, now_epoch
from .utils import JWTBaseModel
from .utils.hmac import validate as validate_hmac


@dataclass
class Callback:
    code: str = Query(...)
    hmac: str = Query(...)
    timestamp: int = Query(...)
    state: str = Query(...)
    shop: str = Query(...)


class OAuthJWT(JWTBaseModel):
    """
    OAuth JWT token. Contains
    """

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
        install_init_path: Optional[str] = '/shopify/auth',
        callback_path: Optional[str] = '/callback',
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

        # Binds the functions to the instance of the object
        if post_install:
            self.post_install = MethodType(post_install, self)

        # We don't redirect if the person is logged in
        if post_login:
            self.post_login = MethodType(post_login, self)
        else:
            self.post_login = None

        # Associate all of the stores with this current application
        self.stores: dict[str, Store] = {}

        for store in stores:
            if store.store_name not in self.stores:
                store.scopes = self.app_scopes
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
        return init_oauth_router(self)

    async def post_install(self, token: OfflineToken):
        """
        This is a function that is called after the installation of the app on a store
        This by default just runs and stores the token in the store.
        """
        self.stores[token.store_name].offline_access_token = token

    async def post_login(self, token: OnlineToken):
        """
        This is a function that is called after the login of a user in the app.
        This by default just runs and stores the token in the store.
        """
        self.stores[token.store_name].online_access_tokens[token.associated_user] = token

    def oauth_init_url(self, store_domain: str, is_login: bool) -> str:
        """
        Create the URL and the parameters needed to start the oauth process to
        install an app or to log a user in.

        Parameters
        ----------
        store_domain: The domain of the requesting store.
        is_login: Specify if the oauth is to install the app or a user logging in

        Returns
        -------
        string: Redirect URL to trigger the oauth process
        """

        # Gets the scopes for the application in string format
        scopes = ','.join(self.app_scopes)
        # We figure out the callback path for the application
        redirect_uri = f'https://{self.app_domain}{self.callback_path}'

        oauthjwt = OAuthJWT(
            is_login=is_login,
            storename=Store.domain_to_storename(store_domain),
            nonce=get_unique_id(),
        )
        oauth_token = oauthjwt.encode_token(key=self.client_secret)
        access_mode = 'per-user' if is_login else ''

        return (
            f'https://{store_domain}/admin/oauth/authorize?client_id={self.client_id}&'
            f'scope={scopes}&redirect_uri={redirect_uri}&state={oauth_token}&'
            f'grant_options[]={access_mode}'
        )

    def app_redirect(self, jwtoken: Optional[JWTBaseModel], store_domain: str) -> RedirectResponse:
        """ """
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
        if now_epoch() - timestamp > 300:
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
    This generates the routing functions for the Shopify OAuth endpoint. I wanted
    this to be a method within the auth class, but this causes a number of problems.
    So it is easier to just pass in an instance of the Auth class, which would have
    all of the related functions.

    This could also be reformed to take in the Store class later on if there is
    no need to separate the Authentication process and the Application, as this
    largely takes in parameters for the application.

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
        """REST endpoint called by Shopify during the OAuth process for installation and login"""
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

        # === If installation ===
        # Setup the login obj and redirect to oauth_redirect
        if not oauthjwt.is_login:
            try:
                # Get the offline token from Shopify
                offline_token = await OfflineToken.new(
                    store_name=args.shop,
                    scope=app.app_scopes,
                    client_id=app.client_id,
                    client_secret=app.client_secret,
                    code=args.code,
                )
                await app.post_install(offline_token)
            except Exception as e:
                logger.exception(f'Could not retrieve offline token for shop {args.shop}')
                raise HTTPException(status_code=400, detail=str(e))

            if app.post_login is None:
                return app.app_redirect(store_domain=args.shop, jwtoken=None)
            # Initiate the oauth loop for login
            return RedirectResponse(app.oauth_init_url(args.shop, is_login=True))

        # === If login ===
        # Get the online token from Shopify
        online_token = await app.OnlineToken.new(domain=args.shop, code=args.code)

        # Await if the provided function is async
        jwtoken = None
        pl_return = app.post_login(online_token)
        if isawaitable(pl_return):
            jwtoken = await pl_return  # type: ignore
        else:
            jwtoken = pl_return

        # Redirect to the app in Shopify admin
        return app.app_redirect(store_domain=args.shop, jwtoken=jwtoken)

    return router
