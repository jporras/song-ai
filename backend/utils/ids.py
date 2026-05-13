from datetime import datetime, timezone


def generate_id(prefix: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    return f"{prefix}-{stamp}"
