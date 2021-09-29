from datetime import datetime, timedelta

import jwt
import pytest

from spylib.utils.session_token import SessionToken

api_key = "API_KEY"
api_secret = "API_SECRET"
token = {
    "iss": "https://test.myshopify.com/admin",
    "dest": "https://test.myshopify.com",
    "aud": api_key,
    "sub": 1,
    "exp": (datetime.now() + timedelta(0, 60)).timestamp(),
    "nbf": datetime.now().timestamp(),
    "iat": datetime.now().timestamp(),
    "jti": 123,
    "sid": "abc123",
}


@pytest.fixture(scope='session', autouse=True)
def auth_header():
    return f'Bearer {jwt.encode(token, api_secret, algorithm="HS256")}'


@pytest.mark.asyncio
async def test_session_token(auth_header):
    session_token = SessionToken.decode_token_from_header(auth_header, api_key, api_secret)

    assert session_token.iss == token['iss']
    assert session_token.dest == token['dest']
    assert session_token.aud == token['aud']
    assert session_token.sub == token['sub']
    assert session_token.exp == token['exp']
    assert session_token.nbf == token['nbf']
    assert session_token.iat == token['iat']
    assert session_token.jti == token['jti']
    assert session_token.sid == token['sid']
