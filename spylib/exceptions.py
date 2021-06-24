class ShopifyError(Exception):
    """Exception to identify any Shopify error"""

    pass


class ShopifyCallInvalidError(ShopifyError):
    """Exception to identify errors that our due to bad data sent by us

    These should not be retried
    """

    pass


class ShopifyThrottledError(ShopifyError):
    """Exception to identify errors that are due to rate limit control"""

    pass


def not_our_fault(exception: Exception):
    """Simple function to identify invalid Shopify calls, i.e. our mistake.

    Probably the only way to make sure we retry for any other exception but those.
    """
    return not isinstance(exception, ShopifyCallInvalidError)
