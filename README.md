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

### Shopify admin API

The Shopify API version is defined [here](spylib/constants.py) and is typically
the latest stable version.

#### Initialize store instance

All the API calls to Shopify are done using an instance of the `Store` class.
This class provides methods to perform Rest and GraphQL calls.

```python
from spylib import Store

store = Store.load(store_id='mystore1', name='mystore', access_token='shppa_7a1e466ab2a')
```

Each store instance is defined using a `store_id` identifying the store uniquely, a `name`
corresponding to the Shopify store subdomain such that `https://<name>.myshopify.com`, and
the `access_token` or offline token to be used in the calls.

#### Rest API

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
customerjson = await store.shoprequest(
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
custdata = await store.shoprequest(
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

res = await store.execute_gql(
    query=QUERY,
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
from spylib.oauth import init_oauth_router, OfflineToken, OnlineToken

async def my_post_install(storename: str, offline_token: OfflineToken):
    """Function handling the offline token obtained at the end of the installation"""
    # Store to database
    pass

async def my_post_login(storename: str, online_token: OnlineToken):
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
as arguments.
```
