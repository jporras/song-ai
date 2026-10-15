"""Cheap local prerequisites; presence is not a proof of model load or audio quality."""
import json
from pathlib import Path

from audio.ace_step_profiles import resolve_ace_step_profile
from adapters.ace_step_memory_budget import estimate_ace_step_memory
from adapters.acestep_checkpoint_inventory import COMPONENTS


class AceStepPreflight:
    def __init__(self, repository_root: Path):
        self.repository_root = repository_root

    def inspect_plan(self, item: dict) -> dict:
        config = item["plan"]["retained_spec"].get("ace_step_config")
        if config not in {"acestep-v15-base", "acestep-v15-turbo"}:
            raise ValueError("Selecciona un modelo local ACE-Step admitido.")
        profile = resolve_ace_step_profile("base" if config == "acestep-v15-base" else "turbo")
        root = self.repository_root / profile.checkpoint_root
        required = [self.repository_root / "tools" / "acestep_generate.py",
                    self.repository_root / ".venv" / "Scripts" / "python.exe"]
        required.extend(root / component / filename
                        for component in (config, 'vae', 'Qwen3-Embedding-0.6B')
                        for filename in COMPONENTS[component])
        payload = item["plan"].get("payload", {})
        lm_model = payload.get("lm_model_path") if payload.get("generation_api") == "high_level_lm" else None
        if lm_model:
            if lm_model not in {"acestep-5Hz-lm-0.6B", "acestep-5Hz-lm-1.7B"}:
                raise ValueError("Modelo LM no admitido.")
            required.extend(root / lm_model / filename for filename in COMPONENTS[lm_model])
        missing = [str(path.relative_to(self.repository_root)) for path in required if not path.is_file() or path.stat().st_size == 0]
        if missing:
            raise ValueError("Faltan archivos locales para ACE-Step: " + ", ".join(missing))
        try:
            architecture = json.loads((root / config / "config.json").read_text(encoding="utf-8")).get("architectures", [])
        except (ValueError, OSError) as error:
            raise ValueError("Revisa la configuracion local del modelo ACE-Step.") from error
        if "AceStepConditionGenerationModel" not in architecture:
            raise ValueError("La configuracion no declara la arquitectura ACE-Step 1.5 esperada.")
        return {"config_path": config, "required_files_present": True,
                "memory_budget": estimate_ace_step_memory(self.repository_root, profile, lm_model),
                "model_loaded_verified": False, "hardware_inference_verified": False,
                "weights_checksum_verified": False, "profile_device": profile.device}
