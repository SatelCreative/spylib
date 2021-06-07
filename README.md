# satel-shopify

The satel-shopify python library simplifies the use of the Shopify services such as
the REST and GraphQL APIs as well as the OAuth authentication.
All of this is done **asynchronously using asyncio**.

Features:

* [Shopify admin API](shopify-admin-api)
  * [REST API](#rest-api)
    * Rate limit handling per API key
    * Retry mechanism for 5xx status codes from Shopify
  * [GraphQL AP](#graphql-api)
* [Shopify OAuth](#shopify-oauth)
  * Provide FastAPI router ready to handle the OAuth process
  * Handle the whole Oauth process
  * Callback validation without the need to track nonce locally
  * Provide post installation and post login function injection for full control

## Tutorial

### Shopify admin API

The Shopify API version is defined [here](satel_shopify/constants.py) and is typically
the latest stable version.

#### Initialize

```python
from satel_shopify import Store

store = Store.load(store_id='mystore1', name='mystore', access_token='shppa_7a1e466ab2a')
```

#### Rest API

```python
custid = 1234567890
customerjson = await store.shoprequest(
    goodstatus=200,
    method='get',
    debug=f'Couldn\'t get tags for customer id {custid} from Shopify.',
    endpoint=f'/customers.json?fields=tags&ids={custid}',
)
```


```python
custdata = await store.shoprequest(
    goodstatus=200,
    method='put',
    debug=(f'Couldn\'t update tags for customer id {custid} from Shopify.'),
    endpoint=f'/customers/{custid}.json',
    json={'customer': {'id': custid, 'tags': 'mytag, yourtag, hertag, histag'}},
)
```

#### GraphQL API

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

res = await store.execute_gql(
    query=QUERY,
    variables={'callbackUrl': 'https://my.app.com/webhooks'},
)
webhook_nodes = res['data']['webhookSubscription']['edges']
```

### Shopify OAuth

Rather than reimplementing for each app the
[Shopify OAuth authentication](https://shopify.dev/tutorials/authenticate-with-oauth)
one can simple get a [FastAPI](https://fastapi.tiangolo.com/) router that provides
the install and callback endpoints ready to handle the whole OAuth process.
You just need to call `init_oauth_router` such that:

```python
from satel_shopify.oauth import init_oauth_router, OfflineToken, OnlineToken

async def post_install(storename: str, offline_token: OfflineToken):
    """Function handling the offline token obtained at the end of the installation"""
    # Store to database
    pass

async def post_login(storename: str, online_token: OnlineToken):
    """Function handling the online token obtained at the end of the user login"""
    # Store to database
    pass


oauth_router = init_oauth_router(
    app_scopes=['write_orders', 'write_products'],
    user_scopes=['read_orders', 'write_products'],
    public_domain='my.app.com',
    private_key='KEY_FOR_OAUTH_JWT',
    post_install=my_post_install,
    post_login=my_post_login,
)
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
as arguments. For example:
```python
from satel_shopify.oauth import OfflineToken, OnlineToken
def my_post_install(storename: str, offlinetoken: OfflineToken):
  pass
def my_post_login(storename: str, onlinetoken: OnlineToken):
  pass
async def my_async_post_install(storename: str, offlinetoken: OfflineToken):
  pass
async def my_async_post_login(storename: str, onlinetoken: OnlineToken):
  pass
```
