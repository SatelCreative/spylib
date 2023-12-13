from datetime import datetime, timedelta
from importlib import util
from sys import modules

import jwt
import pytest
from pydantic import HttpUrl
from starlette.requests import Request

from spylib.session_token import (
    InvalidIssuerError,
    MismatchedHostError,
    SessionToken,
    TokenAuthenticationError,
)

API_KEY = 'API_KEY'
API_SECRET = 'API_SECRET'
now = datetime.now()


def get_token():
    """
    This function returns the same data over and over again. We don't use a variable
    as the fixtures will share the memory and overwrite the value, even with proper scopes.
    """
    return {
        'iss': 'https://test.myshopify.com/admin',
        'dest': 'https://test.myshopify.com',
        'aud': API_KEY,
        'sub': 1,
        'exp': (now + timedelta(0, 60)).timestamp(),
        'nbf': (now - timedelta(0, 60)).timestamp(),
        'iat': now.timestamp(),
        'jti': '3512a085-ee9a-4914-b252-3aabcd1ada14',
        'sid': 'abc123',
    }


@pytest.fixture(scope='function', autouse=False)
def token():
    return get_token()


def generate_auth_header(token):
    return f'Bearer {jwt.encode(token, API_SECRET, algorithm="HS256")}'


@pytest.mark.asyncio
async def test_session_token(token):
    valid_auth_header = generate_auth_header(token)
    session_token = SessionToken.from_header(valid_auth_header, API_KEY, API_SECRET)

    token['iss'] = HttpUrl(token['iss'])
    token['dest'] = HttpUrl(token['dest'])

    assert session_token.model_dump() == token


@pytest.mark.asyncio
async def test_invalid_header():
    with pytest.raises(TokenAuthenticationError):
        SessionToken.from_header('', API_KEY, API_SECRET)


@pytest.mark.asyncio
async def test_invalid_signature(token):
    header = f'Bearer {jwt.encode(token, "invalid_secret", algorithm="HS256")}'
    with pytest.raises(jwt.InvalidSignatureError):
        SessionToken.from_header(header, API_KEY, API_SECRET)


@pytest.mark.parametrize(
    'parameter,value,error',
    [
        ('iss', 'https://someinvalidhost.com', InvalidIssuerError),
        ('iss', 'https://someinvalidhost.myshopify.com/', MismatchedHostError),
        ('nbf', (datetime.now() + timedelta(0, 60)).timestamp(), jwt.ImmatureSignatureError),
        ('exp', (datetime.now() - timedelta(0, 60)).timestamp(), jwt.ExpiredSignatureError),
        ('aud', 'some_invalid_audience', jwt.InvalidAudienceError),
    ],
    ids=['Invalid ISS', 'Mismatched host', 'NBF in future', 'EXP in past', 'Wrong audience'],
)
@pytest.mark.asyncio
async def test_invalid_token_parameters(token, parameter, value, error):
    token[parameter] = value
    header = generate_auth_header(token)
    with pytest.raises(error):
        SessionToken.from_header(header, API_KEY, API_SECRET)


def parse_session_token(request: Request):
    SessionToken.from_header(request.headers.get('Authorization', ''), API_KEY, API_SECRET)


@pytest.mark.asyncio
async def test_depends(token):
    if 'fastapi' not in modules and util.find_spec('fastapi') is None:
        return

    from fastapi import Depends, FastAPI  # type: ignore
    from fastapi.testclient import TestClient  # type: ignore

    app = FastAPI()

    @app.get('/token')
    async def token_endpoint(token: SessionToken = Depends(parse_session_token)):
        return token

    client = TestClient(app=app)

    header = generate_auth_header(token)

    client.get('/token', headers={'Authorization': header})
