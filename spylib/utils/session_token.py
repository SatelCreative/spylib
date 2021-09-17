
from typing import ClassVar, Optional
from pydantic.main import BaseModel
from pydantic.networks import HttpUrl

import jwt
from jwt.exceptions import PyJWKError

from utils.domain import store_domain

class InvalidIssuerError(Exception):
    pass

class MismatchedHostError(Exception):
    pass

class TokenAuthenticationError(Exception):
    pass

class SessionToken(BaseModel):

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

    class Config:
        arbitrary_types_allowed = True


    def validate(self) -> None:
        self.__validate_hostname()
        self.__validate_destination()
    
    @classmethod
    def decode_token_from_header(cls, authorization_header, api_key, secret) -> SessionToken:
        # Take the authorization headers and unload them
        token = cls.__extract_session_token(authorization_header)
        payload = cls.__decode_session_token(token, api_key, secret)
        
        # Verify enough fields specified and validate data 
        session_token = cls(**payload)
        session_token.validate()
        
        return session_token

    @classmethod
    def __extract_session_token(cls, authorization_header: str) -> str:
        if not authorization_header.startswith(cls.prefix):
            raise TokenAuthenticationError("The authorization header does not contain a Bearer token.")
        return authorization_header[len(cls.prefix):]

    @classmethod
    def __decode_session_token(cls, session_token: str, api_key: str, secret: str):
        try:
            return jwt.decode(
                session_token,
                secret,
                audience=api_key,
                algorithms=[cls.algorithm]
            )
        except PyJWKError as e:
            raise e("Error decoding session token")

    def __validate_destination(self):
        if self.iss != self.dest:
            raise MismatchedHostError(f"The issuer {self.iss} does not match the destination {self.dest}")

    def __validate_hostname(self):
        if not store_domain(self.iss):
            raise InvalidIssuerError(f"The domain {self.iss} is not a valid issuer.")

    
