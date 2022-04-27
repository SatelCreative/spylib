# Multipass
[Shopify Multipass](https://shopify.dev/docs/admin-api/rest/reference/plus/multipass) <br>
This helper class generates token or URL that's needed for Shopify Multipass login (Only available in Shopify Plus)
```python
from spylib import Multipass

# Customer email is required to generate token or URL
customer_data = {"email": "customer@email.com"}
# Initiate the Multipass class
multipass = Multipass("MULTIPASSSECRET")
# Generate URL
url = multipass.generate_url(customer_data, "https://{ShopifyDomain}.myshopify.com")

# https://{ShopifyDomain}.myshopify.com/account/login/multipass/{MultipassToken}

```