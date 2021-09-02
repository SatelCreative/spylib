import pytest

from spylib.application import ShopifyApplication
from spylib.exceptions import UndefinedStoreError
from spylib.store import Store
from spylib.token import AssociatedUser, OfflineToken, OnlineToken

from .shared import async_post_install, async_post_login, post_install, post_login

domain = 'test.testing.com'
shopify_handle = 'HANDLE'
app_scopes = ['write_products', 'read_customers']
client_id = 'API_KEY'
client_secret = 'TESTPRIVATEKEY'

store_name = 'test.myshopify.com'


@pytest.mark.asyncio
async def test_empty_app(mocker):

    shopify_app = ShopifyApplication(
        app_domain=domain,
        shopify_handle=shopify_handle,
        app_scopes=app_scopes,
        client_id=client_id,
        client_secret=client_secret,
    )

    assert shopify_app.app_domain == domain
    assert shopify_app.shopify_handle == shopify_handle
    assert shopify_app.app_scopes == app_scopes
    assert shopify_app.client_id == client_id
    assert shopify_app.client_secret == client_secret
    assert len(shopify_app.stores) == 0


@pytest.mark.asyncio
async def test_app_single_store(mocker):

    store = Store(store_name=store_name)

    shopify_app = ShopifyApplication(
        app_domain=domain,
        shopify_handle=shopify_handle,
        app_scopes=app_scopes,
        client_id=client_id,
        client_secret=client_secret,
        stores=[store],
    )

    assert len(shopify_app.stores) == 1
    assert shopify_app.stores[store_name] == store
    assert shopify_app.stores[store_name].store_name == store_name


@pytest.mark.asyncio
async def test_app_multiple_stores(mocker):
    """
    This tests to see what happens when we have multiple stores in one application.
    """

    store_2_name = "Other-Store"
    store = Store(store_name=store_name)
    store_2 = Store(store_name=store_2_name)

    shopify_app = ShopifyApplication(
        app_domain=domain,
        shopify_handle=shopify_handle,
        app_scopes=app_scopes,
        client_id=client_id,
        client_secret=client_secret,
        stores=[store, store_2],
    )

    assert len(shopify_app.stores) == 2
    assert shopify_app.stores[store_name] == store
    assert shopify_app.stores[store_name].store_name == store_name
    assert shopify_app.stores[store_2_name] == store_2
    assert shopify_app.stores[store_2_name].store_name == store_2_name


@pytest.mark.asyncio
async def test_app_multiple_stores_same_name(mocker):
    """
    This tests to see what happens if we accidentally generate two of the same
    store within the application.
    """

    store = Store(store_name=store_name)
    store_2 = Store(store_name=store_name)

    shopify_app = ShopifyApplication(
        app_domain=domain,
        shopify_handle=shopify_handle,
        app_scopes=app_scopes,
        client_id=client_id,
        client_secret=client_secret,
        stores=[store, store_2],
    )

    assert len(shopify_app.stores) == 1
    assert shopify_app.stores[store_name] == store
    assert shopify_app.stores[store_name].store_name == store_name


@pytest.mark.asyncio
async def test_app_post_install(mocker):
    """
    This tests to see what happens if we set the post_install function,
    which changes the function that is called when a new store accepts
    the app being installed on their shopify store.
    """

    store = Store(store_name=store_name)

    shopify_app = ShopifyApplication(
        app_domain=domain,
        shopify_handle=shopify_handle,
        app_scopes=app_scopes,
        client_id=client_id,
        client_secret=client_secret,
        stores=[store],
        post_install=post_install,
    )

    offline_token = OfflineToken(
        store_name=store.store_name,
        scope=[],
        access_token='123',
    )
    shopify_app.post_install(offline_token)

    assert shopify_app.stores[store_name] == store
    assert shopify_app.get_store(store.store_name).offline_access_token == offline_token


@pytest.mark.asyncio
async def test_app_post_login(mocker):
    """
    This tests to see what happens if we set the post_login function, which
    is called after a user logs into the application.
    """

    store = Store(store_name=store_name)

    shopify_app = ShopifyApplication(
        app_domain=domain,
        shopify_handle=shopify_handle,
        app_scopes=app_scopes,
        client_id=client_id,
        client_secret=client_secret,
        stores=[store],
        post_login=post_login,
    )

    # This triggers the post install, which takes a token and adds it to a store
    user = AssociatedUser(
        **{
            "id": 902541635,
            "first_name": "John",
            "last_name": "Smith",
            "email": "john@example.com",
            "email_verified": True,
            "account_owner": True,
            "locale": "en",
            "collaborator": False,
        }
    )
    user_token = OnlineToken(
        associated_user=user,
        scope=[],
        access_token='abc',
        store_name=store.store_name,
    )

    shopify_app.post_login(user_token)

    assert shopify_app.stores[store_name] == store
    assert shopify_app.get_store(store.store_name).get_online_token(user_id=user.id) == user_token


