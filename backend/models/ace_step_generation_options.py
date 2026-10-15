"""Validated controls supported by the installed direct handler."""
import math
from models.ace_step_capability_profile import CONNECTED_PROFILE, APIS, LM_MODELS


def generation_options(spec: dict) -> dict:
    result = {}
    api = spec.get("generation_api", "direct")
    if api not in APIS:
        raise ValueError("Selecciona una API de generacion admitida.")
    if api == "high_level_lm" and spec.get("task_type", "text2music") != "text2music":
        raise ValueError("El LM opcional solo esta conectado para crear desde texto.")
    if api != "direct":
        result["generation_api"] = api
    if api == "high_level_lm":
        model = spec.get("lm_model_path", "acestep-5Hz-lm-1.7B")
        if model not in LM_MODELS:
            raise ValueError("Selecciona un modelo LM local admitido.")
        result["lm_model_path"] = model
    turbo = spec.get("ace_step_config") == "acestep-v15-turbo"
    ranges = CONNECTED_PROFILE.numeric_ranges(str(spec.get("ace_step_config", "")))
    for key, (low, high) in ranges.items():
        value = spec.get(key)
        if value in (None, ""):
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"Revisa {key}: debe estar entre {low} y {high}.")
        if key in {"seed", "inference_steps"} and int(value) != value:
            raise ValueError(f"{key} debe ser entero.")
        if key == "guidance_scale" and turbo and value != 1:
            raise ValueError("Turbo no admite ajustar guidance; usa 1 o delega al perfil.")
        result[key] = int(value) if key in {"seed", "inference_steps"} else value
    return result
