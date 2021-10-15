from unittest.mock import AsyncMock

import pytest

from spylib.exceptions import ShopifyExceedingMaxCostError

from ..token_classes import MockHTTPResponse, OfflineToken, test_information

graphql_throttling_queries = [
    """    {
      products(first: 10) {
        edges {
          node {
            variants(first: 96) {
              edges {
                node {
                  id
                }
              }
            }
          }
        }
      }
    }
    """,
    """
    {
      products(first: 10) {
        edges {
          node {
            variants(first: 100) {
              edges {
                node {
                  id
                }
              }
            }
          }
        }
      }
    }
    """,
]


@pytest.mark.asyncio
async def test_store_graphql_throttling_happypath(mocker):
    """
    Tests the throttling of the graphQL requests. There are 3 possible outcomes
    when running a test in regards to the throttling:

    1. The query runs with no issues (under the limit and within the current resources).
    2. The query fails to run due to a lack of resources, and needs to wait for
        the bucket to re-fill.
    3. The query fails indefinitely due to it being in excess of the maximum
        possible query size.

    This handles the first case (#1).
    """
    token = await OfflineToken.load(store_name=test_information.store_name)

    gql_response = {
        'extensions': {
            'cost': {
                'requestedQueryCost': 992,
                'actualQueryCost': 42,
                'throttleStatus': {
                    'maximumAvailable': 1000,
                    'currentlyAvailable': 1000 - 42,
                    'restoreRate': 50,
                },
            }
        },
        'data': {
            'products': {
                'edges': [
                    {
                        'node': {
                            'variants': {
                                'edges': [
                                    {'node': {'id': 'gid://shopify/ProductVariant/19523123216406'}}
                                ]
                            }
                        }
                    }
                ]
            }
        },
    }

    shopify_request_mock = mocker.patch(
        'httpx.AsyncClient.request',
        new_callable=AsyncMock,
        return_value=MockHTTPResponse(status_code=200, jsondata=gql_response),
    )
    await token.execute_gql(query=graphql_throttling_queries[0])

    assert shopify_request_mock.call_count == 1


@pytest.mark.asyncio
async def test_store_graphql_throttling_catch_cap(mocker):
    """
    Tests the throttling of the graphQL requests. There are 3 possible outcomes
    when running a test in regards to the throttling. This test covers:

    2. The query fails to run due to a lack of resources, and needs to wait for
        the bucket to re-fill.

    """
    token = await OfflineToken.load(store_name=test_information.store_name)

    gql_failure = {
        'extensions': {
            'cost': {
                'requestedQueryCost': 992,
                'actualQueryCost': None,
                'throttleStatus': {
                    'maximumAvailable': 1000,
                    'currentlyAvailable': 800,
                    'restoreRate': 50,
                },
            }
        },
        'errors': [
            {
                'message': 'Throttled',
                'extensions': {
                    'code': 'THROTTLED',
                    'documentation': 'https://help.shopify.com/api/usage/rate-limits',
                },
            }
        ],
    }

    gql_success = {
        'extensions': {
            'cost': {
                'requestedQueryCost': 992,
                'actualQueryCost': None,
                'throttleStatus': {
                    'maximumAvailable': 1000,
                    'currentlyAvailable': 800,
                    'restoreRate': 50,
                },
            }
        },
        'data': {
            'products': {
                'edges': [
                    {
                        'node': {
                            'variants': {
                                'edges': [
                                    {'node': {'id': 'gid://shopify/ProductVariant/19523123216406'}}
                                ]
                            }
                        }
                    }
                ]
            }
        },
    }

    shopify_request_mock = mocker.patch(
        'httpx.AsyncClient.request',
        new_callable=AsyncMock,
        side_effect=[
            MockHTTPResponse(status_code=200, jsondata=gql_failure),
            MockHTTPResponse(status_code=200, jsondata=gql_success),
        ],
    )

    await token.execute_gql(query=graphql_throttling_queries[0])

    assert shopify_request_mock.call_count == 2


params = [
    pytest.param(
        graphql_throttling_queries[1],
        id='Indefinite failed run',
    ),
]


@pytest.mark.asyncio
async def test_store_graphql_throttling_error_test(mocker):
    """
    Tests the throttling of the graphQL requests. There are 3 possible outcomes
    when running a test in regards to the throttling, this handles

    3. The query fails indefinitely due to it being in excess of the maximum
        possible query size.
    """
    token = await OfflineToken.load(store_name=test_information.store_name)

    gql_response = {
        'errors': [
            {
                'message': 'Query cost is 1032, which exceeds the single query ',
                'extensions': {
                    'code': 'MAX_COST_EXCEEDED',
                    'cost': 1032,
                    'maxCost': 1000,
                    'documentation': 'https://help.shopify.com/api/usage/rate-limits',
                },
            }
        ]
    }

    shopify_request_mock = mocker.patch(
        'httpx.AsyncClient.request',
        new_callable=AsyncMock,
        return_value=MockHTTPResponse(status_code=200, jsondata=gql_response),
    )

    with pytest.raises(ShopifyExceedingMaxCostError):
        await token.execute_gql(query=graphql_throttling_queries[1])

    assert shopify_request_mock.call_count == 1
