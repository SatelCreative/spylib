from urllib.parse import parse_qs

from ..utils import domain_to_storename, now_epoch
from ..utils import validate_hmac
from .config import conf
from .tokens import OAuthJWT


def validate_callback(shop: str, timestamp: int, query_string: bytes) -> None:
    # 1) Check that the shop is a valid Shopify URL
    domain_to_storename(shop)

    # 2) Check the timestamp. Must not be more than 5min old
    if now_epoch() - timestamp > 300:
        raise ValueError('Timestamp is too old')

    # 3) Check the hmac
    message = parse_qs(query_string.decode('utf-8')) 
    validate_hmac(secret=conf.secret_key, message=message)

def validate_oauthjwt(token: str, shop: str, jwt_key: str) -> OAuthJWT:
    oauthjwt = OAuthJWT.decode_token(token=token, key=jwt_key)

    storename = domain_to_storename(shop)
    if oauthjwt.storename != storename:
        raise ValueError('Token storename and query shop don\'t match')

    return oauthjwt
