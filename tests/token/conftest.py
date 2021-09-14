from __future__ import annotations

import pytest
from pydantic import validator
from pydantic.dataclasses import dataclass
from pydantic.main import BaseModel

from spylib.token import (
    OfflineTokenABC,
    OfflineTokenResponse,
    OnlineTokenABC,
    OnlineTokenResponse,
)

database = {
    "online": {},
    "offline": {},
}


# These are the fixtures for the subdirectories


@pytest.fixture(scope='session', autouse=True)
def database():
    return database


@pytest.fixture(scope='session', autouse=True)
def OnlineToken():
    global database
    database = {"offline": {}, "online": {}}

    class OnlineToken(OnlineTokenABC):
        async def save_token(self):
            database['online'][self.store_name] = {}
            database['online'][self.store_name][self.associated_user.id] = self

        @classmethod
        async def load_token(cls, store_name: str, user_id: str) -> OnlineToken:
            return database['online'][store_name][user_id]

    yield OnlineToken

    database = {"offline": {}, "online": {}}


@pytest.fixture(scope='session', autouse=True)
def OfflineToken():
    global database
    database = {"offline": {}, "online": {}}

    class OfflineToken(OfflineTokenABC):
        async def save_token(self):
            database['offline'][self.store_name] = self

        @classmethod
        async def load_token(cls, store_name: str) -> OfflineToken:
            return database['offline'][store_name]

    yield OfflineToken

    database = {"offline": {}, "online": {}}


@pytest.fixture(scope='session', autouse=True)
def online_token_data() -> OnlineTokenResponse:
    return OnlineTokenResponse(
        access_token='ONLINETOKEN',
        scope=','.join(['write_products', 'read_customers']),
        expires_in=86399,
        associated_user_scope=','.join(['write_orders', 'read_products']),
        associated_user={
            "id": 902541635,
            "first_name": "John",
            "last_name": "Smith",
            "email": "john@example.com",
            "email_verified": True,
            "account_owner": True,
            "locale": "en",
            "collaborator": False,
        },
    )


@pytest.fixture(scope='session', autouse=True)
def offline_token_data() -> OnlineTokenResponse:
    return OfflineTokenResponse(
        access_token='OFFLINETOKEN',
        scope=','.join(['write_products', 'read_customers']),
    )


class AppInformation(BaseModel):
    """
    Information about the store for tests.
    """

    api_version: str = '2021-04'
    store_name: str = "Test-Store"
    client_id: int = 1
    client_secret: int = 2
    code: int = 3
    public_domain: str = 'test.testing.com'
    private_key: str = 'TESTPRIVATEKEY'


@pytest.fixture(scope='session', autouse=True)
def app_information() -> AppInformation:
    return AppInformation()


@pytest.fixture(scope='session', autouse=True)
def MockHTTPResponse():
    @dataclass
    class MockHTTPResponse:
        status_code: int
        jsondata: dict
        headers: dict = None  # type: ignore

        @validator('headers', pre=True, always=True)
        def set_id(cls, fld):
            return fld or {'X-Shopify-Shop-Api-Call-Limit': '39/40'}

        def json(self):
            return self.jsondata

    return MockHTTPResponse
