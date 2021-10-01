from datetime import datetime, timedelta

import jwt
import pytest

from spylib.utils.session_token import (
    InvalidIssuerError,
    MismatchedHostError,
    SessionToken,
    TokenAuthenticationError,
)

api_key = "API_KEY"
api_secret = "API_SECRET"
now = datetime.now()


def get_token():
    """
    This function returns the same data over and over again. We don't use a variable
    as the fixtures will share the memory and overwrite the value, even with proper scopes.
    """
    return {
        "iss": "https://test.myshopify.com/admin",
        "dest": "https://test.myshopify.com",
        "aud": api_key,
        "sub": 1,
        "exp": (now + timedelta(0, 60)).timestamp(),
        "nbf": (now - timedelta(0, 60)).timestamp(),
        "iat": now.timestamp(),
        "jti": 123,
        "sid": "abc123",
    }


@pytest.fixture(scope='function', autouse=False)
def token_structure():
    return get_token()


def generate_auth_header(token):
    return f'Bearer {jwt.encode(token, api_secret, algorithm="HS256")}'


@pytest.fixture(scope='function', autouse=False)
def valid_auth_header():
    return generate_auth_header(get_token())


@pytest.mark.asyncio
async def test_session_token(valid_auth_header):
    session_token = SessionToken.decode_token_from_header(valid_auth_header, api_key, api_secret)

    token = get_token()

    assert session_token.iss == token['iss']
    assert session_token.dest == token['dest']
    assert session_token.aud == token['aud']
    assert session_token.sub == token['sub']
    assert session_token.exp == token['exp']
    assert session_token.nbf == token['nbf']
    assert session_token.iat == token['iat']
    assert session_token.jti == token['jti']
    assert session_token.sid == token['sid']


@pytest.mark.asyncio
async def test_invalid_header(token_structure):
    with pytest.raises(TokenAuthenticationError):
        SessionToken.decode_token_from_header('', api_key, api_secret)


@pytest.mark.asyncio
async def test_invalid_signature(token_structure):
    header = f'Bearer {jwt.encode(token_structure, "invalid_secret", algorithm="HS256")}'
    with pytest.raises(jwt.InvalidSignatureError):
        SessionToken.decode_token_from_header(header, api_key, api_secret)


@pytest.mark.asyncio
async def test_invalid_hostname(token_structure):
    token_structure['iss'] = 'https://someinvalidhost.com'
    header = generate_auth_header(token_structure)
    with pytest.raises(InvalidIssuerError):
        SessionToken.decode_token_from_header(header, api_key, api_secret)


@pytest.mark.asyncio
async def test_invalid_destination(token_structure):
    token_structure['iss'] = 'https://someinvalidhost.myshopify.com/'
    header = generate_auth_header(token_structure)
    with pytest.raises(MismatchedHostError):
        SessionToken.decode_token_from_header(header, api_key, api_secret)


@pytest.mark.asyncio
async def test_invalid_not_before(token_structure):
    token_structure['nbf'] = (datetime.now() + timedelta(0, 60)).timestamp()
    header = generate_auth_header(token_structure)
    with pytest.raises(jwt.ImmatureSignatureError):
        SessionToken.decode_token_from_header(header, api_key, api_secret)


@pytest.mark.asyncio
async def test_invalid_expiry(token_structure):
    token_structure['exp'] = (datetime.now() - timedelta(0, 60)).timestamp()
    header = generate_auth_header(token_structure)
    with pytest.raises(jwt.ExpiredSignatureError):
        SessionToken.decode_token_from_header(header, api_key, api_secret)


@pytest.mark.asyncio
async def test_invalid_audience(token_structure):
    token_structure['aud'] = 'some_invalid_audience'
    header = generate_auth_header(token_structure)
    with pytest.raises(jwt.InvalidAudienceError):
        SessionToken.decode_token_from_header(header, api_key, api_secret)
