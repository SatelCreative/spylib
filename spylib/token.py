from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from types import MethodType
from typing import Callable, List, Optional
from loguru import logger

from pydantic import BaseModel

from httpx import AsyncClient


class HTTPClient(AsyncClient):
    __instance: AsyncClient = None

    def __new__(cls):
        if HTTPClient.__instance is None:
            HTTPClient.__instance = AsyncClient()
        return HTTPClient.__instance

    @classmethod
    async def close(cls):
        # graceful shutdown
        await HTTPClient.__instance.aclose()


class AssociatedUser(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    email_verified: bool
    account_owner: bool
    locale: str
    collaborator: bool


class OfflineTokenResponse(BaseModel):
    access_token: str
    scope: str


class OnlineTokenResponse(BaseModel):
    access_token: str
    scope: str
    expires_in: int
    associated_user_scope: str
    associated_user: AssociatedUser


class Token(ABC):
    """
    Abstract class for token objects. This should never be extended, as you
    should either be using the OfflineToken or the OnlineToken.
    """

    def __init__(
        self,
        store_name: str,
        scope: List[str],
        access_token: Optional[str] = None,
        save_token: Optional[Callable] = None,
        load_token: Optional[Callable] = None,
    ) -> None:

        self.access_token_invalid = False
        self.store_name = store_name
        self.url = f'https://{store_name}/admin/oauth/access_token'
        self.scope = scope
        self.access_token = access_token

        if load_token:
            self.load_token = MethodType(load_token, self)
        if save_token:
            self.save_token = MethodType(save_token, self)

    @classmethod
    async def new(
        cls,
        store_name: str,
        scope: List[str],
        client_id: str,
        client_secret: str,
        code: str,
        save_token: Optional[Callable] = None,
        load_token: Optional[Callable] = None,
    ):
        """
        Creates a new instance of the object and requests the token from the API
        as it requires an async call.
        """
        token = cls(
            store_name,
            scope,
            None,
            save_token,
            load_token,
        )
        await token.set_token(client_id, client_secret, code)
        return token

    def save_token(self):
        """
        This function handles saving the token. By default this does nothing,
        therefore the developer should override this by passing in a custom
        function to the initialization of the object.
        """
        pass

    def load_token(self):
        """
        This function handles loading the token. By default this does nothing,
        therefore the developer should override this by passing in a custom
        function to the initialization of the object.
        """
        pass

    @abstractmethod
    async def set_token(self, client_id: str, client_secret: str, code: str):
        """
        Sets the token based on the response from _get_token. This is the initial
        generation of the tokens from the endpoint.
        """
        pass

    async def _get_token(
        self, client_id: str, client_secret: str, authorization_code: str
    ) -> dict:
        """
        Makes a request to the access_token endpoint using the API key,
        client secret, store_name, and the code.
        """

        httpclient = HTTPClient()

        jsondata = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': authorization_code,
        }

        response = await httpclient.request(
            method='post',
            url=self.url,
            json=jsondata,
            timeout=20.0,
        )
        if response.status_code != 200:
            message = (
                f'Problem retrieving access token. Status code: {response.status_code} {jsondata}'
                f'response=> {response.text}'
            )
            logger.error(message)
            raise ValueError(message)

        return response.json()

    async def reset_token(self, client_id: str, client_secret: str, code: str):
        """Use this function to initialize a new access token for this store"""
        await self.set_token(client_id, client_secret, code)
        self.access_token_invalid = False

    def __new__(cls, *args, **kwargs):
        """
        Function to keep user from instantiating an instance of this class.
        """
        if cls is Token:
            raise TypeError(f'Can\'t instantiate abstract class {cls.__name__} directly')
        return object.__new__(cls)


class OfflineToken(Token):
    """
    Offline tokens are used for long term access, and do not have a set expiry.
    """

    def __init__(
        self,
        store_name: str,
        scope: List[str],
        access_token: Optional[str] = None,
        save_token: Optional[Callable] = None,
        load_token: Optional[Callable] = None,
    ) -> None:
        super().__init__(store_name, scope, access_token, save_token, load_token)

    async def set_token(self, client_id: str, client_secret: str, code: str):

        token: OfflineTokenResponse = await self._get_token(client_id, client_secret, code)
        self.access_token = token['access_token']
        self.scope = token['scope']


class OnlineToken(Token):
    """
    Online tokens are used to implement applications that are authenticated with
    a specific user's credentials. These extend on the original token, adding
    in a user, its scope and an expiry time.
    """

    def __init__(
        self,
        store_name: str,
        scope: List[str],
        access_token: str,
        associated_user: Optional[AssociatedUser] = None,
        expires_in: Optional[int] = None,
        save_token: Optional[Callable] = None,
        load_token: Optional[Callable] = None,
    ) -> None:
        super().__init__(store_name, scope, access_token, save_token, load_token)

        self.associated_user: AssociatedUser = associated_user
        if expires_in:
            self.expires_at: int = datetime.now() + timedelta(days=0, seconds=expires_in)

    async def update_token(self):
        """
        Updates the current online token with a new one from the endpoint. This is
        only available for online tokens as they have a refresh token associated
        with them.
        """

    async def set_token(self, client_id: str, client_secret: str, code: str):

        token: OnlineTokenResponse = await self._get_token(client_id, client_secret, code)
        self.access_token = token['access_token']
        self.scope = token['scope']
        self.associated_user: AssociatedUser = token['associated_user']
        self.associated_user_scope = token['associated_user_scope']
        self.expires_at = datetime.now() + timedelta(days=0, seconds=token['expires_in'])
