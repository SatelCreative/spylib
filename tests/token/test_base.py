from unittest.mock import AsyncMock
from spylib import OfflineTokenABC, OnlineTokenABC
import json
from pydantic.dataclasses import dataclass
import pytest


# Constants
store_name = "Test-Store"
associated_user = "Test-User"
client_id = 1
client_secret = 2
code = 3
app_scopes = ['write_products', 'read_customers']
user_scopes = ['write_orders', 'read_products']
public_domain = 'test.testing.com'
private_key = 'TESTPRIVATEKEY'

offline_token_data = dict(
    access_token='OFFLINETOKEN',
    scope=','.join(app_scopes),
)
online_token_data = dict(
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


@dataclass
class MockHTTPResponse:
    status_code: int
    jsondata: dict
    headers: dict = None  # type: ignore

    def json(self):
        return self.jsondata


# Defining the object and database
database = {"offline": {}, "online": {}}


class OnlineToken(OnlineTokenABC):
    async def save_token(self):
        database['online'][self.store_name] = {}
        database['online'][self.store_name][self.associated_user.id] = self

    @classmethod
    async def load_token(cls, store_name, user_id):
        return OnlineToken(**json.loads(database['online'][store_name][user_id]))


class OfflineToken(OfflineTokenABC):
    async def save_token(self):
        pass
        database['offline'][self.store_name] = self

    @classmethod
    async def load_token(cls, store_name: str):
        return OfflineToken(**json.loads(database['offline'][store_name]))


@pytest.mark.asyncio
async def test_token(mocker):

    # Generating the object callback with the token information
    shopify_request_mock = mocker.patch('httpx.AsyncClient.request', new_callable=AsyncMock)
    shopify_request_mock.side_effect = [
        MockHTTPResponse(status_code=200, jsondata=offline_token_data),
        MockHTTPResponse(status_code=200, jsondata=online_token_data),
    ]

    # Create a new token
    offline_token = await OfflineToken.new(
        store_name,
        client_id,
        client_secret,
        code,
    )
    online_token = await OnlineToken.new(
        store_name,
        client_id,
        client_secret,
        code,
    )

    # Save the token
    await offline_token.save_token()
    await online_token.save_token()

    # Load the token
    online_token = OnlineToken.load_token(store_name, associated_user)
    offline_token = OfflineToken.load_token(store_name)
