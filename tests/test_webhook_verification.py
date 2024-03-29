import pytest
from pytest import param

from spylib import webhook
from spylib.constants import UTF8ENCODING

API_SECRET = 'secret'
MESSAGE = 'message'
VALID_HMAC = 'i19IcCmVwVmMVz2x4hhmqbgl1KeU0WnXBgoDYFeWNgs='
INVALID_HMAC = 'hmac'

params = [
    param(API_SECRET, MESSAGE, VALID_HMAC, True, id='hmac is valid'),
    param(
        API_SECRET,
        bytes(MESSAGE, UTF8ENCODING),
        VALID_HMAC,
        True,
        id='hmac is valid with data in bytes',
    ),
    param(API_SECRET, MESSAGE, INVALID_HMAC, False, id='hmac is invalid'),
]


@pytest.mark.parametrize('api_secret,data, hmac_header, expected_is_valid', params)
def test_is_webhook_valid(api_secret, data, hmac_header, expected_is_valid):
    is_valid = webhook.validate(data=data, hmac_header=hmac_header, api_secret_key=api_secret)
    assert is_valid is expected_is_valid
