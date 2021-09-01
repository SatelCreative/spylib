import pytest

from spylib.application import ShopifyApplication
from spylib.store import Store

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
