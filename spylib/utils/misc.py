from datetime import datetime, timezone

from .shortuuid import random


def now_epoch() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def get_unique_id() -> str:
    return random(length=10)
