from datetime import datetime, timedelta

import jwt
import pytest

from spylib.utils.session_token import (
    InvalidIssuerError,
    MismatchedHostError,
    SessionToken,
    TokenAuthenticationError,
)

API_KEY = "API_KEY"
API_SECRET = "API_SECRET"
now = datetime.now()


def get_token():
    """
    This function returns the same data over and over again. We don't use a variable
    as the fixtures will share the memory and overwrite the value, even with proper scopes.
    """
    return {
        "iss": "https://test.myshopify.com/admin",
        "dest": "https://test.myshopify.com",
        "aud": API_KEY,
        "sub": 1,
        "exp": (now + timedelta(0, 60)).timestamp(),
        "nbf": (now - timedelta(0, 60)).timestamp(),
        "iat": now.timestamp(),
        "jti": 123,
        "sid": "abc123",
    }


@pytest.fixture(scope='function', autouse=False)
def token():
    return get_token()


def generate_auth_header(token):
    return f'Bearer {jwt.encode(token, API_SECRET, algorithm="HS256")}'


@pytest.mark.asyncio
async def test_session_token(token):
    valid_auth_header = generate_auth_header(token)
    session_token = SessionToken.decode_token_from_header(valid_auth_header, API_KEY, API_SECRET)

    assert session_token.dict() == token


@pytest.mark.asyncio
async def test_invalid_header():
    with pytest.raises(TokenAuthenticationError):
        SessionToken.decode_token_from_header('', API_KEY, API_SECRET)


@pytest.mark.asyncio
async def test_invalid_signature(token):
    header = f'Bearer {jwt.encode(token, "invalid_secret", algorithm="HS256")}'
    with pytest.raises(jwt.InvalidSignatureError):
        SessionToken.decode_token_from_header(header, API_KEY, API_SECRET)


@pytest.mark.asyncio
async def test_invalid_hostname(token):
    token['iss'] = 'https://someinvalidhost.com'
    header = generate_auth_header(token)
    with pytest.raises(InvalidIssuerError):
        SessionToken.decode_token_from_header(header, API_KEY, API_SECRET)


@pytest.mark.asyncio
async def test_invalid_destination(token):
    token['iss'] = 'https://someinvalidhost.myshopify.com/'
    header = generate_auth_header(token)
    with pytest.raises(MismatchedHostError):
        SessionToken.decode_token_from_header(header, API_KEY, API_SECRET)


@pytest.mark.asyncio
async def test_invalid_not_before(token):
    token['nbf'] = (datetime.now() + timedelta(0, 60)).timestamp()
    header = generate_auth_header(token)
    with pytest.raises(jwt.ImmatureSignatureError):
        SessionToken.decode_token_from_header(header, API_KEY, API_SECRET)


@pytest.mark.asyncio
async def test_invalid_expiry(token):
    token['exp'] = (datetime.now() - timedelta(0, 60)).timestamp()
    header = generate_auth_header(token)
    with pytest.raises(jwt.ExpiredSignatureError):
        SessionToken.decode_token_from_header(header, API_KEY, API_SECRET)


@pytest.mark.asyncio
async def test_invalid_audience(token):
    token['aud'] = 'some_invalid_audience'
    header = generate_auth_header(token)
    with pytest.raises(jwt.InvalidAudienceError):
        SessionToken.decode_token_from_header(header, API_KEY, API_SECRET)
