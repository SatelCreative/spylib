import pytest

from .shared import (
    check_oauth_redirect_query,
    check_oauth_redirect_url,
    initialize_store,
)


@pytest.mark.asyncio
async def test_initialization_endpoint_missing_shop_argument(mocker):
    """
    Tests the initialization endpoint to be sure we only redirect if we have the app handle
    """
    shopify_app, app, client, store_name = initialize_store()

    # Missing shop argument
    response = client.get('/shopify/auth')
    assert response.status_code == 422
    body = response.json()
    assert body == {
        'detail': [
            {
                'loc': ['query', 'shop'],
                'msg': 'field required',
                'type': 'value_error.missing',
            }
        ],
    }


@pytest.mark.asyncio
async def test_initialization_endpoint(mocker):
    """
    Tests to be sure that the initial redirect is working and is going to the right
    location.
    """
    shopify_app, app, client, shop_name = initialize_store()
    response = client.get(
        '/shopify/auth',
        params=dict(shop=f'{shop_name}.myshopify.com'),
        allow_redirects=False,
    )
    query = check_oauth_redirect_url(
        shop_domain=f'{shop_name}.myshopify.com',
        response=response,
        client=client,
        path='/admin/oauth/authorize',
    )
    check_oauth_redirect_query(
        shopify_app=shopify_app,
        query=query,
    )
