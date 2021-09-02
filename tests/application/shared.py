import asyncio

from pydantic.dataclasses import dataclass

from spylib.application import ShopifyApplication
from spylib.token import OfflineToken, OnlineToken


@dataclass
class MockHTTPResponse:
    status_code: int
    jsondata: dict
    headers: dict = None  # type: ignore

    def json(self):
        return self.jsondata


def post_install(self: ShopifyApplication, token: OfflineToken):
    self.get_store(token.store_name).offline_access_token = token


def post_login(self: ShopifyApplication, token: OnlineToken):
    if not token.associated_user:
        raise ValueError(
            'Associated user is not defined for this token.',
            'Cannot be added to the store as there is no way to find it.',
        )
    self.get_store(token.store_name).online_access_tokens[token.associated_user.id] = token


async def async_post_install(self: ShopifyApplication, token: OfflineToken):
    await asyncio.sleep(1)
    self.get_store(token.store_name).offline_access_token = token


async def async_post_login(self: ShopifyApplication, token: OnlineToken):
    if not token.associated_user:
        raise ValueError(
            'Associated user is not defined for this token.',
            'Cannot be added to the store as there is no way to find it.',
        )
    await asyncio.sleep(1)
    self.get_store(token.store_name).online_access_tokens[token.associated_user.id] = token
