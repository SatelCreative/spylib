from spylib.exceptions import FastAPIImportError

try:
    from .authentication import (
        WebhookHMACHeader,
        authenticate_webhook_hmac,
        webhook_hmac,
    )
except ImportError as e:
    raise FastAPIImportError(
        'The fastapi interface requires `fastapi` which is not installed. '
        'Run `pip install spylib[fastapi]` to be able to use it.'
    ) from e

__all__ = [
    'webhook_hmac',
    'authenticate_webhook_hmac',
    'WebhookHMACHeader',
]
