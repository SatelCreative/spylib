from copy import deepcopy
import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode
from pydantic.main import BaseModel
from pydantic.networks import HttpUrl

import pytest
import hmac
import hashlib
from spylib.oauth.validations import (
    validate_hmac,
    validate_callback,
    TimestampException,
    HMACException,
)
from spylib.utils import StoreNameException

from spylib.oauth.tokens import OAuthJWT

from spylib.utils.misc import get_unique_id

from ..token_classes import online_token_data, test_information

import json


class InitialRedirectQuery(BaseModel):
    client_id: str
    scope: str
    redirect_uri: str
    state: str
    grant_options: str = '[]='


class AuthRedirectQuery(BaseModel):
    shop: str
    state: str
    timestamp: int
    code: str
    hmac: Optional[str] = None


INITIAL_REDIRECT_QUERY = InitialRedirectQuery(
    client_id=test_information.client_id,
    scope=online_token_data.scope,
    redirect_uri=f'https://{test_information.public_domain}/api/callback',
    state=OAuthJWT(
        is_login=False,
        storename=test_information.store_name,
        nonce=get_unique_id(),
    ).encode_token(key=test_information.private_key),
)


TIMESTAMP = int(datetime.datetime.now(datetime.timezone.utc).timestamp())


QUERY_STRING = AuthRedirectQuery(
    shop=f'https://{test_information.store_name}.myshopify.com',
    state=INITIAL_REDIRECT_QUERY.state,
    timestamp=TIMESTAMP,
    code=test_information.code,
)

QUERY_STRING_HMAC = hmac.new(
    test_information.client_secret.encode('utf-8'),
    QUERY_STRING.json(exclude_none=True).encode('utf-8'),
    hashlib.sha256,
).hexdigest()

QUERY_STRING.hmac = QUERY_STRING_HMAC


@pytest.mark.asyncio
async def test_validate_hmac():
    assert validate_hmac(secret=test_information.client_secret, message=QUERY_STRING.dict())


@pytest.mark.parametrize(
    'hmac',
    [(''), ('RANDOM')],
    ids=['Empty HMAC', 'Random HMAC'],
)
@pytest.mark.asyncio
async def test_invalid_validate_hmac(hmac):
    query_string = deepcopy(QUERY_STRING)
    query_string.hmac = hmac
    with pytest.raises(HMACException):
        assert validate_hmac(secret=test_information.client_secret, message=query_string.dict())


@pytest.mark.asyncio
async def test_validate_callback():
    assert (
        validate_callback(
            QUERY_STRING.shop,
            QUERY_STRING.timestamp,
            urlencode(QUERY_STRING.dict(), safe='=,&/[]:').encode('utf-8'),
            test_information.client_secret,
        )
        is None
    )


@pytest.mark.parametrize(
    'param,value,exception',
    [
        ('shop', 'random.notshopify.com', StoreNameException),
        ('timestamp', 100, TimestampException),
        ('hmac', '1', HMACException),
    ],
    ids=['Invalid Store Name', 'Invalid Timestamp', 'Invalid HMAC'],
)
@pytest.mark.asyncio
async def test_invalid_validate_callback(param, value, exception):
    query_string = QUERY_STRING.dict()
    query_string[param] = value
    with pytest.raises(exception):
        validate_callback(
            query_string['shop'],
            query_string['timestamp'],
            urlencode(query_string, safe='=,&/[]:').encode('utf-8'),
            test_information.client_secret,
        )
