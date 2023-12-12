from typing import List

from ..utils import domain_to_storename, get_unique_id
from .tokens import OAuthJWT


def oauth_init_url(
    domain: str,
    requested_scopes: List[str],
    callback_domain: str,
    callback_path: str,
    path_prefix: str,
    is_login: bool,
    jwt_key: str,
    api_key: str,
) -> str:
    """Create the URL and the parameters needed to start the oauth process to install an app or to log a user in.

    Args
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
    redirect_uri = f'https://{callback_domain}{path_prefix}{callback_path}'
    oauthjwt = OAuthJWT(
        is_login=is_login, storename=domain_to_storename(domain), nonce=get_unique_id()
    )
    oauth_token = oauthjwt.encode_token(key=jwt_key)
    access_mode = 'per-user' if is_login else ''

    return (
        f'https://{domain}/admin/oauth/authorize?client_id={api_key}&'
        f'scope={scopes}&redirect_uri={redirect_uri}&state={oauth_token}&'
        f'grant_options[]={access_mode}'
    )


def app_redirect(
    store_domain: str,
    app_domain: str,
    app_api_key: str,
) -> str:
    return f'https://{store_domain}/admin/apps/{app_api_key}'
