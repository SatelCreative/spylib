from __future__ import annotations

from pathlib import Path
from urllib import parse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from .hmac import validate_hmac


class CheckAppProxy(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, secret: str, proxy_endpoint: str) -> None:
        super().__init__(app)
        self.secret: str = secret
        self.proxy_endpoint: Path = Path(proxy_endpoint)

    async def dispatch(self, request: Request, call_next):

        # As middleware is run on everyt(hing, this allows us to avoid checking on
        # non-proxied endpoints (as you can only have 1 proxy root per app)
        path = Path(request.scope['path'])
        if path == self.proxy_endpoint or self.proxy_endpoint in path.parents:
            # Take the authorization headers and unload them
            decoded_message = parse.parse_qs(str(request.query_params))

            try:
                validate_hmac(
                    secret=self.secret,
                    hash_name='signature',
                    message=decoded_message,
                )
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={"error": "HMAC failed to be verified for the request"},
                )

        return await call_next(request)
