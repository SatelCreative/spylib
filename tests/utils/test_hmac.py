from copy import deepcopy
from hmac import compare_digest

import pytest

from spylib.utils.hmac import (
    calculate_from_components,
    calculate_from_message,
    validate,
)

API_KEY = 'API_KEY'
API_SECRET = 'API_SECRET'
MESSAGE = 'test'
HMAC = '5bed91cf26169e535628d92924b28554649451aa7c005e40b5614d71b7f4d2d1'

COMPONENTS = {
    'datetime': '1637865391.929965',
    'path': "https://host.myshopify.com/",
    'query_string': "val=val",
    'body': "",
    'secret': API_SECRET,
}

COMPONENTS_HMAC = "e570623dce50171e5f4d29e03f422d5abb90f4a7d13947b9b57da153766d480e"


@pytest.mark.asyncio
async def test_calculate_from_message():
    assert compare_digest(HMAC, calculate_from_message(API_SECRET, message=MESSAGE))


@pytest.mark.parametrize(
    'message',
    [(''), ('RANDOM')],
    ids=['Empty', 'Random'],
)
@pytest.mark.asyncio
async def test_invalid_calculate_from_message(message):
    assert not compare_digest(HMAC, calculate_from_message(API_SECRET, message=message))


@pytest.mark.asyncio
async def test_calculate_from_components():
    assert compare_digest(COMPONENTS_HMAC, calculate_from_components(**COMPONENTS))


@pytest.mark.parametrize(
    'param,value',
    [
        ('datetime', '1637865391.929966'),
        ('path', 'https://invalidhost.myshopify.com/'),
        ('query_string', 'val=notval'),
        ('body', 'some data in our body'),
    ],
    ids=['Invalid Datetime', 'Invalid Path', 'Invalid Query String', 'Invalid Body'],
)
@pytest.mark.asyncio
async def test_invalid_calculate_from_components(param, value):
    components = deepcopy(COMPONENTS)
    components[param] = value
    assert not compare_digest(COMPONENTS_HMAC, calculate_from_components(**components))


@pytest.mark.asyncio
async def test_validate():
    assert not validate(secret=API_SECRET, sent_hmac=HMAC, message=MESSAGE)


@pytest.mark.parametrize(
    'message',
    [(''), ('RANDOM')],
    ids=['Empty', 'Random'],
)
@pytest.mark.asyncio
async def test_invalid_validate(message):
    with pytest.raises(ValueError):
        assert validate(secret=API_SECRET, sent_hmac=HMAC, message=message)
