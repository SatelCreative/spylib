# Multipass
[Shopify Multipass - Shopify Documentation](https://shopify.dev/docs/admin-api/rest/reference/plus/multipass) <br>
This helper class generates token or URL that's needed for Shopify Multipass login.

```python
from spylib import multipass


# Customer email is required to generate token or URL
contact_data = {"email": "customer@email.com"}

# Generate URL
url = multipass.generate_url("MULTIPASS_SECRET", contact_data, 'https://example.myshopify.com')
# https://example.myshopify.com/account/login/multipass/{MultipassToken}

# If for some reason you need the token, you can also generate the token used in the URL separately:
token = multipass.generate_token("MULTIPASS_SECRET", contact_data)

```