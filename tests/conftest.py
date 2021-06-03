from asyncio import get_event_loop
from os import environ

import nest_asyncio  # type: ignore
from pytest import fixture

nest_asyncio.apply()

environ['SHOPIFY_API_KEY'] = 'API_KEY'
environ['SHOPIFY_SECRET_KEY'] = 'SECRET_KEY'
environ['SHOPIFY_handle'] = 'HANDLE'


@fixture()
def event_loop():
    """Prevent errors where two coroutines are in different loops by never closing the loop"""
    loop = get_event_loop()
    yield loop
