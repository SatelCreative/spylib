from typing import List, Optional

from starlette.responses import RedirectResponse

from ..utils import JWTBaseModel, domain_to_storename, get_unique_id
from .config import conf
from .tokens import OAuthJWT


def oauth_init_url(
    domain: str,
    requested_scopes: List[str],
    callback_domain: str,
    callback_path: str,
    is_login: bool,
    jwt_key: str,
) -> str:
    """
    Create the URL and the parameters needed to start the oauth process to install an app or to log
    a user in.

    Parameters
    ----------
    domain: Domain of the shopify store in the format "{storesubdomain}.myshopify.com"
    requested_scopes: List of scopes accessible to the app once installed.
        See https://shopify.dev/docs/admin-api/access-scopes
    callback_domain: Public domain Shopify will connect to during the oauth process
    is_login: Specify if the oauth is to install the app or a user logging in

    Returns
    -------
    URL with all needed parameters to trigger the oauth process
    """
    scopes = ','.join(requested_scopes)
    redirect_uri = f'https://{callback_domain}{callback_path}'
    oauthjwt = OAuthJWT(
        is_login=is_login, storename=domain_to_storename(domain), nonce=get_unique_id()
    )
    oauth_token = oauthjwt.encode_token(key=jwt_key)
    access_mode = 'per-user' if is_login else ''

    return (
        f'https://{domain}/admin/oauth/authorize?client_id={conf.api_key}&'
        f'scope={scopes}&redirect_uri={redirect_uri}&state={oauth_token}&'
        f'grant_options[]={access_mode}'
    )


def app_redirect(
    store_domain: str, app_domain: str, jwtoken: Optional[JWTBaseModel], jwt_key: str
) -> RedirectResponse:
    app_handle = conf.handle

    if jwtoken is None:
        return RedirectResponse(f'https://{store_domain}/admin/apps/{app_handle}')

    jwtarg, signature = jwtoken.encode_hp_s(key=jwt_key)
    redir = RedirectResponse(f'https://{store_domain}/admin/apps/{app_handle}?jwt={jwtarg}')

    # TODO set 'expires'
    redir.set_cookie(
        key=jwtoken.cookie_key,
        value=signature,
        domain=app_domain,
        httponly=True,
        secure=True,
    )

    return redir
