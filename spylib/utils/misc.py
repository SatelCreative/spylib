from datetime import datetime, timezone
from functools import wraps
from time import perf_counter
from typing import Any, List, Type

from pydantic import BaseModel

from .shortuuid import random


def now_epoch() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def get_unique_id() -> str:
    return random(length=10)


def parse_scope(v: Any) -> List[str]:
    if isinstance(v, str):
        return v.split(',')
    return v


class ElapsedTime(BaseModel):
    start: float
    end: float

    @property
    def seconds(self) -> float:
        return self.end - self.start

    @property
    def milliseconds(self) -> float:
        return 1000 * (self.end - self.start)


class TimedResult(BaseModel):
    result: Any
    elapsed_time: ElapsedTime


def elapsed_time(data_type: Type[TimedResult]):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = perf_counter()
            result = await func(*args, **kwargs)
            end = perf_counter()

            return data_type(result=result, elapsed_time=ElapsedTime(start=start, end=end))

        return wrapper

    return decorator
