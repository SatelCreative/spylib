import json

import pytest
from pytest_httpx import HTTPXMock

shop = 'example.myshopify.com'
online_token_response = dict(
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
)

# Would be parametrized
@pytest.mark.asyncio
async def test_perform_token_exchange(httpx_mock: HTTPXMock):
    # Would move this functionality into a fixture
    # I'd love a nicer way to do this in fact, features needed:
    # throw if not called, assert on body, mock response
    httpx_mock.add_response(
        url=f'https://{shop}/admin/oauth/access_token',
        method='POST',
        json=online_token_response,
        # This is not great - key order matters since we are comparing a byte stream
        match_content=bytes(
            json.dumps(
                {
                    'code': 'code',
                    'client_id': 'api-key',
                    'client_secret': 'api-secret-key',
                }
            ),
            'utf-8',
        ),
    )

    from spylib.oauth import perform_token_exchange

    await perform_token_exchange(
        code='code',
        shop=shop,
        api_key='api-key',
        api_secret_key='api-secret-key',
    )
