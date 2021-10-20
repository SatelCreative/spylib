from __future__ import annotations
from hmac import compare_digest
from typing import Any, Dict

from pydantic import BaseModel
from pydantic.networks import HttpUrl

from urllib import parse

from utils.hmac import calculate_message_hmac


class AppProxy(BaseModel):

    shop: HttpUrl
    path_prefix: str
    timestamp: float
    signature: str
    parameters: str

    @classmethod
    def decode_message(
        cls,
        message: str,
        secret: str,
    ) -> AppProxy:

        # Take the authorization headers and unload them
        decoded_message = cls.__extract_proxy_message(message)

        real_signature = decoded_message.pop('signature')[0]
        body = '&'.join([f'{arg}={",".join(message.get(arg))}' for arg in message.keys()])

        message_signature = calculate_message_hmac(secret, body)

        # Validate that the message HMAC and recieved HMAC are the same.
        if not compare_digest(real_signature, message_signature):
            raise ValueError('HMAC verification failed')

        # Verify enough fields specified
        proxy_message = cls.parse_obj(decoded_message)

        return proxy_message

    @classmethod
    def __extract_proxy_message(cls, message: str) -> Dict[str, Any]:
        return parse.parse_qs(parse.urlsplit(message))
