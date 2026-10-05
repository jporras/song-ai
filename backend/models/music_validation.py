"""Shared musical input boundaries for persisted project intent."""

BPM_MIN = 48
BPM_MAX = 240


def validate_bpm(value: object) -> int:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"BPM debe ser un entero entre {BPM_MIN} y {BPM_MAX}.")
    try:
        bpm = int(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"BPM debe ser un entero entre {BPM_MIN} y {BPM_MAX}.") from error
    if str(value).strip() != str(bpm) or not BPM_MIN <= bpm <= BPM_MAX:
        raise ValueError(f"BPM debe ser un entero entre {BPM_MIN} y {BPM_MAX}.")
    return bpm
