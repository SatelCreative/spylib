# Shopify Python Library - SPyLib

The Shopify python library or SPyLib, simplifies the use of the Shopify
services such as the REST and GraphQL APIs as well as the OAuth authentication.
All of this is done **asynchronously using asyncio**.

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


## Overview

### Token

The token class contains the majority of the logic for communicating with shopify.
To use the token class, you must define a child class for the tokens you are using 
and implement the `save` and `load` abstract methods. Your option for child classes 
are `OnlineTokenABC` or `OfflineTokenABC`:

#### Implement Token Classes 

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
```

#### Create Token

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
```

#### Querying Shopify

We can query the store using either the REST endpoint or the GraphQL endpoint:

```python
token.execute_rest(
  goodstatus,
  method,
  debug,
  endpoint
)

token.execute_gql(
  query,
  variables,
  operation_name
)
```

The `REST` method takes a `goodstatus` parameter that is the response from the API
that will not trigger an error.

The `method` can be `get`, `post`, `put` or `delete`.

Debug is the error that is outputted on failure.

Endpoint is the API endpoint string that we are querying.

### OAuth

Rather than reimplementing for each app the
[Shopify OAuth authentication](https://shopify.dev/tutorials/authenticate-with-oauth)
one can simple get a [FastAPI](https://fastapi.tiangolo.com/) router that provides
the install and callback endpoints ready to handle the whole OAuth process.
You just need to call `init_oauth_router` such that:

```python
from spylib.oauth import OfflineToken, OnlineToken, init_oauth_router


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
