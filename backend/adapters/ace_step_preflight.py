"""Cheap local prerequisites; presence is not a proof of model load or audio quality."""
import json
from pathlib import Path

from audio.ace_step_profiles import resolve_ace_step_profile


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
                    self.repository_root / ".venv" / "Scripts" / "python.exe",
                    root / config / "config.json", root / config / "model.safetensors",
                    root / "vae" / "config.json", root / "vae" / "diffusion_pytorch_model.safetensors",
                    root / "Qwen3-Embedding-0.6B" / "config.json", root / "Qwen3-Embedding-0.6B" / "model.safetensors"]
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
                "model_loaded_verified": False, "hardware_inference_verified": False,
                "weights_checksum_verified": False, "profile_device": profile.device}
