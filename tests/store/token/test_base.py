import pytest

from ..shared import TestStore


@pytest.mark.asyncio
async def test_online_happypath():
    """
    This checks to see if the Store object has been initialized with the proper
    information for the online token.
    """

    # We first save the token
    TestStore.save_online_token(store_name='test-store', key='123')

    store = TestStore.load(store_name='test-store', staff_id=1)

    assert store.staff_id == 1
    assert store.store_name == 'test-store'
    assert store.access_token == '123'


@pytest.mark.asyncio
async def test_offline_happypath():
    """
    This checks to see if the Store object has been initialized with the proper
    information for an offline token.
    """
    # We first save the token
    TestStore.save_offline_token(store_name='test-store', key='123')

    store = TestStore.load(store_name='test-store')

    assert store.store_name == 'test-store'
    assert store.access_token == '123'
    assert not hasattr(store, 'staff_id')
