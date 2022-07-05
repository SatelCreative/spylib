import pytest
from httpx import Response
from respx import MockRouter


@pytest.mark.asyncio
async def test_event_based_credential_leak(respx_mock: MockRouter):
    from spylib.admin_api import OfflineTokenABC
    from spylib.utils.rest import GET

    class OfflineToken(OfflineTokenABC):
        async def save(self):
            raise NotImplementedError()

        @classmethod
        async def load(cls, store_name: str):
            raise NotImplementedError()

    store_one = 'store_one'
    store_two = 'store_two'

    token_one = OfflineToken(
        store_name=store_one, access_token=f'secret_token_for_{store_one}', scope=[]
    )
    token_two = OfflineToken(
        store_name=store_two, access_token=f'secret_token_for_{store_two}', scope=[]
    )

    token_one_headers = []

    async def capture_request(request):
        token_one_headers.append(request.headers['X-Shopify-Access-Token'])

    token_one.client.event_hooks['request'] = [capture_request]

    respx_mock.get().mock(
        return_value=Response(200, json={}, headers={'X-Shopify-Shop-Api-Call-Limit': '10/20'})
    )

    await token_two.execute_rest(
        request=GET,
        endpoint='/test',
    )

    assert token_one_headers == []
