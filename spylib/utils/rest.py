from enum import Enum

from pydantic import BaseModel
from starlette import status


class Method(Enum):
    GET = 'get'
    POST = 'post'
    PUT = 'put'
    DELETE = 'delete'


class Request(BaseModel):
    method: Method
    good_status: int


GET = Request(method=Method.GET, good_status=status.HTTP_200_OK)
POST = Request(method=Method.POST, good_status=status.HTTP_201_CREATED)
PUT = Request(method=Method.PUT, good_status=status.HTTP_200_OK)
DELETE = Request(method=Method.DELETE, good_status=status.HTTP_200_OK)
