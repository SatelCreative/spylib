def test_webhook_hmac_api_secret_missing(client):
    response = client.get('/webhook_hmac')
    assert response.status_code == 403
    assert response.json() == {'detail': 'api_secret_key must be set'}
