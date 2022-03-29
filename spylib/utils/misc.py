from datetime import datetime, timezone


def now_epoch() -> int:
    return int(datetime.now(timezone.utc).timestamp())
