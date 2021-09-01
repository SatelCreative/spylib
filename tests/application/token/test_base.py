import pytest

from spylib.store import Store
from spylib.token import AssociatedUser


@pytest.mark.asyncio
async def test_online_token():
    """
    This checks to see if the Store object has been initialized with the proper
    information for the online token.
    """

    user = AssociatedUser(
        **{
            "id": 902541635,
            "first_name": "John",
            "last_name": "Smith",
            "email": "john@example.com",
            "email_verified": True,
            "account_owner": True,
            "locale": "en",
            "collaborator": False,
        }
    )

    # We first save the token
    store = Store(store_name='test-store')
    await store.add_online_token(token='123', associated_user=user, expires_in=10000)

    assert store.store_name == 'test-store'
    assert user.id in store.online_access_tokens
    assert store.online_access_tokens[user.id].access_token == "123"
    assert store.online_access_tokens[user.id].associated_user == user


@pytest.mark.asyncio
async def test_offline_token():
    """
    This checks to see if the Store object has been initialized with the proper
    information for an offline token.
    """
    # We first save the token
    store = Store(store_name='test-store')
    await store.add_offline_token(token='123')

    assert store.store_name == 'test-store'
    assert store.offline_access_token.access_token == "123"
