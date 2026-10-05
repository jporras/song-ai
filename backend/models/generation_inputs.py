"""Project phase content that affects generation, excluding persistence metadata."""
from copy import deepcopy


def musical_phase_inputs(records: dict[str, object]) -> dict[str, object]:
    result = {}
    for phase, record in records.items():
        data = deepcopy(record.get("data", {}))
        if phase == "production":
            production = data.get("production", {})
            for key in ("projectSet", "productionProjectId", "productionGlobalStatus"):
                production.pop(key, None)
            if not production:
                data.pop("production", None)
        if phase == "intent":
            data.get("intent", {}).pop("inspirationInput", None)
        if phase == "lyrics":
            data.get("lyricsEditor", {}).pop("path", None)
        if data:
            result[phase] = data
    return result
