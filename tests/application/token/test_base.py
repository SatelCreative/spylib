import pytest

from spylib.store import Store


@pytest.mark.asyncio
async def test_online_happypath():
    """
    This checks to see if the Store object has been initialized with the proper
    information for the online token.
    """

    # We first save the token
    store = Store(store_name='test-store')
    await store.add_online_token(token='123', associated_user=1, expires_in=10000)

    assert store.store_name == 'test-store'
    assert 1 in store.online_access_tokens
    assert store.online_access_tokens[1].access_token == "123"
    assert store.online_access_tokens[1].associated_user == 1


@pytest.mark.asyncio
async def test_offline_happypath():
    """
    This checks to see if the Store object has been initialized with the proper
    information for an offline token.
    """
    # We first save the token
    store = Store(store_name='test-store')
    await store.add_offline_token(token='123')

    assert store.store_name == 'test-store'
    assert store.offline_access_token.access_token == "123"
