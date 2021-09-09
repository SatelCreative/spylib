from __future__ import annotations

from spylib.token import OfflineTokenABC, OfflineTokenResponse, OnlineTokenABC, OnlineTokenResponse
from pydantic import validator
from pydantic.dataclasses import dataclass


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


# Constants
api_version = '2021-04'
store_name = "Test-Store"
client_id = 1
client_secret = 2
code = 3
app_scopes = ['write_products', 'read_customers']
user_scopes = ['write_orders', 'read_products']
public_domain = 'test.testing.com'
private_key = 'TESTPRIVATEKEY'

offline_token_data = OfflineTokenResponse(
    access_token='OFFLINETOKEN',
    scope=','.join(app_scopes),
)

online_token_data = OnlineTokenResponse(
    access_token='ONLINETOKEN',
    scope=','.join(app_scopes),
    expires_in=86399,
    associated_user_scope=','.join(user_scopes),
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


# Defining the object and database
database = {
    "offline": {},
    "online": {},
}


class OnlineToken(OnlineTokenABC):
    async def save_token(self):
        database['online'][self.store_name] = {}
        database['online'][self.store_name][self.associated_user.id] = self

    @classmethod
    async def load_token(cls, store_name: str, user_id: str) -> OnlineToken:
        return database['online'][store_name][user_id]


class OfflineToken(OfflineTokenABC):
    async def save_token(self):
        database['offline'][self.store_name] = self

    @classmethod
    async def load_token(cls, store_name: str) -> OfflineToken:
        return database['offline'][store_name]
