from __future__ import annotations

from pydantic.class_validators import validator
from pydantic.main import BaseModel

from spylib.token import (
    OfflineTokenABC,
    OfflineTokenResponse,
    OnlineTokenABC,
    OnlineTokenResponse,
)

online_token_data = OnlineTokenResponse(
    access_token='ONLINETOKEN',
    scope=','.join(['write_products', 'read_customers']),
    expires_in=86399,
    associated_user_scope=','.join(['read_products']),
    associated_user={
        'id': 902541635,
        'first_name': 'John',
        'last_name': 'Smith',
        'email': 'john@example.com',
        'email_verified': True,
        'account_owner': True,
        'locale': 'en',
        'collaborator': False,
    },
)

offline_token_data = OfflineTokenResponse(
    access_token='OFFLINETOKEN',
    scope=','.join(['write_products', 'read_customers']),
)


class MockHTTPResponse(BaseModel):
    status_code: int
    jsondata: dict
    headers: dict = None  # type: ignore

    @validator('headers', pre=True, always=True)
    def set_id(cls, fld):
        return fld or {'X-Shopify-Shop-Api-Call-Limit': '39/40'}

    def json(self):
        return self.jsondata


class TestInformation(BaseModel):
    """
    Information about the store for tests.
    """

    api_version: str = '2021-04'
    store_name: str = 'Test-Store'
    client_id: int = 1
    client_secret: int = 2
    code: int = 3
    public_domain: str = 'test.testing.com'
    private_key: str = 'TESTPRIVATEKEY'


test_information = TestInformation()


class OnlineToken(OnlineTokenABC):
    async def save(self):
        pass

    @classmethod
    async def load(cls, store_name: str, user_id: str) -> OnlineToken:
        return OnlineToken(
            access_token=online_token_data.access_token,
            scope=online_token_data.scope.split(','),
            associated_user_id=online_token_data.associated_user.id,
            associated_user_scope=online_token_data.associated_user_scope.split(','),
            expires_in=online_token_data.expires_in,
            store_name=test_information.store_name,
        )


class OfflineToken(OfflineTokenABC):
    async def save(self):
        pass

    @classmethod
    async def load(cls, store_name: str) -> OfflineToken:
        return OfflineToken(
            access_token=offline_token_data.access_token,
            scope=offline_token_data.scope.split(','),
            store_name=test_information.store_name,
        )
