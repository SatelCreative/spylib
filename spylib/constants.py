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
# Error Messages
OPERATION_NAME_REQUIRED_ERROR_MESSAGE = 'An operation name is required'
WRONG_OPERATION_NAME_ERROR_MESSAGE = (
    'No operation named "{}"'  # Required as they don't stay consistant
)
