import pytest

from spylib.utils.webhook import (
    WebhookSubscriptionCreate,
    WebhookSubscriptionInput,
    generate_query,
    generate_variables,
)


@pytest.mark.parametrize(
    'webhook_create,webhook_input, operation_name, operation_input',
    [
        (
            WebhookSubscriptionCreate.HTTP,
            WebhookSubscriptionInput.HTTP,
            'webhookSubscriptionCreate',
            'WebhookSubscriptionInput!',
        ),
        (
            WebhookSubscriptionCreate.EVENT_BRIDGE,
            WebhookSubscriptionInput.EVENT_BRIDGE,
            'eventBridgeWebhookSubscriptionCreate',
            'EventBridgeWebhookSubscriptionInput!',
        ),
        (
            WebhookSubscriptionCreate.PUBSUB,
            WebhookSubscriptionInput.PUBSUB,
            'pubSubWebhookSubscriptionCreate',
            'PubSubWebhookSubscriptionInput!',
        ),
    ],
    ids=['http', 'event_bridge', 'pubsub'],
)
def test_generate_query(webhook_create, webhook_input, operation_name, operation_input):
    query_generated = generate_query(
        webhook_subscription_create=webhook_create, webhook_subscription_input=webhook_input
    )
    query_expected = f'''
    mutation {operation_name}($topic: WebhookSubscriptionTopic!,
                                        $webhookSubscription: {operation_input}) {{
        {operation_name}(topic: $topic, webhookSubscription: $webhookSubscription) {{
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
    assert query_generated == query_expected


@pytest.mark.parametrize(
    'topic,callback_url',
    [
        ('ORDERS_CREATE', 'https://some_example.com/endpoint'),
    ],
    ids=['http'],
)
def test_generate_variables_http_webhook(topic, callback_url):
    variables_generated = generate_variables(topic=topic, callback_url=callback_url)
    variables_expected = {
        'topic': topic,
        'webhookSubscription': {
            'format': 'JSON',
            'includeFields': None,
            'metafieldNamespaces': None,
            'privateMetafieldNamespaces': None,
            'callback_url': callback_url,
        },
    }
    assert variables_generated == variables_expected


@pytest.mark.parametrize(
    'topic,arn',
    [
        ('ORDERS_CREATE', 'ARN'),
    ],
    ids=['arn'],
)
def test_generate_variables_event_bridge_webhook(topic, arn):
    variables_generated = generate_variables(topic=topic, arn=arn)
    variables_expected = {
        'topic': topic,
        'webhookSubscription': {
            'format': 'JSON',
            'includeFields': None,
            'metafieldNamespaces': None,
            'privateMetafieldNamespaces': None,
            'arn': arn,
        },
    }
    assert variables_generated == variables_expected


@pytest.mark.parametrize(
    'topic,pubsub_project,pubsub_topic',
    [
        ('ORDERS_CREATE', 'PROJECT', 'TOPIC'),
    ],
    ids=['pubsub'],
)
def test_generate_variables_pubsub_webhook(topic, pubsub_project, pubsub_topic):
    variables_generated = generate_variables(
        topic=topic, pubsub_project=pubsub_project, pubsub_topic=pubsub_topic
    )
    variables_expected = {
        'topic': topic,
        'webhookSubscription': {
            'format': 'JSON',
            'includeFields': None,
            'metafieldNamespaces': None,
            'privateMetafieldNamespaces': None,
            'pubsub_project': pubsub_project,
            'pubsub_topic': pubsub_topic,
        },
    }
    assert variables_generated == variables_expected
