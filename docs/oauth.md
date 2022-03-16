# Install an app through OAuth

**Notice** there have been considerable changes to the oauth in version 0.3. The core
of this change has been the move from environment variables to parameters in the init
script for the routers. The following describes a very basic implementation.

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
    api_key='SHOPIFY_APP_API_KEY',
    api_secret_key='SHOPIFY_APP_SECRET_KEY',
    app_handle='SHOPIFY_APP_HANDLE',
    post_install=my_post_install,
    post_login=my_post_login,
    install_init_path='/install_path',
    callback_path='/callback_path',
    path_prefix= '/api',
)
```

The `app_scopes` are for the offline token and the `user_scopes` for the online token.
The `public_domain` is used to set the callback URL used in the OAuth process.

This library uses a JWT encoded `nonce` to avoid the need for a database or some other
mechanism to track the `nonce`. This JWT has an expiration time and is unique for each
OAuth process making it a valid `nonce` mechanism.
The `private_key` parameter defines the key used to encode and decode this JWT.

The api and secret key can be found inside your shopify app main configuration page. The
app handle can be found in the same spot but needs to be pulled from the url:

1. Go to your shopify app's editing page (The url should be `https://partners.shopify.com/<partner_id>/apps/<app_id>/edit`)
2. Open the console and run `window.RailsData.user.app.handle`. The result is the handle.

The `post_install` and `post_login` provide a way to inject functions handling the
result of the installation and the login processes respectivaly. They are meant in
particular to record the offline and online tokens in your app's database.
They can be synchronous or asynchronous functions taking the storename and the token
as arguments.

The `install_init_path` is used to set the path for initiating the OAuth process. 
It has a default value `/shopify/auth`. <br>
The `callback_path` is used to set the callback path once user has accepted the permissions required by installing the app. 
It has a default value  `/callback`. <br>
The `path_prefix` applies to both `install_init_path` and `callback_path` and it's empty by default. <br>
With the example above the URL to install the app will be `https://my.app.com/api/install_path` 
and the callback URL will be `https://my.app.com/api/callback_path`
