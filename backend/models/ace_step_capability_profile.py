"""Connected integration rules, independent of hardware availability and providers."""
from dataclasses import dataclass
from models.ace_step_control_help import CONTROL_HELP

TASKS = ("text2music", "cover", "repaint", "lego", "extract", "complete")
BASE_TASKS = frozenset({"lego", "extract", "complete"})
INTERVAL_TASKS = frozenset({"repaint", "lego"})
TRACKS = frozenset({"vocals", "backing_vocals", "drums", "bass", "guitar", "keyboard",
                    "percussion", "strings", "synth", "fx", "brass", "woodwinds"})
APIS = ("direct", "high_level", "high_level_lm")
LM_MODELS = ("acestep-5Hz-lm-0.6B", "acestep-5Hz-lm-1.7B")
LOCAL_CONFIGS = ("acestep-v15-base", "acestep-v15-turbo")
BASE_COMPATIBLE_CONFIGS = frozenset({"acestep-v15-base", "acestep-v15-xl-base"})


@dataclass(frozen=True)
class AceStepCapabilityProfile:
    """Versioned contract: connected does not imply installed/available/verified audio."""
    version: str = "song-ai-connected-1.0"

    def engine_choices(self) -> dict:
        return {"generation_api": APIS, "lm_model_path": LM_MODELS, "task_type": TASKS,
                "ace_step_config": LOCAL_CONFIGS, "target_tracks": tuple(sorted(TRACKS))}

    def numeric_ranges(self, config: str) -> dict:
        return {"seed": (0, 2**32 - 1),
                "inference_steps": (1, 20 if config == "acestep-v15-turbo" else 200),
                "guidance_scale": (1, 15), "shift": (.1, 10)}

    def field_policy(self, field: str, spec: dict) -> dict:
        task = spec.get("task_type", "text2music")
        applicable = True
        required = False
        if field in {"source_artifact_id", "src_audio"}:
            applicable = task != "text2music"
            required = applicable
        elif field in {"instruction", "target_tracks"}:
            applicable = task in BASE_TASKS
            required = applicable
        elif field in {"repainting_start", "repainting_end"}:
            applicable = task in INTERVAL_TASKS
        elif field == "audio_cover_strength":
            applicable = task == "cover"
        elif field == "lm_model_path":
            applicable = task == "text2music" and spec.get("generation_api", "direct") == "high_level_lm"
        result = {"applicable": applicable, "required_for_task": required}
        if field in self.numeric_ranges(str(spec.get("ace_step_config", ""))):
            low, high = self.numeric_ranges(str(spec.get("ace_step_config", "")))[field]
            result.update(minimum=low, maximum=high)
            if field == "guidance_scale" and spec.get("ace_step_config") == "acestep-v15-turbo":
                result.update(minimum=1, maximum=1, fixed_value=1)
        return result

    def public_contract(self) -> dict:
        return {"version": self.version, "scope": "connected_rules_not_runtime_availability",
                "control_help": {
                    **CONTROL_HELP,
                    "seed": {"meaning": "Número que identifica una variación de generación.",
                        "effect": "Permite comparar cambios con la misma configuración; no garantiza audio idéntico entre modelos o equipos.",
                        "example": "Conserva 24680 al comparar dos propuestas; cambia el número para explorar otra variación."},
                    "inference_steps": {"meaning": "Cantidad de pasos que usa el motor para generar el audio.",
                        "effect": "Puede cambiar tiempo y resultado; más pasos no garantizan más calidad. El límite depende del modelo.",
                        "example": "Puedes dejarlo vacío para usar el perfil; Turbo permite hasta 20 pasos."},
                    "guidance_scale": {"meaning": "Ajuste técnico de condicionamiento de la generación.",
                        "effect": "No asegura fidelidad musical. Turbo exige 1; Base admite el rango mostrado.",
                        "example": "Con Turbo usa 1 o deja el valor delegado al perfil."},
                    "shift": {"meaning": "Ajuste de cómo se distribuyen los pasos de generación.",
                        "effect": "Modifica la ejecución del motor, no equivale a volumen, emoción ni velocidad de la canción.",
                        "example": "Déjalo vacío para usar el perfil; cualquier cambio se revisa antes de generar."},
                },
                "runtime_availability": "requires_preflight", "audio_quality": "not_verified_by_contract",
                "fixed_values_by_config": {"acestep-v15-turbo": {"guidance_scale": 1}},
                "creation_task": "text2music", "choices": self.engine_choices(),
                "modes": {task: {"requires_source": task != "text2music",
                    "requires_base": task in BASE_TASKS, "uses_interval": task in INTERVAL_TASKS,
                    "track_cardinality": "one" if task in {"lego", "extract"} else
                                         "one_or_more" if task == "complete" else "not_applicable"}
                          for task in TASKS},
                "numeric_ranges_by_config": {config: self.numeric_ranges(config) for config in LOCAL_CONFIGS}}


CONNECTED_PROFILE = AceStepCapabilityProfile()