@pytest.mark.asyncio
async def test_app_post_install_async(mocker):
    """
    This tests to see what happens if we set the post_install function,
    which changes the function that is called when a new store accepts
    the app being installed on their shopify store.
    """

    store = Store(store_name=store_name)

    shopify_app = ShopifyApplication(
        app_domain=domain,
        shopify_handle=shopify_handle,
        app_scopes=app_scopes,
        client_id=client_id,
        client_secret=client_secret,
        stores=[store],
        post_install=async_post_install,
    )

    offline_token = OfflineToken(
        store_name=store.store_name,
        scope=[],
        access_token='123',
    )
    await shopify_app.post_install(offline_token)

    assert shopify_app.stores[store_name] == store
    assert shopify_app.get_store(store.store_name).offline_access_token == offline_token


@pytest.mark.asyncio
async def test_app_post_login_async(mocker):
    """
    This tests to see what happens if we set the post login to be an async function.
    """

    store = Store(store_name=store_name)

    shopify_app = ShopifyApplication(
        app_domain=domain,
        shopify_handle=shopify_handle,
        app_scopes=app_scopes,
        client_id=client_id,
        client_secret=client_secret,
        stores=[store],
        post_login=async_post_login,
    )

    # This triggers the post install, which takes a token and adds it to a store
    user = AssociatedUser(
        **{
            "id": 902541635,
            "first_name": "John",
            "last_name": "Smith",
            "email": "john@example.com",
            "email_verified": True,
            "account_owner": True,
            "locale": "en",
            "collaborator": False,
        }
    )
    user_token = OnlineToken(
        associated_user=user,
        scope=[],
        access_token='abc',
        store_name=store.store_name,
    )

    await shopify_app.post_login(user_token)

    assert shopify_app.stores[store_name] == store
    assert shopify_app.get_store(store.store_name).get_online_token(user_id=user.id) == user_token


@pytest.mark.asyncio
async def test_app_get_store(mocker):
    """
    This tests to see what happens if we attempt to request a store from the app.
    """

    store = Store(store_name=store_name)

    shopify_app = ShopifyApplication(
        app_domain=domain,
        shopify_handle=shopify_handle,
        app_scopes=app_scopes,
        client_id=client_id,
        client_secret=client_secret,
        stores=[store],
    )

    assert shopify_app.get_store(store.store_name) == store
    assert len(shopify_app.stores) == 1


@pytest.mark.asyncio
async def test_app_get_store_failed(mocker):
    """
    This tests to see what happens if we try to get a store that doesn't exist.
    """

    shopify_app = ShopifyApplication(
        app_domain=domain,
        shopify_handle=shopify_handle,
        app_scopes=app_scopes,
        client_id=client_id,
        client_secret=client_secret,
    )

    with pytest.raises(UndefinedStoreError):
        shopify_app.get_store(store_name)


@pytest.mark.asyncio
async def test_app_delete_store(mocker):
    """
    This tests to see what happens if we set the post_login function, which
    is called after a user logs into the application.
    """

    store = Store(store_name=store_name)

    shopify_app = ShopifyApplication(
        app_domain=domain,
        shopify_handle=shopify_handle,
        app_scopes=app_scopes,
        client_id=client_id,
        client_secret=client_secret,
        stores=[store],
    )

    assert len(shopify_app.stores) == 1
    shopify_app.remove_store(store.store_name)
    assert len(shopify_app.stores) == 0


@pytest.mark.asyncio
async def test_app_delete_store_failed(mocker):
    """
    This tests to see what happens if we try to get a store that doesn't exist.
    """

    shopify_app = ShopifyApplication(
        app_domain=domain,
        shopify_handle=shopify_handle,
        app_scopes=app_scopes,
        client_id=client_id,
        client_secret=client_secret,
    )

    with pytest.raises(UndefinedStoreError):
        shopify_app.remove_store(store_name)
