from typing import Optional

from fastapi import Request, Security  # type: ignore
from fastapi.openapi.models import APIKey, APIKeyIn  # type: ignore
from fastapi.security.api_key import APIKeyBase  # type: ignore
from starlette.exceptions import HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from spylib import webhook

SHOPIFY_WEBHOOK_HMAC_HEADER = 'X-Shopify-Hmac-SHA256'


class WebhookHMACHeader(APIKeyBase):
    """Reuse APIKey to authenticate the webhook using the HMAC signature.

    It requires our own implementation of APIKeyHeader because we need to
    pass in the api secret and process the whole request object.
    """

    def __init__(
        self,
        *,
        name: str,
        api_secret_key: str,
        scheme_name: Optional[str] = None,
        description: Optional[str] = None,
        auto_error: bool = True,
    ):
        self.model: APIKey = APIKey(**{'in': APIKeyIn.query}, name=name, description=description)
        self.scheme_name = scheme_name or self.__class__.__name__
        self.auto_error = auto_error
        self.api_secret_key = api_secret_key

    async def __call__(self, request: Request) -> bool:
        data = str(await request.body(), 'utf-8')
        if not self.api_secret_key:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail='api_secret_key must be set'
            )

        hmac_header = request.headers.get(SHOPIFY_WEBHOOK_HMAC_HEADER, '')
        return webhook.validate(
            data=data, hmac_header=hmac_header, api_secret_key=self.api_secret_key
        )


webhook_hmac = WebhookHMACHeader(name=SHOPIFY_WEBHOOK_HMAC_HEADER, api_secret_key='')


def authenticate_webhook_hmac(hmac: bool = Security(webhook_hmac)):
    """Dependency for authenticating the webhook using the HMAC signature.

    `webhook_hmac.api_secret_key` needs to be assigned with a valid secret prior to using this dependency.

    ```python
    webhook_hmac.api_secret_key = 'SOME_SECRET'
    @app.post('/SOME_PATH')
    def some_path(is_hmac_valid: bool = Depends(authenticate_webhook_hmac)):
        if not is_hmac_valid:
            return HTTPException(status_code=400, detail='Invalid HMAC')
    ```
    """

    if not hmac:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, detail='Webhook HMAC authentication failed'
        )
    else:
        return hmac
