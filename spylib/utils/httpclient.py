from typing import Any

from httpx import AsyncClient


class HTTPClient(AsyncClient):
    __instance: Any = None

    def __new__(cls):
        if HTTPClient.__instance is None:
            HTTPClient.__instance = AsyncClient()
        return HTTPClient.__instance

    @classmethod
    async def close(cls):
        # graceful shutdown
        await HTTPClient.__instance.aclose()
