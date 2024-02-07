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


class _Time(BaseModel):
    seconds: float
    milliseconds: float


class TimedResult(BaseModel):
    result: Any
    elapsed_time: _Time


def elapsed_time(data_type: Type[TimedResult]):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = perf_counter()
            result = await func(*args, **kwargs)
            end = perf_counter()

            time_diff_seconds = end - start
            return data_type(
                result=result,
                elapsed_time=_Time(
                    seconds=time_diff_seconds, milliseconds=time_diff_seconds * 1000
                ),
            )

        return wrapper

    return decorator
