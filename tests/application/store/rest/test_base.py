from unittest.mock import AsyncMock

import pytest

from spylib.exceptions import ShopifyCallInvalidError
from spylib.store import Store
from spylib.token import AssociatedUser

from ..shared import MockHTTPResponse


@pytest.mark.asyncio
async def test_rest_offline(mocker):
    store = Store(store_name='test-store')
    await store.add_offline_token(token='Te5tM3')

    shopify_request_mock = mocker.patch(
        'httpx.AsyncClient.request',
        new_callable=AsyncMock,
        return_value=MockHTTPResponse(status_code=200, jsondata={'success': True}),
    )

    jsondata = await store.execute_rest_offline(
        goodstatus=200, debug='Test failed', endpoint='/test.json', method='get'
    )

    shopify_request_mock.assert_called_once()

    assert jsondata == {'success': True}

    # 80 from assuming Shopify plus then 1 used just now.
    assert store.rest_bucket == 79


@pytest.mark.asyncio
async def test_rest_online(mocker):
    """
    Tests the rest API call using an online token instead of an offline token.
    Since this is a wrapper around the original function we only need to test
    the ability to get the token and make the call.
    """
    user = AssociatedUser(
        **{
            "id": 902541635,
            "first_name": "John",
            "last_name": "Smith",
            "email": "john@example.com",
            "email_verified": True,
            "account_owner": True,
            "locale": "en",
            "collaborator": False,
        }
    )

    store = Store(store_name='test-store')
    await store.add_online_token(
        token='Te5tM3',
        associated_user=user,
        expires_in=1000,
    )

    shopify_request_mock = mocker.patch(
        'httpx.AsyncClient.request',
        new_callable=AsyncMock,
        return_value=MockHTTPResponse(status_code=200, jsondata={'success': True}),
    )

    jsondata = await store.execute_rest_online(
        user_id=user.id,
        goodstatus=200,
        debug='Test failed',
        endpoint='/test.json',
        method='get',
    )

    shopify_request_mock.assert_called_once()

    assert jsondata == {'success': True}

    # 80 from assuming Shopify plus then 1 used just now.
    assert store.rest_bucket == 79


@pytest.mark.asyncio
async def test_rest_badrequest(mocker):
    store = Store(store_name='test-store')
    await store.add_offline_token(token='Te5tM3')

    shopify_request_mock = mocker.patch(
        'httpx.AsyncClient.request',
        new_callable=AsyncMock,
        return_value=MockHTTPResponse(
            status_code=422, jsondata={'errors': {'title': ["can't be blank"]}}
        ),
    )

    with pytest.raises(ShopifyCallInvalidError):
        await store.execute_rest_offline(
            goodstatus=201,
            debug='Test failed',
            endpoint='/products.json',
            method='post',
            json={'product': {'body_html': 'A mystery!'}},
        )

    shopify_request_mock.assert_called_once()
