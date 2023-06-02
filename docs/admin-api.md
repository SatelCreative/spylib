# Admin API


## Token

The token class contains the majority of the logic for communicating with shopify.
To use the token class, you must define a child class for the tokens you are using
and implement a subset of the `save` and `load` abstract methods. Your option for
child classes are `OnlineTokenABC`, `OfflineTokenABC` or `PrivateTokenABC`:

### Implement Token Classes

```python
class OfflineToken(OfflineTokenABC):
  async def save(self):
      # Some code to save the token to a database

  @classmethod
  async def load(cls, store_name: str):
      # Some code to load the token from the database

class OnlineToken(OnlineTokenABC):
  async def save(self):
      # Some code to save the token to a database

  @classmethod
  async def load(cls, store_name: str, user_id: str):
      # Some code to load the token from the database

class PrivateToken(PrivateTokenABC):
  @classmethod
  async def load(cls, store_name: str, user_id: str):
      # Some code to load the token from the database
      # No need for save, as it is static.
```

### Change Shopify API version

- As shown in the `Implement Token Classes`, token can be used as following:
```python
from spylib import OfflineTokenABC


class OfflineToken(OfflineTokenABC):
  async def save(self):
      pass

  @classmethod
  async def load(cls, store_name: str):
      # For version <= 0.8.x, use sync for load function
      pass
```

- If the Shopify API version used in Spylib is not the desired version, it can be changed with the following:
```python
class OfflineToken(OfflineTokenABC):
  async def save(self):
      pass

  @classmethod
  async def load(cls, store_name: str):
      # For version <= 0.8.x, use sync for load function
      pass
      
# Add the version to be used here
OfflineToken.api_version: '2022-01'
```

### Create Token

Once you have defined these methods, we can create an instance of a token using
one of the following:

```python
token = OfflineToken(
  store_name,
  access_token,
  scope
)

token = OnlineToken(
  store_name,
  access_token,
  scope,
  expires_in,
  associated_user_scope,
  associated_user_id
)

token = PrivateToken(
  store_name,
  access_token,
  scope
)
```

## Querying Shopify

### REST

We can query the store using the REST endpoint:

```python
await token.execute_rest(
  request: Request,
  endpoint: str,
  json: Optional[Dict[str, Any]],
  debug: Optional[str],
)
```

For example, if you want to query a product from shopify you can run:

```python
product_json = await token.execute_rest(
  request = GET,
  endpoint = f'/products/{product_id}.json'
)
```

If you want to update a product in a shop you can run:

```python
product_json = await token.execute_rest(
  request = PUT,
  endpoint = f'/products/{product_id}.json',
  json = {
    "product":
    {
      "id": product_id,
      "title": "New Title"
    }
  }
)
```

The `REST` method takes a `request` parameter which is one of the `Request` constants defined in
the [rest](https://github.com/SatelCreative/spylib/blob/main/spylib/utils/rest.py) file.
The options are `GET`, `POST`, `PUT`, or `DELETE`.

Endpoint is the API endpoint string that we are querying, this should be similar to
the following format:

```python
f'/{resource}.json?fields={resource.param}&{[params]}'
```

The `debug` parameter is the message that is returned when there is an error. It is optional as it defaults to `""`.

### GraphQL

We can also query Shopify using the GraphQL endpoint:

```python
token.execute_gql(
  query: str,
  variables: Dict[str, Any],
  operation_name: Optional[str]
)
```

For example, if you want to query a product from shopify you can run:

```python
query = """
{
  product(id: "gid://shopify/Product/1974208299030") {
  	id,
    title
  }
}"""

product_json = await token.execute_gql(query = query)
```

If you want to update a product in a shop you can run:

```python
query = """
mutation productUpdateMutation($id: ID, $title: String) {
  productUpdate(input: {
    id: $id,
    title: $title
  })
  {
    product {
      id
    }
  }
}"""

variables = {
  'id': 'gid://shopify/Product/108828309',
  'title': "Sweet new product - GraphQL Edition"
}
product_json = await token.execute_gql(
  query = query,
  variables = variables
)
```

The `query` is a GraphQL query that will be passed to shopify for execution. You can use the GQL explorer
for your shop to create a query. For example, the [shopify demo GQL explorer](https://shopify.dev/apps/tools/graphiql-admin-api).

The `variables` are a dictionary of variables that will be substituted into the query.

The `operation_name` is a name for the query you are about to run.
