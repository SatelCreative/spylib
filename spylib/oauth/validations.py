from copy import deepcopy
from operator import itemgetter
from typing import Any, List, Tuple
from urllib.parse import parse_qsl

from ..utils import domain_to_storename, now_epoch
from ..utils import validate as validate_hmac
from .config import conf
from .tokens import OAuthJWT


def validate_callback(shop: str, timestamp: int, query_string: Any) -> None:
    q_str = query_string.decode('utf-8')
    # 1) Check that the shop is a valid Shopify URL
    domain_to_storename(shop)

    # 2) Check the timestamp. Must not be more than 5min old
    if now_epoch() - timestamp > 300:
        raise ValueError('Timestamp is too old')

    # 3) Check the hmac
    # Extract HMAC
    args = parse_qsl(q_str)
    original_args = deepcopy(args)
    try:
        # Let's assume alphabetical sorting to avoid issues with scrambled args when using bonnette
        args.sort(key=itemgetter(0))
        validate_callback_args(args=args)
    except ValueError:
        # Try with the original ordering
        validate_callback_args(args=original_args)


def validate_callback_args(args: List[Tuple[str, str]]) -> None:
    # We assume here that the arguments were validated prior to calling
    # this function.
    hmac_arg = [arg[1] for arg in args if arg[0] == 'hmac'][0]
    message = '&'.join([f'{arg[0]}={arg[1]}' for arg in args if arg[0] != 'hmac'])
    # Check HMAC
    validate_hmac(secret=conf.secret_key, sent_hmac=hmac_arg, message=message)


def validate_oauthjwt(token: str, shop: str, jwt_key: str) -> OAuthJWT:
    oauthjwt = OAuthJWT.decode_token(token=token, key=jwt_key)

    storename = domain_to_storename(shop)
    if oauthjwt.storename != storename:
        raise ValueError("Token storename and query shop don't match")

    return oauthjwt
