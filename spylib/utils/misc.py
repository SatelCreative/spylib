from datetime import datetime, timezone

from shortuuid import ShortUUID  # type: ignore


def now_epoch() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def get_unique_id() -> str:
    return ShortUUID().random(length=10)
