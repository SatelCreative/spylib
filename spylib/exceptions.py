class ShopifyError(Exception):
    """Exception to identify any Shopify error"""

    pass


class ShopifyGQLError(Exception):
    """Exception to identify any Shopify admin graphql error"""

    pass


class ShopifyGQLUserError(Exception):
    """Exception to identify any Shopify admin graphql error caused by the user mistake"""

    pass


class ShopifyCallInvalidError(ShopifyError):
    """Exception to identify errors that our due to bad data sent by us

    These should not be retried
    """

    pass


class ShopifyThrottledError(ShopifyError):
    """Exception to identify errors that are due to rate limit control"""

    pass


class ShopifyExceedingMaxCostError(ShopifyError):
    """
    Exception to identify errors that are due to queries exceeding the max query size
    """

    pass


class FastAPIImportError(ImportError):
    """Exception to identify errors when spylip.oauth is accessed without fastapi installed"""

    pass


def not_our_fault(exception: Exception):
    """Simple function to identify invalid Shopify calls, i.e. our mistake.

    Probably the only way to make sure we retry for any other exception but those.
    """
    return not isinstance(exception, ShopifyCallInvalidError)
