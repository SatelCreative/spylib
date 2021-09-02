# Shopify Python Library - SPyLib

The Shopify python library or SPyLib, simplifies the use of the Shopify
services such as the REST and GraphQL APIs as well as the OAuth authentication.
All of this is done **asynchronously using asyncio**.

Features:

* [Shopify admin API](#shopify-admin-api)
  * [REST API](#rest-api)
    * Rate limit handling per API key
    * Retry mechanism for 5xx status codes from Shopify
  * [GraphQL API](#graphql-api)
* [Shopify OAuth](#shopify-oauth)
  * Provide FastAPI router ready to handle the OAuth process
  * Handle the whole Oauth process
  * Callback validation without the need to track nonce locally
  * Provide post installation and post login function injection for full control

## Installation

```bash
pip install spylib
```

## Contributing

If you want to contribute a small change/feature, the best is to just create a PR with
your changes.
For bigger changes/features it's best to open an issue first and discuss it to agree
on the code organization and overall implementation before spending too much time on
the code, unless you want to keep it in your own forked repo.

### Setting up the development environment

We use the [python poetry](https://python-poetry.org/) package to manage this package.
Follow the official instructions to install poetry on your system then once you clone
this repository just just need to do the following to install the dependencies from
the development environment, as well as install `spylib` in
[editable mode](https://pip.pypa.io/en/stable/cli/pip_install/#install-editable):
```bash
poetry install
```

Then you can start monitoring the code for changes and run the test suite this way:
```bash
poetry shell
scripts/test_watch.sh
```

## Tutorial

The overview of this library is that you generate an application. This application
has a set of stores which can be used to execute queries on shopify. Since shopify
uses tokens, the stores can hold up to one offline token and `n` online tokens.

On initialization of the application, the OAuth endpoints for getting the tokens
are generated and must be appended to a fastAPI instance.

### Application

The core of the application is an instance of [`ShopifyApplication`](./spylib/application.py). The shopify application holds all of the stores and can be used to 
initialize the oauth logic for the application. The most basic version of the
class can be implemented as:

```python
from spylib import ShopifyApplication

shopify_app = ShopifyApplication(
  app_domain,
  shopify_handle,
  app_scopes,
  client_id,
  client_secret
)
```

To generate the oauth router for this application we can call the method `oauth_init_url`:

```python
from fastapi import FastAPI

app = FastAPI()
routes = shopify_app.generate_oauth_routes()
app.include_router(routes)
```

By default the application generates routes for just the offline token, if you
want to have both offline and online tokens you need to add in the `my_post_login`
function.

### Store
The store object contains all of the logic for querying a specific store. You 
can query on both the REST and GraphQL APIs using both online and offline tokens.

The most basic implementation of the store is using just the `name`
corresponding to the Shopify store subdomain `https://<name>.myshopify.com`,

```python
from spylib import Store

store = Store(store_name="my_store_name")
```

It can then be stored in the application, allowing us to easily share all of the
stores using the following:

```python
shopify_app = ShopifyApplication(
  app_domain,
  shopify_handle,
  app_scopes,
  client_id,
  client_secret,
  stores=[store]
)
```

### Tokens

The main way to load a token into the store is by using one of the load functions,
which can either load an online token or an offline token:

The offline token is straightforward requiring a store to add it to, and the
token that we would like to use:

```python
store = Store(store_name="my_store_name")
await store.add_offline_token(token='Te5tM3')
```

For the online token, we need to have an associated user for that specific token.
This can be pulled from a database.

```python
user = AssociatedUser(
  **{
    "id": 1,
    "first_name": "John",
    "last_name": "Smith",
    "email": "john@example.com",
    "email_verified": True,
    "account_owner": True,
    "locale": "en",
    "collaborator": False,
  }
)

store = Store(store_name="my_store_name")

await store.add_online_token(
  token='Te5tM3',
  associated_user=user,
  expires_in=1000,
)

```

### Offline Token Queries
To make a query using an offline token we can use one of the following methods:

```python
store = Store(store_name="my_store_name")

await store.add_offline_token(token='Te5tM3')

# To execute REST
store.execute_rest_offline(
  goodstatus,
  debug,
  endpoint,
  method,
  json,
)

# To execute GQL
store.execute_gql_offline(query)
```

### Online Token Queries
The online version of the query, assuming you already have the online token
for some user with `user_id` being the `AssociatedUser` `id` returned by Shopify.

```python
store = Store(store_name="my_store_name")

# To execute REST
store.execute_rest_offline(
  user_id,
  goodstatus,
  debug,
  endpoint,
  method,
  json,
)

# To execute GQL
store.execute_gql_offline(user_id, query)
```

### Rest API

The `Store` instance tracks and handles the rate limit for Rest calls.
When the rate limit is hit (status code 429), the `Store` instance will estimate how quickly
the available calls are restored and it will randomly retry one of the calls that
were stalled.

Besides the rate limit, the `Store` will also automatically retry calls failing with a status
code 5xx which are due to failures of Shopify or the network. All other status codes are
assumed to be errors of the implementation and therefore shouldn't be needlessly retried but
instead raise an exception right away.

Example `GET` request to retrieve all the tags on a customer account:

```python
custid = 1234567890
customerjson = await store.execute_rest_offline(
    goodstatus=200,
    method='get',
    debug=f'Couldn\'t get tags for customer id {custid} from Shopify.',
    endpoint=f'/customers.json?fields=tags&ids={custid}',
)
```

The `goodstatus` defines the expected successful status code. Any other status code will
be considered to be an error and will raise an exception.
In case the Rest call cannot go through, the `debug` message
is used to provide an app specific messaging along with the generic exception message.

The `method` and `endpoint` define the Rest API call with the `endpoint` being the last
part of the URL.

Example `POST` request to update tags on a customer account:

```python
custdata = await store.execute_rest_offline(
    goodstatus=200,
    method='put',
    debug=(f'Couldn\'t update tags for customer id {custid} from Shopify.'),
    endpoint=f'/customers/{custid}.json',
    json={'customer': {'id': custid, 'tags': 'mytag, yourtag, hertag, histag'}},
)
```

The body of the `POST` request is given as a dictionary to the `json` argument.
Similarly the headers can be passed as a dictionary to the `headers` argument.
The URL parameters can be passed as part of `endpoint` although it is preferrable
to provide a dictionary to the `params` argument.

#### GraphQL API

To perform a GraphQL call, one must simply provide the `query` string.
The `query` name of the argument matches the GraphQL specification for the field
name that corresponds to a string with the `query` or `mutation` code
in the GraphQL format.

The variables of the GraphQL query are passed as a dictionary to the `variables`
argument.

See this example retrieving the list of webhooks defined for a store with
a given callback URL:

```python
query = """query getWebhooks($callbackUrl: URL!) {
  webhookSubscriptions(callbackUrl: $callbackUrl, first: 1) {
    edges {
      node {
        id
        callbackUrl
      }
    }
  }
}"""

res = await store.execute_gql_offline(
    query=query,
    variables={'callbackUrl': 'https://my.app.com/webhooks'},
)
webhook_nodes = res['webhookSubscription']['edges']
```

### Shopify OAuth

Rather than reimplementing for each app the
[Shopify OAuth authentication](https://shopify.dev/tutorials/authenticate-with-oauth)
one can simple get a [FastAPI](https://fastapi.tiangolo.com/) router that provides
the install and callback endpoints ready to handle the whole OAuth process.
You just need to call `init_oauth_router` such that:

```python
from spylib import OfflineToken, OnlineToken, ShopifyApplication


async def my_post_install(self: ShopifyApplication, offline_token: OfflineToken):
    # Run after installation, store the token in a database and then add it to the store

async def my_post_login(self: ShopifyApplication, online_token: OnlineToken):
    # Run after user logs in, store to database the append the token to the store

shopify_app = ShopifyApplication(
  app_domain="Domain for your app",
  shopify_handle='URL endpoint on store for the application',
  app_scopes=['List of scopes required by the application'],
  client_id='ID for your application from spotify',
  client_secret='Client secret for the application from spotify',
  post_install=my_post_install,
  post_login=my_post_login,
)

oauth_router = shopify_app.init_oauth_router()
```

The `app_scopes` are for the offline token and the `user_scopes` for the online token.
The `public_domain` is used to set the callback URL used in the OAuth process.

This library uses a JWT encoded `nonce` to avoid the need for a database or some other
mechanism to track the `nonce`. This JWT has an expiration time and is unique for each
OAuth process making it a valid `nonce` mechanism.
The `private_key` parameter defines the key used to encode and decode this JWT.

The `post_install` and `post_login` provide a way to inject functions handling the
result of the installation and the login processes respectivaly. They are meant in 
particular to record the offline and online tokens in your app's database.
They can be synchronous or asynchronous functions taking the storename and the token
as arguments.