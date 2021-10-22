from datetime import datetime
from urllib import parse

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
async def test_app_proxy(url: str):
    app = FastAPI()

    app.add_middleware(CheckAppProxy, secret=API_SECRET, proxy_endpoint='/api/')

    @app.get("/api/")
    async def test():
        return True

    client = TestClient(app)

    response = client.get(url)

    assert response.status_code == 200
    assert bool(response.text) is True


@pytest.mark.parametrize(
    "parameter,value",
    [
        ('shop', 'random-name'),
        ('path_prefix', '/random_path/'),
        ('timestamp', '1'),
    ],
    ids=['Altered shop', 'Altered shop prefix', 'Altered timestamp'],
)
@pytest.mark.asyncio
async def test_altered_hmac(url: str, parameter, value):
    app = FastAPI()

    app.add_middleware(CheckAppProxy, secret=API_SECRET, proxy_endpoint='/api/')

    @app.get("/api/")
    async def test():
        return True

    client = TestClient(app)

    parsed = parse.urlsplit(url)
    query = parse.parse_qs(parsed.query)
    query[parameter] = value
    encoded_query = parse.urlencode(query)
    parsed = parsed._replace(query=encoded_query)

    response = client.get(parsed.geturl())

    assert response.status_code == 400
