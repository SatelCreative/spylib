from typing import Optional

from ..utils import JWTBaseModel


class OAuthJWT(JWTBaseModel):
    is_login: bool
    storename: str
    nonce: Optional[str] = None
