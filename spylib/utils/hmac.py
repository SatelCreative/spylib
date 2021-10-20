from base64 import b64encode
from hashlib import sha256
from hmac import compare_digest, new
from typing import Dict


def calculate_message_hmac(secret: str, message: str, is_base64: bool = False) -> str:
    hmac_hash = new(secret.encode('utf-8'), message.encode('utf-8'), sha256)
    if is_base64:
        # TODO fix bytes / str union issue
        return b64encode(hmac_hash.digest()).decode('utf-8')

    return hmac_hash.hexdigest()


def validate_hmac(secret: str, message: Dict[str, list], is_base64: bool = False):

    hmac_actual = message.pop('hmac')[0]
    body = '&'.join([f'{arg}={",".join(message.get(arg))}' for arg in message.keys()])

    message_hmac = calculate_message_hmac(secret, body, is_base64)

    if not compare_digest(hmac_actual, message_hmac):
        raise ValueError('HMAC verification failed')
