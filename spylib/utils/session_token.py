from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from jwt import decode
from pydantic import root_validator
from pydantic.main import BaseModel
from pydantic.networks import HttpUrl

from .domain import store_domain


class ValidationError(Exception):
    pass


class InvalidIssuerError(ValidationError):
    pass


class MismatchedHostError(ValidationError):
    pass


class TokenAuthenticationError(ValidationError):
    pass


class SessionToken(BaseModel):
    """
    Session tokens are derived from the authrization header from Shopify.
    This performs the set of validations as defined by shopify
    https://shopify.dev/apps/auth/session-tokens/authenticate-an-embedded-app-using-session-tokens#obtain-session-details-manually
    """

    iss: HttpUrl
    dest: HttpUrl
    aud: Optional[str]
    sub: int
    exp: Optional[float]
    nbf: Optional[float]
    iat: Optional[float]
    jti: int
    sid: str

    @root_validator()
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
    @property
    def algorithm(cls) -> str:
        return 'HS256'

    @classmethod
    @property
    def prefix(cls) -> str:
        return 'Bearer '

    @classmethod
    @property
    def required_fields(cls) -> List[str]:
        return ['iss', 'dest', 'sub', 'jti', 'sid']

    @classmethod
    def from_header(
        cls,
        authorization_header: str,
        api_key: str,
        secret: str,
    ) -> SessionToken:

        # Take the authorization headers and unload them
        if not authorization_header.startswith(str(cls.prefix)):
            raise TokenAuthenticationError(
                'The authorization header does not contain a Bearer token.'
            )

        token = authorization_header[len(str(cls.prefix)) :]

        payload = decode(
            token,
            secret,
            audience=api_key,
            algorithms=[str(cls.algorithm)],
            options={'require': cls.required_fields},
        )

        # Verify enough fields specified and perform validation checks
        return cls.parse_obj(payload)

    @staticmethod
    def __url_to_base(url):
        return '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(url))
