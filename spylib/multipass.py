import datetime
import json
from base64 import urlsafe_b64encode
from typing import Any, Dict

from Crypto.Cipher import AES
from Crypto.Hash import HMAC, SHA256
from Crypto.Random import get_random_bytes


def generate_token(secret: str, contact_raw_data: Dict[str, Any]) -> bytes:
    key = SHA256.new(secret.encode('utf-8')).digest()
    encryption_key = key[0:16]
    signature_key = key[16:32]

    contact_raw_data['created_at'] = datetime.datetime.utcnow().isoformat()
    cypher_text = _encrypt(encryption_key, json.dumps(contact_raw_data))
    return urlsafe_b64encode(cypher_text + _sign(signature_key, cypher_text))


def generate_url(secret: str, contact_raw_data: Dict[str, Any], url) -> str:
    token = generate_token(secret, contact_raw_data).decode('utf-8')
    return f'{url}/account/login/multipass/{token}'


def _encrypt(encryption_key, plainText) -> bytes:
    plainText = _pad(plainText)
    iv = get_random_bytes(AES.block_size)
    cipher = AES.new(encryption_key, AES.MODE_CBC, iv)
    return iv + cipher.encrypt(str.encode(plainText))


def _sign(signature_key, secret):
    return HMAC.new(signature_key, secret, SHA256).digest()


def _pad(s):
    return s + (AES.block_size - len(s) % AES.block_size) * chr(
        AES.block_size - len(s) % AES.block_size
    )