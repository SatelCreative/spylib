from enum import Enum
from pathlib import Path

from pydantic import BaseModel

WEBHOOK_CREATE_GQL = Path('./spylib/webhook.graphql').read_text()


class WebhookTopic(Enum):
    ORDERS_CREATE = 'ORDERS_CREATE'


class WebhookResponse(BaseModel):
    id: str


class WebhookCreate(Enum):
    HTTP = 'webhookSubscriptionCreate'
    EVENT_BRIDGE = 'eventBridgeWebhookSubscriptionCreate'
    PUB_SUB = 'pubSubWebhookSubscriptionCreate'
