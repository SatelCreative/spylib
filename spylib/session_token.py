from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import urlparse

from jwt import decode
from pydantic import model_validator
from pydantic.main import BaseModel
from pydantic.networks import HttpUrl

from .utils.domain import store_domain

REQUIRED_FIELDS = ['iss', 'dest', 'sub', 'jti', 'sid']
ALGORITHM = 'HS256'
PREFIX = 'Bearer '
LEEWAY_SECONDS = 10


class TokenValidationError(Exception):
    pass


class InvalidIssuerError(TokenValidationError):
    pass


class MismatchedHostError(TokenValidationError):
    pass


class TokenAuthenticationError(TokenValidationError):
    pass


class SessionToken(BaseModel):
    """Session tokens are derived from the authorization header from Shopify.

    This performs the set of validations as defined by shopify
    https://shopify.dev/apps/auth/session-tokens/authenticate-an-embedded-app-using-session-tokens#obtain-session-details-manually
    """

    iss: HttpUrl
    dest: HttpUrl
    aud: Optional[str] = None
    sub: str
    exp: Optional[float] = None
    nbf: Optional[float] = None
    iat: Optional[float] = None
    jti: str
    sid: str

    @model_validator(mode='before')
    @classmethod
    def equal_iss_and_dest(cls, values: Dict[str, Any]):
        domain = cls.__url_to_base(values.get('iss'))
        try:
            store_domain(domain)
        except ValueError as e:
            raise InvalidIssuerError(f'The domain {domain} is not a valid issuer.') from e

        iss = cls.__url_to_base(values.get('iss'))
        dest = cls.__url_to_base(values.get('dest'))
        if iss != dest:
            raise MismatchedHostError(f'The issuer {iss} does not match the destination {dest}')

        return values

    @classmethod
    def from_header(
        cls,
        authorization_header: str,
        api_key: str,
        secret: str,
    ) -> SessionToken:
        # Take the authorization headers and unload them
        if not authorization_header.startswith(PREFIX):
            raise TokenAuthenticationError(
                'The authorization header does not contain a Bearer token.'
            )

        token = authorization_header[len(PREFIX) :]

        payload = decode(
            token,
            secret,
            audience=api_key,
            algorithms=[ALGORITHM],
            # AppBridge frequently sends future `nbf`, and it causes `ImmatureSignatureError`.
            # Accept few seconds clock skew to avoid this error.
            leeway=LEEWAY_SECONDS,
            options={'require': REQUIRED_FIELDS},
        )

        # Verify enough fields specified and perform validation checks
        return cls.model_validate(payload)

    @staticmethod
    def __url_to_base(url):
        return '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(url))
