from enum import Enum
from pathlib import Path

from pydantic import BaseModel

from spylib.hmac import validate

WEBHOOK_CREATE_GQL = Path('./spylib/webhook.graphql').read_text()


class WebhookTopic(Enum):
    ORDERS_CREATE = 'ORDERS_CREATE'


class WebhookResponse(BaseModel):
    id: str


class WebhookCreate(Enum):
    HTTP = 'webhookSubscriptionCreate'
    EVENT_BRIDGE = 'eventBridgeWebhookSubscriptionCreate'
    PUB_SUB = 'pubSubWebhookSubscriptionCreate'


def is_valid(data: str, hmac_header: str, api_secret_key: str) -> bool:
    try:
        validate(secret=api_secret_key, sent_hmac=hmac_header, message=data, use_base64=True)
    except ValueError:
        return False
    return True
