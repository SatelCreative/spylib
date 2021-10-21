from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from spylib.utils import calculate_message_hmac
from spylib.utils.app_proxy import CheckAppProxy

API_KEY = "API_KEY"
API_SECRET = "API_SECRET"
now = datetime.now()

SHOP = 'test.myshopify.com'
PREFIX = '/apps/api'
TIMESTAMP = "1317327555"


@pytest.fixture(scope='function', autouse=False)
def url():
    params = f'shop={SHOP}&path_prefix={PREFIX}&timestamp={TIMESTAMP}'

    signature = calculate_message_hmac(API_SECRET, params)

    return f'http://testserver/api/?{params}&signature={signature}'


@pytest.mark.asyncio
async def test_session_token(mocker, url: str):
    app = FastAPI()

    app.add_middleware(CheckAppProxy, secret=API_SECRET, proxy_endpoint='/api/')

    @app.get("/api/")
    async def test():
        return True

    client = TestClient(app)

    response = client.get(url)

    assert response.status_code == 200
    assert bool(response.text) is True
