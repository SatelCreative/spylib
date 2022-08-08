WEBHOOK_CREATE_GQL = """
mutation webhookSubscriptionCreate($topic: WebhookSubscriptionTopic!, $webhookSubscription: WebhookSubscriptionInput!) {
  webhookSubscriptionCreate(topic: $topic, webhookSubscription: $webhookSubscription) {
    webhookSubscription {
      ...WebhookSubscription
    }
    userErrors {
      field
      message
    }
  }
}

mutation pubSubWebhookSubscriptionCreate($topic: WebhookSubscriptionTopic!, $webhookSubscription: PubSubWebhookSubscriptionInput!) {
  pubSubWebhookSubscriptionCreate(topic: $topic, webhookSubscription: $webhookSubscription) {
    webhookSubscription {
      ...WebhookSubscription
    }
    userErrors {
      field
      message
    }
  }
}

mutation eventBridgeWebhookSubscriptionCreate($topic: WebhookSubscriptionTopic!, $webhookSubscription: EventBridgeWebhookSubscriptionInput!) {
  eventBridgeWebhookSubscriptionCreate(topic: $topic, webhookSubscription: $webhookSubscription) {
    webhookSubscription {
      ...WebhookSubscription
    }
    userErrors {
      field
      message
    }
  }
}

fragment WebhookSubscription on WebhookSubscription {
  id
  topic
  format
  endpoint {
    __typename
    ... on WebhookHttpEndpoint {
      callbackUrl
    }
    ... on WebhookEventBridgeEndpoint {
      arn
    }
    ... on WebhookPubSubEndpoint {
      pubSubProject
      pubSubTopic
    }
  }
}
"""
