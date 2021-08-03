API_VERSION: str = '2021-04'
# Default assumes Shopify Plus rate
RATE = 4
MAX_TOKENS = 80
GRAPH_MAX = 1000  # Max rate for GraphQL

"""
These are the text error codes thrown by the GraphQL API. Although some errors
throw a code e.g.

    "errors": [
        {
            "message": "Throttled",
            "extensions": {
                "code": "THROTTLED"
            }
        }

Not all provide the `code` parameter. Although you could just handle errors
based on the message, this becomes very difficult as some of the messages
are very long (see the max_cost_exceeded error output, which is ~350 characters)
"""

# Error Codes
THROTTLED_ERROR_CODE = 'THROTTLED'
MAX_COST_EXCEEDED_ERROR_CODE = 'MAX_COST_EXCEEDED'
