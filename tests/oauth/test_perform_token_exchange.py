import pytest
from respx import MockRouter

from spylib.oauth import (
    OfflineTokenResponse,
    OnlineTokenResponse,
    perform_token_exchange,
)

perform_token_exchange_params = [
    (
        dict(
            access_token='offline-token',
            scope='read_products',
        ),
        OfflineTokenResponse,
    ),
    (
        dict(
            access_token='online-token',
            scope='write_products',
            expires_in=86399,
            associated_user_scope='read_products',
            associated_user=dict(
                id=902541635,
                first_name='John',
                last_name='Smith',
                email='john@example.com',
                email_verified=True,
                account_owner=True,
                locale='en',
                collaborator=False,
            ),
        ),
        OnlineTokenResponse,
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize('token_dict,token_model', perform_token_exchange_params)
async def test_perform_token_exchange(respx_mock: MockRouter, token_dict, token_model):
    shop = 'example.myshopify.com'
    code = 'code'
    api_key = 'api-key'
    api_secret_key = 'api-secret-key'

    respx_mock.post(
        f'https://{shop}/admin/oauth/access_token',
        json__code=code,
        json__client_id=api_key,
        json__client_secret=api_secret_key,
    ).respond(
        json=token_dict,
    )

    result = await perform_token_exchange(
        shop=shop,
        code=code,
        api_key=api_key,
        api_secret_key=api_secret_key,
    )

    assert result == token_model.parse_obj(token_dict)
