import datetime
import json
from base64 import urlsafe_b64encode
from typing import Any, Dict

from Crypto.Cipher import AES
from Crypto.Hash import HMAC, SHA256
from Crypto.Random import get_random_bytes


class Multipass:
    def __init__(self, secret):
        key = SHA256.new(secret.encode('utf-8')).digest()
        self.encryption_key = key[0:16]
        self.signature_key = key[16:32]

    def generate_token(self, contact_raw_data: Dict[str, Any]) -> str:
        contact_raw_data['created_at'] = datetime.datetime.utcnow().isoformat()
        cypher_text = self.encrypt(json.dumps(contact_raw_data))
        return urlsafe_b64encode(cypher_text + self.sign(cypher_text))

    def generate_url(self, contact_raw_data: Dict[str, Any], url) -> str:
        token = self.generate_token(contact_raw_data).decode('utf-8')
        return '{0}/account/login/multipass/{1}'.format(url, token)

    def encrypt(self, plainText) -> bytes:
        plainText = self.pad(plainText)
        iv = get_random_bytes(AES.block_size)
        cipher = AES.new(self.encryption_key, AES.MODE_CBC, iv)
        return iv + cipher.encrypt(str.encode(plainText))

    def sign(self, secret):
        return HMAC.new(self.signature_key, secret, SHA256).digest()

    def pad(self, s):
        return s + (AES.block_size - len(s) % AES.block_size) * chr(
            AES.block_size - len(s) % AES.block_size
        )
