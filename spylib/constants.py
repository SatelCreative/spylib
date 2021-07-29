API_VERSION: str = '2021-04'
# Default assumes Shopify Plus rate
RATE = 4
MAX_TOKENS = 80
THROTTLED_ERROR_MESSAGE = 'Throttled'
OPERATION_NAME_REQUIRED_ERROR_MESSAGE = 'An operation name is required'
WRONG_OPERATION_NAME_ERROR_MESSAGE = (
    'No operation named "{}"'  # Required as they don't stay consistant
)
