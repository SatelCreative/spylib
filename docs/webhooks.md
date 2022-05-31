# Webhooks

The [webhook](https://shopify.dev/apps/webhooks/configuration)
functionality can be used to register webhooks and validate that the webhook notifications are from Shopify

**Breaking Changes in version 0.6.0**: <br>
The param `is_base64` used in function `validate` from module `spylib.utils.hmac` is renamed to `use_base64`
to better convey the meaning of the parameter


**Breaking Changes in version 0.7.0**: <br>
The webhook features become available from `spylib.webhook` module as functions 
instead of from the `Token` class as methods. 

## Register Webhooks

You can easily register your endpoint to receive webhooks from Shopify using an admin API access token:
```python
from spylib import webhook

async def register_webhook_with_http_endpoint():
    # topics from https://shopify.dev/api/admin-graphql/<API-VERSION>/enums/webhooksubscriptiontopic
    res = await webhook.create_http(offline_token=<concrete_offline_token>, topic='ORDERS_CREATE', callback_url='https://sometest.com/example')
    print(f'Webhook registered with id {res.id}')

async def register_webhook_with_event_bridge_endpoint():
    # configure AWS Event Bridge https://shopify.dev/apps/webhooks/configuration/eventbridge
    res = await webhook.create_event_bridge(offline_token=<concrete_offline_token>, topic='ORDERS_CREATE', arn='<RESOURCE_NAME>')
    print(f'Webhook registered with id {res.id}')

async def register_webhook_with_pub_sub_endpoint():
    # configure Google Cloud PubSub https://shopify.dev/apps/webhooks/configuration/google-cloud
    res = await webhook.create_pub_sub(offline_token=<concrete_offline_token>, topic='ORDERS_CREATE', pub_sub_project='<PROJECT>', pub_sub_topic='<TOPIC>')
    print(f'Webhook registered with id {res.id}')
```

## Validate Webhooks

Shopify webhooks are signed with an HMAC in a header. You can use `is_valid` to [verify this signature](https://shopify.dev/apps/webhooks/configuration/https#step-5-verify-the-webhook):

```python
from spylib import webhook

is_webhook_valid = webhook.is_valid(data='data', hmac_header='hmac', api_secret_key='API_SECRET_KEY')
if is_webhook_valid:
    # do something
```
