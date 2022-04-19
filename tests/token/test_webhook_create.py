from unittest.mock import AsyncMock

import pytest

from spylib import WebhookResponse, WebhookTopic
from spylib.exceptions import ShopifyGQLUserError

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
                },
                'userErrors': [],
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


@pytest.mark.asyncio
async def test_store_http_webhook_create_usererrors(mocker):
    token = await OfflineToken.load(store_name=test_information.store_name)

    gql_response = {
        'data': {
            'webhookSubscriptionCreate': {
                'webhookSubscription': None,
                'userErrors': [
                    {
                        'field': ['webhookSubscription', 'callbackUrl'],
                        'message': 'Address for this topic has already been taken',
                    }
                ],
            }
        }
    }

    shopify_request_mock = mocker.patch(
        'httpx.AsyncClient.request',
        new_callable=AsyncMock,
        return_value=MockHTTPResponse(status_code=200, jsondata=gql_response),
    )
    with pytest.raises(ShopifyGQLUserError):
        await token.create_http_webhook(
            topic=WebhookTopic.ORDERS_CREATE,
            callback_url='https://example.org/endpoint',
            include_fields=["id", "note"],
        )

    assert shopify_request_mock.call_count == 1


@pytest.mark.asyncio
async def test_store_http_webhook_create_invalidtopic(mocker):
    token = await OfflineToken.load(store_name=test_information.store_name)

    gql_response = {
        'errors': [
            {
                'message': 'Variable $topic of type WebhookSubscriptionTopic! '
                'was provided invalid value',
                'locations': [{'line': 1, 'column': 36}],
            }
        ]
    }

    shopify_request_mock = mocker.patch(
        'httpx.AsyncClient.request',
        new_callable=AsyncMock,
        return_value=MockHTTPResponse(status_code=200, jsondata=gql_response),
    )
    with pytest.raises(ValueError):
        await token.create_http_webhook(
            topic='invalid topic',
            callback_url='https://example.org/endpoint',
            include_fields=["id", "note"],
        )

    assert shopify_request_mock.call_count == 1
