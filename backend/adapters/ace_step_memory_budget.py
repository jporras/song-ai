"""Conservative local budget, not a measured model working set."""
import math
from pathlib import Path


def estimate_ace_step_memory(repository_root: Path, profile, lm_model_path=None) -> dict:
    root = repository_root / profile.checkpoint_root
    files = (root / profile.config_path / "model.safetensors",
             root / "vae" / "diffusion_pytorch_model.safetensors",
             root / "Qwen3-Embedding-0.6B" / "model.safetensors")
    if lm_model_path:
        if lm_model_path not in {"acestep-5Hz-lm-0.6B", "acestep-5Hz-lm-1.7B"}:
            raise ValueError("Modelo LM no admitido.")
        files += (root / lm_model_path / "model.safetensors",)
    sizes = [p.stat().st_size if p.is_file() else 0 for p in files]
    if not all(sizes):
        raise ValueError("Faltan pesos locales para estimar el presupuesto de memoria de ACE-Step.")
    weights_mb = math.ceil(sum(sizes) / (1024 * 1024))
    reserve = 2048 if lm_model_path else 1024
    return {"profile": profile.name, "config_path": profile.config_path,
            "weight_files_mb": weights_mb, "lm_model_path": lm_model_path, "additional_reserve_mb": reserve,
            "required_ram_mb": weights_mb + reserve, "method": "local_weight_bytes_plus_reserve",
            "measured_working_set": False, "model_load_verified": False}
