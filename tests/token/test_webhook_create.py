from unittest.mock import AsyncMock

import pytest

from spylib import WebhookResponse, WebhookTopic

from ..token_classes import MockHTTPResponse, OfflineToken, test_information


@pytest.mark.asyncio
async def test_store_http_webhook_create_happypath(mocker):
    token = await OfflineToken.load(store_name=test_information.store_name)

    webhook_id = 'gid://shopify/WebhookSubscription/7191874123'
    gql_response = {
        'data': {
            'webhookSubscriptionCreate': {
                'webhookSubscription': {
                    'id': webhook_id,
                    'topic': 'ORDERS_CREATE',
                    'format': 'JSON',
                    'includeFields': ['id', 'note'],
                    'endpoint': {
                        '__typename': 'WebhookHttpEndpoint',
                        'callbackUrl': 'https://example.org/endpoint',
                    },
                }
            }
        }
    }

    shopify_request_mock = mocker.patch(
        'httpx.AsyncClient.request',
        new_callable=AsyncMock,
        return_value=MockHTTPResponse(status_code=200, jsondata=gql_response),
    )

    res = await token.create_http_webhook(
        topic=WebhookTopic.ORDERS_CREATE,
        callback_url='https://example.org/endpoint',
        include_fields=["id", "note"],
    )

    shopify_request_mock.assert_called_once()

    assert res == WebhookResponse(id=webhook_id)
