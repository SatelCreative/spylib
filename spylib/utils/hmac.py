from base64 import b64encode
from hashlib import sha256
from hmac import compare_digest, new


def calculate_hmac_from_message(secret: str, message: str, is_base64: bool = False) -> str:
    hmac_hash = new(secret.encode('utf-8'), message.encode('utf-8'), sha256)
    if is_base64:
        # TODO fix bytes / str union issue
        return b64encode(hmac_hash.digest()).decode('utf-8')

    return hmac_hash.hexdigest()

def validate_hmac(secret: str, sent_hmac: str, message: str, is_base64: bool = False):

    hmac_calculated = calculate_hmac_from_message(secret, message, is_base64)

    if not compare_digest(sent_hmac, hmac_calculated):
        raise ValueError('HMAC verification failed')