from copy import deepcopy
from dataclasses import dataclass
from spylib.store import Store
from fastapi import APIRouter, Depends, HTTPException, Query
from inspect import isawaitable
from typing import Any, Callable, List, Optional, Tuple
from types import MethodType
from urllib.parse import parse_qsl

from loguru import logger
from pydantic.main import BaseModel
from starlette.requests import Request
from starlette.responses import RedirectResponse

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


class Auth(BaseModel):
    def __init__(
        self,
        app_domain: str,
        app_scopes: List[str],
        user_scopes: List[str],
        client_id: str,
        client_secret: str,
        app_handle: str,
        post_install: Optional[Callable] = None,
        post_login: Optional[Callable] = None,
        install_init_path: str = '/shopify/auth',
        callback_path: str = '/callback',
    ):
        self.app_domain = app_domain
        self.app_scopes = app_scopes
        self.user_scopes = user_scopes
        self.callback_path = callback_path
        self.client_id = client_id
        self.secret_key = client_secret
        self.app_handle = app_handle
        self.install_init_path = install_init_path
        self.callback_path = callback_path

        # We initialize the post login and install as methods on the instance
        # which allows us to avoid requiring extending the class which is a mess.
        if post_install:
            self.post_install = MethodType(post_install, self)
        if post_login:
            self.post_login = MethodType(post_login, self)

    def post_install(self, store: Store):
        """This is a function that is called after the installation of the app on a store"""
        pass

    def post_login(self, store: Store):
        """This is a function that is called after the login of a user in the app."""
        pass

    def oauth_init_url(self, store_domain: str, is_login: bool, jwt_key: str) -> str:
        """
        Create the URL and the parameters needed to start the oauth process to
        install an app or to log a user in.

        Parameters
        ----------
        store_domain: The domain of the requesting store.
        is_login: Specify if the oauth is to install the app or a user logging in
        jwt_key: The session JWT token for the user

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
        oauth_token = oauthjwt.encode_token(key=jwt_key)
        access_mode = 'per-user' if is_login else ''

        return (
            f'https://{self.app_domain}/admin/oauth/authorize?client_id={self.client_id}&'
            f'scope={scopes}&redirect_uri={redirect_uri}&state={oauth_token}&'
            f'grant_options[]={access_mode}'
        )

    def app_redirect(self, jwtoken: Optional[JWTBaseModel], store_domain: str) -> RedirectResponse:
        """ """
        if jwtoken is None:
            return RedirectResponse(f'https://{store_domain}/admin/apps/{self.app_handle}')

        jwtarg, signature = jwtoken.encode_hp_s(key=self.jwt_key)

        redir = RedirectResponse(
            f'https://{store_domain}/admin/apps/{self.app_handle}?jwt={jwtarg}'
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
            # Let's assume alphabetical sorting to avoid issues with scrambled args when using bonnette
            args.sort(key=itemgetter(0))
            self._validate_callback_args(args=args)
        except ValueError:
            # Try with the original ordering
            self._validate_callback_args(args=original_args)


def init_oauth_router(auth: Auth) -> APIRouter:
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

    if not auth.install_init_path.startswith('/'):
        raise ValueError('The install_init_path argument must start with "/"')
    if not auth.callback_path.startswith('/'):
        raise ValueError('The callback_path argument must start with "/"')

    @router.get(auth.install_init_path, include_in_schema=False)
    async def shopify_auth(shop: str):
        """Endpoint initiating the OAuth process on a Shopify store"""
        return RedirectResponse(auth.oauth_init_url(is_login=False, jwt_key=auth.private_key))

    @router.get(auth.callback_path, include_in_schema=False)
    async def shopify_callback(request: Request, args: Callback = Depends(Callback)):
        """REST endpoint called by Shopify during the OAuth process for installation and login"""
        try:
            auth.validate_callback(
                shop=args.shop,
                timestamp=args.timestamp,
                query_string=request.scope['query_string'],
            )
            oauthjwt: OAuthJWT = auth.validate_oauthjwt(
                token=args.state, shop=args.shop, jwt_key=auth.jwt_key
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f'Validation failed: {e}')

        # === If installation ===
        # Setup the login obj and redirect to oauth_redirect
        if not oauthjwt.is_login:
            try:
                # Get the offline token from Shopify
                offline_token = await auth.OfflineToken.new(domain=args.shop, code=args.code)
            except Exception as e:
                logger.exception(f'Could not retrieve offline token for shop {args.shop}')
                raise HTTPException(status_code=400, detail=str(e))

            # Await if the provided function is async
            if isawaitable(pi_return := auth.post_install(oauthjwt.storename, offline_token)):
                await pi_return  # type: ignore

            if auth.post_login is None:
                return auth.app_redirect(jwtoken=None)
            # Initiate the oauth loop for login
            return RedirectResponse(auth.oauth_init_url(is_login=True))

        # === If login ===
        # Get the online token from Shopify
        online_token = await auth.OnlineToken.new(domain=args.shop, code=args.code)

        # Await if the provided function is async
        jwtoken = None
        pl_return = auth.post_login(oauthjwt.storename, online_token)
        if isawaitable(pl_return):
            jwtoken = await pl_return  # type: ignore
        else:
            jwtoken = pl_return

        # Redirect to the app in Shopify admin
        return auth.app_redirect(store_domain=args.shop, jwtoken=jwtoken)

    return router
