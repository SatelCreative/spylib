from spylib.token import verify_webhook

API_SECRET = 'secret'
MESSAGE = 'message'
VALID_HMAC = 'i19IcCmVwVmMVz2x4hhmqbgl1KeU0WnXBgoDYFeWNgs='
INVALID_HMAC = 'hmac'


def test_verify_webhook_valid():
    is_valid = verify_webhook(data=MESSAGE, hmac_header=VALID_HMAC, api_secret_key=API_SECRET)
    assert is_valid is True


def test_verify_webhook_invalid():
    is_valid = verify_webhook(data=MESSAGE, hmac_header=INVALID_HMAC, api_secret_key=API_SECRET)
    assert is_valid is False
