# Shopify GraphQL error Codes
# https://shopify.dev/api/admin-graphql#status_and_error_codes
THROTTLED_ERROR_CODE = 'THROTTLED'
MAX_COST_EXCEEDED_ERROR_CODE = 'MAX_COST_EXCEEDED'

# Error Messages
OPERATION_NAME_REQUIRED_ERROR_MESSAGE = 'An operation name is required'
WRONG_OPERATION_NAME_ERROR_MESSAGE = (
    'No operation named "{}"'  # Required as they don't stay consistant
)

UTF8ENCODING = 'utf-8'
API_CALL_NUMBER_RETRY_ATTEMPTS = 5
