from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel

from spylib.admin_api import OfflineTokenABC
from spylib.constants import UTF8ENCODING
from spylib.exceptions import ShopifyGQLError, ShopifyGQLUserError
from spylib.hmac import validate as validate_hmac
from spylib.webhook.graphql_queries import WEBHOOK_CREATE_GQL


class WebhookTopic(Enum):
    ORDERS_CREATE = 'ORDERS_CREATE'


class WebhookResponse(BaseModel):
    id: str


class WebhookCreate(Enum):
    HTTP = 'webhookSubscriptionCreate'
    EVENT_BRIDGE = 'eventBridgeWebhookSubscriptionCreate'
    PUB_SUB = 'pubSubWebhookSubscriptionCreate'


def validate(data: Union[str, bytes], hmac_header: str, api_secret_key: str) -> bool:
    data_str: str
    if isinstance(data, bytes):
        data_str = data.decode(UTF8ENCODING)
    else:
        data_str = data
    try:
        validate_hmac(
            secret=api_secret_key, sent_hmac=hmac_header, message=data_str, use_base64=True
        )
    except ValueError:
        return False
    return True


async def create_http(
    offline_token: OfflineTokenABC,
    topic: Union[WebhookTopic, str],
    callback_url: str,
    include_fields: Optional[List[str]] = None,
    metafield_namespaces: Optional[List[str]] = None,
    filter: Optional[str] = None,
) -> WebhookResponse:
    """Creates a HTTP webhook subscription.

    Uses graphql to subscribe to a webhook and associate it with an HTTP endpoint.
    """
    variables = {
        'topic': topic.value if isinstance(topic, WebhookTopic) else topic,
        'webhookSubscription': {
            'format': 'JSON',
            'includeFields': include_fields,
            'metafieldNamespaces': metafield_namespaces,
            'callbackUrl': callback_url,
            'filter': filter,
        },
    }
    res = await offline_token.execute_gql(
        query=WEBHOOK_CREATE_GQL,
        operation_name=WebhookCreate.HTTP.value,
        variables=variables,
    )
    webhook_create = res.get(WebhookCreate.HTTP.value, None)
    if webhook_create and webhook_create.get('userErrors'):
        raise ShopifyGQLUserError(res)
    if not webhook_create:
        raise ShopifyGQLError(res)
    return WebhookResponse(id=webhook_create['webhookSubscription']['id'])


async def create_event_bridge(
    offline_token: OfflineTokenABC,
    topic: Union[WebhookTopic, str],
    arn: str,
    include_fields: Optional[List[str]] = None,
    metafield_namespaces: Optional[List[str]] = None,
    filter: Optional[str] = None,
) -> WebhookResponse:
    """Creates an Amazon EventBridge webhook subscription.

    Uses graphql to subscribe to a webhook and associated it with
    and AWS Event Bridge with ARN (Amazon Resource Name)
    """
    variables = {
        'topic': topic.value if isinstance(topic, WebhookTopic) else topic,
        'webhookSubscription': {
            'format': 'JSON',
            'includeFields': include_fields,
            'metafieldNamespaces': metafield_namespaces,
            'arn': arn,
            'filter': filter,
        },
    }
    res = await offline_token.execute_gql(
        query=WEBHOOK_CREATE_GQL,
        operation_name=WebhookCreate.EVENT_BRIDGE.value,
        variables=variables,
    )
    webhook_create = res.get(WebhookCreate.EVENT_BRIDGE.value, None)
    if webhook_create and webhook_create.get('userErrors'):
        raise ShopifyGQLUserError(res)
    if not webhook_create:
        raise ShopifyGQLError(res)
    return WebhookResponse(id=webhook_create['webhookSubscription']['id'])


async def create_pub_sub(
    offline_token: OfflineTokenABC,
    topic: Union[WebhookTopic, str],
    pub_sub_project: str,
    pub_sub_topic: str,
    include_fields: Optional[List[str]] = None,
    metafield_namespaces: Optional[List[str]] = None,
    filter: Optional[str] = None,
) -> WebhookResponse:
    """Creates a Google Cloud Pub/Sub webhook subscription.

    Uses graphql to subscribe to a webhook and associate it with a Google PubSub endpoint
    """
    variables = {
        'topic': topic.value if isinstance(topic, WebhookTopic) else topic,
        'webhookSubscription': {
            'format': 'JSON',
            'includeFields': include_fields,
            'metafieldNamespaces': metafield_namespaces,
            'pubSubProject': pub_sub_project,
            'pubSubTopic': pub_sub_topic,
            'filter': filter,
        },
    }
    res = await offline_token.execute_gql(
        query=WEBHOOK_CREATE_GQL,
        operation_name=WebhookCreate.PUB_SUB.value,
        variables=variables,
    )
    webhook_create = res.get(WebhookCreate.PUB_SUB.value, None)
    if webhook_create and webhook_create.get('userErrors'):
        raise ShopifyGQLUserError(res)
    if not webhook_create:
        raise ShopifyGQLError(res)
    return WebhookResponse(id=webhook_create['webhookSubscription']['id'])
