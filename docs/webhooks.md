# Webhooks

The [webhook](https://shopify.dev/apps/webhooks/configuration)
functionality can be used to register webhooks and validate that the webhook notifications are from Shopify

**Breaking Changes in version 0.6.0**: <br>
The param `is_base64` used in function `validate` from module `spylib.utils.hmac` is renamed to `use_base64`
to better convey the meaning of the parameter


## Register Webhooks

You can easily register your endpoint to receive webhooks from Shopify using an admin API access token:
```python
from spylib import OfflineTokenABC

class OfflineToken(OfflineTokenABC):
    """Example offline token"""
    async def save(self):
        # Write to storage
        pass

    async def load(cls, store_name: str):
        # API access scopes from https://shopify.dev/api/usage/access-scopes
        return cls(store_name=store_name, scope=['write_orders'], access_token='ACCESS_TOKEN')

async def register_webhook_with_http_endpoint():

    token = await OfflineToken.load(store_name='my-store')
    # topics from https://shopify.dev/api/admin-graphql/<API-VERSION>/enums/webhooksubscriptiontopic
    res = await token.create_http_webhook(topic='ORDERS_CREATE', callback_url='https://sometest.com/example')
    print(f'Webhook registered with id {res.id}')
    # topics from https://shopify.dev/api/admin-graphql/<API-VERSION>/enums/webhooksubscriptiontopic
    res = await token.create_http_webhook(topic='ORDERS_CREATE', callback_url='https://sometest.com/example') 
```

## Validate Webhooks

Shopify webhooks are signed with an HMAC in a header. You can use `is_webhook_valid` to [verify this signature](https://shopify.dev/apps/webhooks/configuration/https#step-5-verify-the-webhook):

```python
is_valid = is_webhook_valid(data='data', hmac_header='hmac', api_secret_key='API_SECRET_KEY')
if is_valid:
    # do something
```
