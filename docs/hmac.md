# HMAC

The hmac functionality can be used to validate the following Shopify requests:
 - [OAuth](https://shopify.dev/apps/auth/oauth/getting-started#step-7-verify-a-request)
 - [Webhook](https://shopify.dev/apps/webhooks/configuration/https#verify-the-webhook)
 - [App Proxy](https://shopify.dev/apps/online-store/app-proxies#calculate-a-digital-signature)

```python
from spylib.hmac import validate

# use_base64 is set to False by default, set it to True for verifying webhook hmac
def validate_webhook_hmac(data: str, hmac_header: str, api_secret_key: str):
    validate(secret=api_secret_key, sent_hmac=hmac_header, message=data, use_base64=True)

```
