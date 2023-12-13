class ShopifyError(Exception):
    """Exception to identify any Shopify error."""

    pass


class ShopifyGQLError(Exception):
    """Exception to identify any Shopify admin graphql error."""

    pass


class ShopifyIntermittentError(Exception):
    """Exception to identify any Shopify admin API Intermittent error."""

    pass


class ShopifyGQLUserError(Exception):
    """Exception to identify any Shopify admin graphql error caused by the user mistake."""

    pass


class ShopifyInvalidResponseBody(ShopifyError):
    """Exception to identify when Shopify returned body is not the expected type, i.e. not a JSON.

    These seem extremely rare and should be retried because they are intermittent and most likely
    and internal error in Shopify that wasn't handled properly.
    """

    pass


class ShopifyCallInvalidError(ShopifyError):
    """Exception to identify errors that our due to bad data sent by us.

    These should not be retried
    """

    pass


class ShopifyThrottledError(ShopifyError):
    """Exception to identify errors that are due to rate limit control."""

    pass


class ShopifyExceedingMaxCostError(ShopifyError):
    """Exception to identify errors that are due to queries exceeding the max query size."""

    pass


class FastAPIImportError(ImportError):
    """Exception to identify errors when spylip.oauth is accessed without fastapi installed."""

    pass


def not_our_fault(exception: BaseException) -> bool:
    """Simple function to identify invalid Shopify calls, i.e. our mistake.

    Probably the only way to make sure we retry for any other exception but those.
    """
    return not isinstance(exception, ShopifyCallInvalidError)
