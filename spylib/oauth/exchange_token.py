from typing import Union

from httpx import AsyncClient, codes

from .models import OfflineTokenModel, OnlineTokenModel


async def exchange_token(
    *,
    shop: str,
    code: str,
    api_key: str,
    api_secret_key: str,
) -> Union[OnlineTokenModel, OfflineTokenModel]:
    """[Exchanges the temporary authorization code with Shopify for a token](https://shopify.dev/apps/auth/oauth/getting-started#step-5-get-a-permanent-access-token).

    [All prior security checks must already have been completed.](https://shopify.dev/apps/auth/oauth/getting-started#step-4-confirm-installation)

    Args:
        shop (str): The name of the merchant's shop. `example.myshopify.com`
        code (str): The authorization code provided in the redirect.
        api_key (str): The API key for the app, as defined in the Shopify Partner Dashboard.
        api_secret_key (str): The API secret key for the app, as defined in the Shopify Partner Dashboard.

    Returns:
        Union[OnlineTokenModel, OfflineTokenModel]: Validated token response. Will differ [depending upon the requested access mode.](https://shopify.dev/apps/auth/oauth/access-modes)
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
            f'Shopify rejected token exchange. Shop: "{shop}". Status: "{response.status_code}".'
        )
        raise Exception(message)  # Not sure what the convention is here

    raw_response_body = response.json()
    is_online_token = 'associated_user' in raw_response_body

    if is_online_token:
        return OnlineTokenModel.model_validate(raw_response_body)

    return OfflineTokenModel.model_validate(raw_response_body)


async def exchange_offline_token(
    *,
    shop: str,
    code: str,
    api_key: str,
    api_secret_key: str,
) -> OfflineTokenModel:
    """[Exchanges the temporary authorization code with Shopify for an offline token](https://shopify.dev/apps/auth/oauth/getting-started#step-5-get-a-permanent-access-token).

    Can be used instead of `exchange_token` when you know by some mechanism it will only be an offline token.

    [All prior security checks must already have been completed.](https://shopify.dev/apps/auth/oauth/getting-started#step-4-confirm-installation)

    Args:
        shop (str): The name of the merchant's shop. `example.myshopify.com`
        code (str): The authorization code provided in the redirect.
        api_key (str): The API key for the app, as defined in the Shopify Partner Dashboard.
        api_secret_key (str): The API secret key for the app, as defined in the Shopify Partner Dashboard.

    Returns:
        OfflineTokenModel: [Validated offline token response.]https://shopify.dev/apps/auth/oauth/access-modes#offline-access
    """
    token = await exchange_token(
        shop=shop, code=code, api_key=api_key, api_secret_key=api_secret_key
    )

    assert isinstance(token, OfflineTokenModel)

    return token


async def exchange_online_token(
    *,
    shop: str,
    code: str,
    api_key: str,
    api_secret_key: str,
) -> OnlineTokenModel:
    """[Exchanges the temporary authorization code with Shopify for an online token](https://shopify.dev/apps/auth/oauth/getting-started#step-5-get-a-permanent-access-token).

    Can be used instead of `exchange_token` when you know by some mechanism it will only be an online token.

    [All prior security checks must already have been completed.](https://shopify.dev/apps/auth/oauth/getting-started#step-4-confirm-installation)

    Args:
        shop (str): The name of the merchant's shop. `example.myshopify.com`
        code (str): The authorization code provided in the redirect.
        api_key (str): The API key for the app, as defined in the Shopify Partner Dashboard.
        api_secret_key (str): The API secret key for the app, as defined in the Shopify Partner Dashboard.

    Returns:
        OnlineTokenModel: [Validated online token response.]https://shopify.dev/apps/auth/oauth/access-modes#online-access
    """
    token = await exchange_token(
        shop=shop, code=code, api_key=api_key, api_secret_key=api_secret_key
    )

    assert isinstance(token, OnlineTokenModel)

    return token
