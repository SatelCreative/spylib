import jwt
from pydantic import BaseModel, Field

from .misc import now_epoch


class JWTBaseModel(BaseModel):
    """Base class to manage JWT.

    The pydantic model fields are the data content of the JWT.
    The default expiration (exp) is set to 900 seconds. Overwrite the ClassVar exp to change the
    expiration time.
    """

    exp: int = Field(default_factory=lambda: now_epoch() + 900)

    @classmethod
    def decode_token(cls, key: str, token: str, verify: bool = True):
        """Decode the token and load the data content into an instance of this class.

        Args
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

    def encode_token(self, key: str) -> str:
        """Encode the class data into a JWT and return a string.

        Args
        ----------
        key: Secret key used to encrypt the JWT

        Returns
        -------
        The JWT as a string
        """
        data = self.model_dump()
        data['exp'] = self.exp
        return jwt.encode(data, key, algorithm='HS256')
