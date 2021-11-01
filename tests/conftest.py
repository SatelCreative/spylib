from asyncio import get_event_loop

import nest_asyncio  # type: ignore
from pytest import fixture

nest_asyncio.apply()


@fixture()
def event_loop():
    """Prevent errors where two coroutines are in different loops by never closing the loop"""
    loop = get_event_loop()
    yield loop
