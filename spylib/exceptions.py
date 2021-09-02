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


class ShopifyExceedingMaxCostError(ShopifyError):
    """
    Exception to identify errors that are due to queries exceeding the max query size
    """

    pass


class UndefinedTokenError(ValueError):
    """
    Error for when a token is not defined in the store.
    """

    def __init__(
        self,
        msg=(
            'Access token has not been defined.',
            'Are you sure the token is valid for this store?',
        ),
        user=None,
        *args,
        **kwargs,
    ):
        if user:
            msg = (
                f'Access token for user {user} has not been defined.',
                'Are you sure the token is valid for this store? Or if the user',
                'has been validated for this store?',
            )
        super().__init__(msg, *args, **kwargs)


class UndefinedStoreError(ValueError):
    """
    Error for when a store is not defined in the application.
    """

    def __init__(
        self,
        msg=(
            'This store has not been defined.',
            ' Are you sure the application has a store defined with this name?',
        ),
        store=None,
        *args,
        **kwargs,
    ):
        if store:
            msg = (
                f'The store {store} has not been defined in the ',
                'application. Are you sure the store name is correct?',
            )
        super().__init__(msg, *args, **kwargs)


def not_our_fault(exception: Exception):
    """Simple function to identify invalid Shopify calls, i.e. our mistake.

    Probably the only way to make sure we retry for any other exception but those.
    """
    return not isinstance(exception, ShopifyCallInvalidError)
