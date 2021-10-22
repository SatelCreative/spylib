from __future__ import annotations

from hmac import compare_digest
from pathlib import Path
from urllib import parse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from .hmac import calculate_message_hmac


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

            real_signature = decoded_message.pop('signature')[0]
            body = '&'.join(
                [f'{arg}={",".join(decoded_message[arg])}' for arg in decoded_message.keys()]
            )

            message_signature = calculate_message_hmac(self.secret, body)

            # Validate that the message HMAC and recieved HMAC are the same.
            if not compare_digest(real_signature, message_signature):
                return JSONResponse(
                    status_code=400,
                    content={"error": "HMAC failed to be verified for the request"},
                )

        return await call_next(request)
