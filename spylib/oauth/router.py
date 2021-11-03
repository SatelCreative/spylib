from dataclasses import dataclass
from typing import List, Optional, Type

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from starlette.requests import Request
from starlette.responses import RedirectResponse

from spylib.token import (
    OfflineTokenABC,
    OfflineTokenResponse,
    OnlineTokenABC,
    OnlineTokenResponse,
    get_token,
)

from ..utils import OAuthJWT, store_domain
from .redirects import app_redirect, oauth_init_url
from .validations import validate_callback, validate_oauthjwt


@dataclass
class Callback:
    code: str = Query(...)
    hmac: str = Query(...)
    timestamp: int = Query(...)
    state: str = Query(...)
    shop: str = Query(...)


def init_oauth_router(
    app_scopes: List[str],
    user_scopes: List[str],
    public_domain: str,
    private_key: str,
    app_handle: str,
    api_key: str,
    api_secret_key: str,
    OfflineToken: Type[OfflineTokenABC],
    OnlineToken: Optional[Type[OnlineTokenABC]] = None,
    install_init_path='/shopify/auth',
    callback_path='/callback',
) -> APIRouter:
    router = APIRouter()

    if not install_init_path.startswith('/'):
        raise ValueError('The install_init_path argument must start with "/"')
    if not callback_path.startswith('/'):
        raise ValueError('The callback_path argument must start with "/"')

    @router.get(install_init_path, include_in_schema=False)
    async def shopify_auth(shop: str):
        """Endpoint initiating the OAuth process on a Shopify store"""
        return RedirectResponse(
            oauth_init_url(
                domain=store_domain(shop=shop),
                is_login=False,
                requested_scopes=app_scopes,
                callback_domain=public_domain,
                callback_path=callback_path,
                jwt_key=private_key,
                api_key=api_key,
            )
        )

    @router.get(callback_path, include_in_schema=False)
    async def shopify_callback(request: Request, args: Callback = Depends(Callback)):
        """REST endpoint called by Shopify during the OAuth process for installation and login"""
        try:
            validate_callback(
                shop=args.shop,
                timestamp=args.timestamp,
                query_string=request.scope['query_string'],
                api_secret_key=api_secret_key,
            )
            oauthjwt: OAuthJWT = validate_oauthjwt(
                token=args.state, shop=args.shop, jwt_key=private_key
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f'Validation failed: {e}')

        # === If installation ===
        # Setup the login obj and redirect to oauth_redirect
        if not oauthjwt.is_login:
            try:
                # Get the offline token from Shopify
                offline_token = await get_token(
                    domain=args.shop,
                    code=args.code,
                    api_key=api_key,
                    api_secret_key=api_secret_key,
                    CustomToken=OfflineToken,
                    Response=OfflineTokenResponse,
                )

                await offline_token.save()

            except Exception as e:
                logger.exception(f'Could not retrieve offline token for shop {args.shop}')
                raise HTTPException(status_code=400, detail=str(e))

            if OnlineToken is None:
                return app_redirect(
                    store_domain=args.shop,
                    jwtoken=None,
                    jwt_key=private_key,
                    app_domain=public_domain,
                    app_handle=app_handle,
                )
            # Initiate the oauth loop for login
            return RedirectResponse(
                oauth_init_url(
                    domain=args.shop,
                    is_login=True,
                    requested_scopes=user_scopes,
                    callback_domain=public_domain,
                    callback_path=callback_path,
                    jwt_key=private_key,
                    api_key=api_key,
                )
            )

        # === If login ===
        # Get the online token from Shopify
        if OnlineToken:
            online_token = await get_token(
                domain=args.shop,
                code=args.code,
                api_key=api_key,
                api_secret_key=api_secret_key,
                CustomToken=OnlineToken,
                Response=OnlineTokenResponse,
            )

            await online_token.save()

            # Await if the provided function is async
            jwtoken = None

            # Redirect to the app in Shopify admin
            return app_redirect(
                store_domain=args.shop,
                jwtoken=jwtoken,
                jwt_key=private_key,
                app_domain=public_domain,
                app_handle=app_handle,
            )

    return router
