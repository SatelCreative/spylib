from datetime import datetime, timezone

from .shortuuid import random


def now_epoch() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def get_unique_id() -> str:
    return random(length=10)


def snake_to_camel_case(text: str) -> str:
    temp = text.lower().split('_')
    return temp[0] + ''.join(element.title() for element in temp[1:])
