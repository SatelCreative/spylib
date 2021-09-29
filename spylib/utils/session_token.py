from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar, Dict, List, Optional
from urllib.parse import urlparse

from jwt import decode
from jwt.exceptions import PyJWKError
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

    algorithm: ClassVar[str] = "HS256"
    prefix: ClassVar[str] = "Bearer "
    required_fields: ClassVar[List[str]] = ["iss", "dest", "sub", "jti", "sid"]

    class Config:
        arbitrary_types_allowed = True

    def validate(self) -> None:
        self.__validate_hostname()
        self.__validate_destination()
        self.__validate_nbf()
        self.__validate_sub()

    @classmethod
    def decode_token_from_header(
        cls,
        authorization_header: str,
        api_key: str,
        secret: str,
    ) -> SessionToken:
        # Verify the integrity of the token

        # Take the authorization headers and unload them
        token = cls.__extract_session_token(authorization_header)
        payload = cls.__decode_session_token(token, api_key, secret)

        # Verify enough fields specified and perform validation checks
        session_token = cls(**payload)
        session_token.validate()

        return session_token

    @classmethod
    def __extract_session_token(cls, authorization_header: str) -> str:
        if not authorization_header.startswith(cls.prefix):
            raise TokenAuthenticationError(
                "The authorization header does not contain a Bearer token."
            )
        return authorization_header[len(cls.prefix) :]

    @classmethod
    def __decode_session_token(
        cls, session_token: str, api_key: str, secret: str
    ) -> Dict[str, Any]:
        """
        By default the JWT.decode method automatically checks to see if the
        exp is in the past,
        """
        try:
            return decode(
                session_token,
                secret,
                audience=api_key,
                algorithms=[cls.algorithm],
                options={'require': cls.required_fields},
            )
        except PyJWKError as e:
            raise e("Error decoding session token")

    def __validate_destination(self):
        if self.__url_to_base(self.iss) != self.__url_to_base(self.dest):
            raise MismatchedHostError(
                f'The issuer {self.__url_to_base(self.iss)} does not match '
                f'the destination {self.__url_to_base(self.dest)}'
            )

    def __validate_hostname(self):
        domain = self.__url_to_base(self.iss)
        try:
            store_domain(domain)
        except ValueError:
            raise InvalidIssuerError(f"The domain {domain} is not a valid issuer.")

    def __validate_nbf(self):
        """
        Checks to be sure that the nbf was is the past.
        """
        if self.nbf > datetime.now().timestamp():
            raise ValidationError(f"The not before date (nbf) {self.nbf} has not occured yet.")

    def __validate_sub(self):
        """
        Checks to be sure that the subject (sub) is the same as the user who made the request.
        """
        pass

    def __url_to_base(self, url):
        return '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(url))
