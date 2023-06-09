from spylib.fastapi import webhook_hmac

API_SECRET = 'secret'
MESSAGE = 'message'
VALID_HMAC = 'i19IcCmVwVmMVz2x4hhmqbgl1KeU0WnXBgoDYFeWNgs='
INVALID_HMAC = 'hmac'


def test_webhook_hmac_api_secret_missing(client):
    response = client.post('/webhook_hmac')
    assert response.status_code == 403
    assert response.json() == {'detail': 'api_secret_key must be set'}


def test_webhook_hmac_valid(client):
    webhook_hmac.api_secret_key = API_SECRET
    response = client.post(
        '/webhook_hmac', headers={'X-Shopify-Hmac-Sha256': VALID_HMAC}, data=MESSAGE
    )
    assert response.status_code == 200


def test_webhook_hmac_invalid(client):
    webhook_hmac.api_secret_key = API_SECRET
    response = client.post(
        '/webhook_hmac', headers={'X-Shopify-Hmac-Sha256': INVALID_HMAC}, data=MESSAGE
    )
    assert response.status_code == 401
    assert response.json() == {'detail': 'Webhook HMAC authentication failed'}
