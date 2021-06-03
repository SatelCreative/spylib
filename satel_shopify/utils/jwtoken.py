from typing import Optional, Tuple

import jwt
from pydantic import BaseModel, validator

from .misc import now_epoch


class JWTBaseModel(BaseModel):
    """Base class to manage JWT

    The pydantic model fields are the data content of the JWT.
    The default expiration (exp) is set to 900 seconds. Overwrite the ClassVar exp to change the
    expiration time.
    """

    exp: int = None  # type: ignore

    @validator('exp', pre=True, always=True)
    def set_id(cls, exp):
        return exp or (now_epoch() + 900)

    @classmethod
    def decode_token(cls, key: str, token: str, verify: bool = True):
        """Decode the token and load the data content into an instance of this class

        Parameters
        ----------
        key: Secret key used to encrypt the JWT
        verify: If true, verify the signature is valid, otherwise skip. Default is True

        Returns
        -------
        Class instance
        """
        data = jwt.decode(token, key, algorithms=['HS256'], verify=verify)
        # Enforce conversion to satisfy typing
        data = dict(data)
        return cls(**data)

    @classmethod
    def decode_hp_s(cls, key: str, header_payload: str, signature: Optional[str] = None):
        """Decode the token provided in the format "header.payload" and signature

        Parameters
        ----------
        key: Secret key used to encrypt the JWT
        signature: If provided, verify the authenticity of the token.

        Returns
        -------
        Class instance
        """
        sig = signature if signature is not None else 'DUMMYSIGNATURE'
        token = header_payload + '.' + sig
        return cls.decode_token(token=token, key=key, verify=(signature is not None))

    def encode_token(self, key: str) -> str:
        """Encode the class data into a JWT and return a string

        Parameters
        ----------
        key: Secret key used to encrypt the JWT

        Returns
        -------
        The JWT as a string
        """
        data = self.dict()
        data['exp'] = self.exp
        return jwt.encode(data, key, algorithm='HS256')

    def encode_hp_s(self, key: str) -> Tuple[str, str]:
        """Encode the class data into a JWT

        Parameters
        ----------
        key: Secret key used to encrypt the JWT

        Returns
        -------
        The JWT in the format "header.payload" and the signature
        """
        token = self.encode_token(key=key)

        header, payload, signature = token.split('.')
        return f'{header}.{payload}', signature

    @property
    def cookie_key(self) -> str:
        """Define the key of the cookie used to store the JWT"""
        raise NotImplementedError
