from dataclasses import dataclass
from typing import Awaitable, Callable, List, Optional

from spylib.exceptions import FastAPIImportError

try:
    from fastapi import APIRouter, Depends, HTTPException, Query  # type: ignore
except ImportError as e:
    raise FastAPIImportError(
        'The oauth router is a fastapi router and fastapi is not installed. '
        'Run `pip install spylib[fastapi]` to be able to use the oauth router.'
    ) from e

from starlette.requests import Request
from starlette.responses import RedirectResponse

from ..utils import store_domain
from .callback import process_callback
from .models import OfflineTokenModel, OnlineTokenModel
from .redirects import app_redirect, oauth_init_url


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
    api_key: str,
    api_secret_key: str,
    post_install: Callable[[str, OfflineTokenModel], Optional[Awaitable]],
    post_login: Optional[Callable[[str, OnlineTokenModel], Optional[Awaitable]]] = None,
    install_init_path='/shopify/auth',
    callback_path='/callback',
    path_prefix: str = '',
) -> APIRouter:
    router = APIRouter()

    if not install_init_path.startswith('/'):
        raise ValueError('The install_init_path argument must start with "/"')
    if not callback_path.startswith('/'):
        raise ValueError('The callback_path argument must start with "/"')
    if path_prefix and not path_prefix.startswith('/'):
        raise ValueError('The path_prefix argument must start with "/"')

    @router.get(install_init_path, include_in_schema=False)
    async def shopify_auth(shop: str):
        """Endpoint initiating the OAuth process on a Shopify store."""
        return RedirectResponse(
            oauth_init_url(
                domain=store_domain(shop=shop),
                is_login=False,
                requested_scopes=app_scopes,
                callback_domain=public_domain,
                callback_path=callback_path,
                path_prefix=path_prefix,
                jwt_key=private_key,
                api_key=api_key,
            )
        )

    @router.get(callback_path, include_in_schema=False)
    async def shopify_callback(request: Request, shop: str, args: Callback = Depends(Callback)):
        """REST endpoint called by Shopify during the OAuth process for installation and login."""
        try:
            oauthjwt = await process_callback(
                shop=args.shop,
                timestamp=args.timestamp,
                query_string=request.scope['query_string'],
                api_secret_key=api_secret_key,
                api_key=api_key,
                state=args.state,
                private_key=private_key,
                code=args.code,
                post_install=post_install,
                post_login=post_login,
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f'Validation failed: {e}')

        # === If installation ===
        # Setup the login obj and redirect to oauth_redirect
        if not oauthjwt.is_login:
            if post_login is None:
                return RedirectResponse(
                    app_redirect(
                        store_domain=args.shop,
                        app_domain=public_domain,
                        app_api_key=api_key,
                    )
                )
            # Initiate the oauth loop for login
            return RedirectResponse(
                oauth_init_url(
                    domain=args.shop,
                    is_login=True,
                    requested_scopes=user_scopes,
                    callback_domain=public_domain,
                    callback_path=callback_path,
                    path_prefix=path_prefix,
                    jwt_key=private_key,
                    api_key=api_key,
                )
            )

        # Redirect to the app in Shopify admin
        return RedirectResponse(
            app_redirect(
                store_domain=args.shop,
                app_domain=public_domain,
                app_api_key=api_key,
            )
        )

    return router
