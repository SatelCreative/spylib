from __future__ import annotations

from typing import Any, ClassVar, Dict, List, Optional
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
        except ValueError:
            raise InvalidIssuerError(f"The domain {domain} is not a valid issuer.")
        
        if cls.__url_to_base(values.get('iss')) != cls.__url_to_base(values.get('dest')):
            raise MismatchedHostError(
                f'The issuer {cls.__url_to_base(values.get("iss"))} does not match '
                f'the destination {cls.__url_to_base(values.get("dest"))}'
            )
        
        return values


    algorithm: ClassVar[str] = "HS256"
    prefix: ClassVar[str] = "Bearer "
    required_fields: ClassVar[List[str]] = ["iss", "dest", "sub", "jti", "sid"]


    @classmethod
    def from_header(
        cls,
        authorization_header: str,
        api_key: str,
        secret: str,
    ) -> SessionToken:
        # Verify the integrity of the token

        # Take the authorization headers and unload them
        if not authorization_header.startswith(cls.prefix):
            raise TokenAuthenticationError(
                "The authorization header does not contain a Bearer token."
            )
        
        token = authorization_header[len(cls.prefix) :]

        payload =  decode(
            token,
            secret,
            audience=api_key,
            algorithms=[cls.algorithm],
            options={'require': cls.required_fields},
        )

        # Verify enough fields specified and perform validation checks
        return cls.parse_obj(payload)

    @classmethod
    def __url_to_base(cls, url):
        return '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(url))
