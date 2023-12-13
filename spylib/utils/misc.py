from datetime import datetime, timezone
from typing import Any, List

from .shortuuid import random


def now_epoch() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def get_unique_id() -> str:
    return random(length=10)


def parse_scope(v: Any) -> List[str]:
    if isinstance(v, str):
        return v.split(',')
    return v
