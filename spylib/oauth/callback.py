from inspect import isawaitable
from typing import Awaitable, Callable, Optional

from .exchange_token import exchange_offline_token, exchange_online_token
from .models import OfflineTokenModel, OnlineTokenModel
from .tokens import OAuthJWT
from .validations import validate_callback, validate_oauthjwt


async def process_callback(
    shop: str,
    timestamp: int,
    query_string: str,
    api_secret_key: str,
    api_key: str,
    state: str,
    private_key: str,
    code: str,
    post_install: Callable[[str, OfflineTokenModel], Optional[Awaitable]],
    post_login: Optional[Callable[[str, OnlineTokenModel], Optional[Awaitable]]],
) -> OAuthJWT:
    validate_callback(
        shop=shop,
        timestamp=timestamp,
        query_string=query_string,
        api_secret_key=api_secret_key,
    )
    oauthjwt: OAuthJWT = validate_oauthjwt(token=state, shop=shop, jwt_key=private_key)

    if not oauthjwt.is_login:
        await process_install_callback(
            oauthjwt=oauthjwt,
            shop=shop,
            code=code,
            api_key=api_key,
            api_secret_key=api_secret_key,
            post_install=post_install,
        )
        return oauthjwt

    await process_login_callback(
        oauthjwt=oauthjwt,
        shop=shop,
        code=code,
        api_key=api_key,
        api_secret_key=api_secret_key,
        post_login=post_login,
    )

    return oauthjwt


async def process_install_callback(
    oauthjwt: OAuthJWT,
    shop: str,
    code: str,
    api_key: str,
    api_secret_key: str,
    post_install: Callable[[str, OfflineTokenModel], Optional[Awaitable]],
):
    offline_token = await exchange_offline_token(
        shop=shop,
        code=code,
        api_key=api_key,
        api_secret_key=api_secret_key,
    )

    # Await if the provided function is async
    if isawaitable(pi_return := post_install(oauthjwt.storename, offline_token)):
        await pi_return  # type: ignore


async def process_login_callback(
    oauthjwt: OAuthJWT,
    shop: str,
    code: str,
    api_key: str,
    api_secret_key: str,
    post_login: Optional[Callable[[str, OnlineTokenModel], Optional[Awaitable]]],
):
    # Get the online token from Shopify
    online_token = await exchange_online_token(
        shop=shop,
        code=code,
        api_key=api_key,
        api_secret_key=api_secret_key,
    )

    # Await if the provided function is async
    if post_login:
        if isawaitable(pl_return := post_login(oauthjwt.storename, online_token)):
            await pl_return  # type: ignore
