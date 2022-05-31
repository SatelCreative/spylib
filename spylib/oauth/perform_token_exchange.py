from typing import List, Union

from httpx import AsyncClient, codes
from pydantic import BaseModel, validator


def parse_scope(scope: str) -> List[str]:
    return scope.split(',')


# Docstrings would be fully completed
# Types would potentially be moved to .types


class OfflineTokenResponse(BaseModel):   # I don't love this naming
    """
    [Read more about Offline access](https://shopify.dev/apps/auth/oauth/access-modes#offline-access)
    """

    access_token: str
    """
    An API access token that can be used to access the shop’s data as long as your app is installed. Your app should store the token somewhere to make authenticated requests for a shop’s data.
    """
    scope: List[str]
    """
    The list of access scopes that were granted to your app and are associated with the access token.
    """

    _normalize_scope = validator('scope', allow_reuse=True, pre=True)(parse_scope)


class AssociatedUser(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    email_verified: bool
    account_owner: bool
    locale: str
    collaborator: bool


class OnlineTokenResponse(BaseModel):
    """
    [Read more about Online access](https://shopify.dev/apps/auth/oauth/access-modes#online-access)
    """

    access_token: str
    """
    
    """
    scope: List[str]
    """
    The list of access scopes that were requested to be associated with the access token.
    """

    _normalize_scope = validator('scope', allow_reuse=True, pre=True)(parse_scope)

    expires_in: int
    associated_user_scope: List[str]

    _normalize_associated_user_scope = validator(
        'associated_user_scope', allow_reuse=True, pre=True
    )(parse_scope)

    """
    The list of access scopes that were granted to associated with the access token.
    """
    associated_user: AssociatedUser


async def perform_token_exchange(
    *,
    code: str,
    shop: str,
    api_key: str,
    api_secret_key: str,
) -> Union[OnlineTokenResponse, OfflineTokenResponse]:
    """_summary_

    Args:
        code (str): _description_
        shop (str): _description_
        api_key (str): _description_
        api_secret_key (str): _description_

    Raises:
        Exception: _description_

    Returns:
        Union[OnlineTokenResponse, OfflineTokenResponse]: _description_
    """

    async with AsyncClient(base_url=f'https://{shop}') as client:
        response = await client.post(
            url='/admin/oauth/access_token',
            json={
                'code': code,
                'client_id': api_key,
                'client_secret': api_secret_key,
            },
        )

    if response.status_code != codes.OK:
        message = (
            f'Shopify rejected token exchange. Shop: "{shop}". Status "{response.status_code}"'
        )
        raise Exception(message)   # Not sure what the convention is here

    raw_response_body = response.json()
    is_online_token = hasattr(raw_response_body, 'associated_user')

    if is_online_token:
        return OnlineTokenResponse.parse_obj(raw_response_body)

    return OfflineTokenResponse.parse_obj(raw_response_body)
