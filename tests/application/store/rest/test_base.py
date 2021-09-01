from time import monotonic
from unittest.mock import AsyncMock

import pytest

from spylib.exceptions import ShopifyCallInvalidError
from spylib.store import Store

from ..shared import MockHTTPResponse


@pytest.mark.asyncio
async def test_store_rest_happypath(mocker):
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
async def test_store_rest_badrequest(mocker):
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


params = [
    pytest.param(0, 1000, 79, id='Last call hit rate limit, long time ago'),
    pytest.param(0, 20, 79, id='Last call hit rate limit, 20s ago'),
    pytest.param(0, 10, 39, id='Last call hit rate limit, 10s ago'),
    # Wait 1 second to get 4 then use 1 so 3
    pytest.param(0, 0, 3, id='Last call that hit rate limit just happened'),
]


@pytest.mark.parametrize('init_tokens, time_passed, expected_tokens', params)
@pytest.mark.asyncio
async def test_store_rest_ratetokens(init_tokens, time_passed, expected_tokens, mocker):
    store = Store(store_name='test-store')
    await store.add_offline_token(token='Te5tM3')

    # Simulate that there is only 2 calls available before hitting the rate limit.
    # If we set this to zero, then the code will wait 1 sec which is not great to keep the tests
    # fast
    store.rest_bucket = init_tokens
    store.updated_at = monotonic() - time_passed  # A looooong time ago

    shopify_request_mock = mocker.patch(
        'httpx.AsyncClient.request',
        new_callable=AsyncMock,
        return_value=MockHTTPResponse(status_code=200, jsondata={'success': True}),
    )
    await store.execute_rest_offline(
        goodstatus=200, debug='Test failed', endpoint='/test.json', method='get'
    )

    shopify_request_mock.assert_called_once()

    assert store.rest_bucket == expected_tokens
