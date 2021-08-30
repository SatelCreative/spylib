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
