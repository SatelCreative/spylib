from enum import Enum

from pydantic import BaseModel


class Status(Enum):
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    SEE_OTHER = 303
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    PAYMENT_REQUIRED = 402
    FORBIDDEN = 403
    NOT_FOUND = 404
    NOT_ACCEPTABLE = 406
    UNPROCESSABLE_ENTITY = 422
    SHOP_LOCKED = 423
    TOO_MANY_REQUESTS = 429
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504


class Method(Enum):
    GET = 'get'
    POST = 'post'
    PUT = 'put'
    DELETE = 'delete'


class Request(BaseModel):
    method: Method
    good_status: Status


GET = Request(method=Method.GET, good_status=Status.OK)
POST = Request(method=Method.POST, good_status=Status.CREATED)
PUT = Request(method=Method.PUT, good_status=Status.OK)
DELETE = Request(method=Method.DELETE, good_status=Status.OK)
