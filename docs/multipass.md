# Multipass
[Shopify Multipass - Shopify Documentation](https://shopify.dev/docs/admin-api/rest/reference/plus/multipass) <br>
This helper class generates token or URL that's needed for Shopify Multipass login.

```python
from spylib import multipass


# Customer email is required to generate token or URL
customer_data = {'email': 'customer@email.com'}

# Generate URL
url = multipass.generate_url(
    secret='MULTIPASS_SECRET',
    customer_data=customer_data,
    store_url='https://example.myshopify.com'
)
# https://example.myshopify.com/account/login/multipass/{MultipassToken}

# If for some reason you need the token, you can also generate the token used in the URL separately:
token = multipass.generate_token(secret='MULTIPASS_SECRET', customer_data=customer_data)

```