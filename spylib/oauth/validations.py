from hmac import compare_digest
from typing import Dict
from urllib.parse import parse_qs

import hmac
import hashlib

from ..utils import domain_to_storename, now_epoch, StoreNameException
from .tokens import OAuthJWT


class TimestampException(ValueError):
    pass


class HMACException(ValueError):
    pass


def validate_callback(shop: str, timestamp: int, query_string: bytes, api_secret_key: str) -> None:
    # 1) Check that the shop is a valid Shopify URL
    domain_to_storename(shop)

    # 2) Check the timestamp. Must not be more than 5min old
    if now_epoch() - timestamp > 300:
        raise TimestampException('Timestamp is too old')

    # 3) Check the hmac
    message = parse_qs(query_string.decode('utf-8'))
    if not validate_hmac(secret=api_secret_key, message=message):
        raise HMACException('HMAC not valid')


def validate_oauthjwt(token: str, shop: str, jwt_key: str) -> OAuthJWT:
    oauthjwt = OAuthJWT.decode_token(token=token, key=jwt_key)

    storename = domain_to_storename(shop)
    if oauthjwt.storename != storename:
        raise StoreNameException("Token storename and query shop don't match")

    return oauthjwt


def validate_hmac(secret: str, message: Dict[str, list]) -> bool:
    """
    Checks to see if the hmac for a str is valid.
    """

    hmac_actual = message.pop('hmac')
    message_str = '&'.join([f'{arg}={",".join(message[arg])}' for arg in message.keys()])
    message_hmac = hmac.new(
        secret.encode('utf-8'), message_str.encode('utf-8'), hashlib.sha256
    ).hexdigest()

    return compare_digest(hmac_actual, message_hmac)
