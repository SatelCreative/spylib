from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel


class WebhookTopic(Enum):
    ORDERS_CREATE = 'ORDERS_CREATE'


class WebhookResponse(BaseModel):
    id: str


class WebhookSubscriptionCreate(Enum):
    HTTP = 'webhookSubscriptionCreate'
    EVENT_BRIDGE = 'eventBridgeWebhookSubscriptionCreate'
    PUBSUB = 'pubSubWebhookSubscriptionUpdate'


class WebhookSubscriptionInput(Enum):
    HTTP = 'WebhookSubscriptionInput!'
    EVENT_BRIDGE = 'EventBridgeWebhookSubscriptionInput!'
    PUBSUB = 'PubSubWebhookSubscriptionInput!'


def generate_query(
    webhook_subscription_create: WebhookSubscriptionCreate,
    webhook_subscription_input: WebhookSubscriptionInput,
) -> str:
    """Generate the webhook creation graphql query"""
    operation = webhook_subscription_create.value
    input_type = webhook_subscription_input.value

    query = f'''
    mutation {operation}($topic: WebhookSubscriptionTopic!,
                                        $webhookSubscription: {input_type}) {{
        {operation}(topic: $topic, webhookSubscription: $webhookSubscription) {{
            webhookSubscription {{
            id
            topic
            format
            endpoint {{
                __typename
                ... on WebhookHttpEndpoint {{
                callbackUrl
                }}
                ... on WebhookEventBridgeEndpoint {{
                arn
                }}
                ... on WebhookPubSubEndpoint {{
                pubSubProject
                pubSubTopic
                }}
              }}
            }}
            userErrors {{
                field
                message
              }}
            }}
        }}
    '''
    return query


def generate_variables(
    topic: Union[WebhookTopic, str],
    include_fields: Optional[List[str]] = None,
    metafield_namespaces: Optional[List[str]] = None,
    private_metafield_namespaces: Optional[List[str]] = None,
    **endpoint_kwargs,
) -> dict:
    variables = {
        'topic': topic.value if isinstance(topic, WebhookTopic) else topic,
        'webhookSubscription': {
            'format': 'JSON',
            'includeFields': include_fields,
            'metafieldNamespaces': metafield_namespaces,
            'privateMetafieldNamespaces': private_metafield_namespaces,
            **endpoint_kwargs,
        },
    }
    return variables
