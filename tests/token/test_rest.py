from time import monotonic
from unittest.mock import AsyncMock

import pytest

from spylib.exceptions import ShopifyCallInvalidError
from spylib.utils.rest import GET, POST

from ..token_classes import MockHTTPResponse, OfflineToken, test_information


@pytest.mark.asyncio
async def test_store_rest_happypath(mocker):
    token = await OfflineToken.load(store_name=test_information.store_name)

    shopify_request_mock = mocker.patch(
        'httpx.AsyncClient.request',
        new_callable=AsyncMock,
        return_value=MockHTTPResponse(status_code=200, jsondata={'success': True}),
    )

    jsondata = await token.execute_rest(
        request=GET,
        endpoint='/test.json',
        debug='Test failed',
    )

    shopify_request_mock.assert_called_once()

    assert jsondata == {'success': True}

    # 80 from assuming Shopify plus then 1 used just now.
    assert token.rest_bucket == 79


@pytest.mark.asyncio
async def test_store_rest_badrequest(mocker):
    token = await OfflineToken.load(store_name=test_information.store_name)

    shopify_request_mock = mocker.patch(
        'httpx.AsyncClient.request',
        new_callable=AsyncMock,
        return_value=MockHTTPResponse(
            status_code=422, jsondata={'errors': {'title': ["can't be blank"]}}
        ),
    )

    with pytest.raises(ShopifyCallInvalidError):
        await token.execute_rest(
            request=POST,
            endpoint='/products.json',
            json={'product': {'body_html': 'A mystery!'}},
            debug='Test failed',
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
async def test_store_rest_ratetokens(
    init_tokens,
    time_passed,
    expected_tokens,
    mocker,
):
    token = await OfflineToken.load(store_name=test_information.store_name)

    # Simulate that there is only 2 calls available before hitting the rate limit.
    # If we set this to zero, then the code will wait 1 sec which is not great to keep the tests
    # fast
    token.rest_bucket = init_tokens
    token.updated_at = monotonic() - time_passed  # A looooong time ago

    shopify_request_mock = mocker.patch(
        'httpx.AsyncClient.request',
        new_callable=AsyncMock,
        return_value=MockHTTPResponse(status_code=200, jsondata={'success': True}),
    )
    await token.execute_rest(
        request=GET,
        endpoint='/test.json',
        debug='Test failed',
    )

    shopify_request_mock.assert_called_once()

    assert token.rest_bucket == expected_tokens
