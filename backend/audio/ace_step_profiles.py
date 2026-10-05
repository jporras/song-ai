from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AceStepProfile:
    name: str
    model_type: str
    infer_steps: int
    threads: int
    device: str
    model_repo: str
    config_path: str
    checkpoint_root: str = "data/models/music/acestep-1.5-2b-turbo"

    def format_values(self) -> dict[str, object]:
        return {
            "model_type": self.model_type,
            "infer_steps": self.infer_steps,
            "threads": self.threads,
            "device": self.device,
            "config_path": self.config_path,
            "checkpoint_root": self.checkpoint_root,
        }


TURBO_PROFILE = AceStepProfile(
    name="turbo",
    model_type="2b-turbo",
    infer_steps=8,
    threads=4,
    device="xpu",
    model_repo="ACE-Step/Ace-Step1.5",
    config_path="acestep-v15-turbo",
)
BASE_PROFILE = AceStepProfile(
    name="base",
    model_type="2b-base",
    infer_steps=32,
    threads=14,
    device="cpu",
    model_repo="ACE-Step/acestep-v15-base",
    config_path="acestep-v15-base",
)


def resolve_ace_step_profile(requested: str | None = None) -> AceStepProfile:
    raw = (
        requested
        or os.getenv("SONG_AI_FULL_SONG_PROFILE")
        or os.getenv("SONG_AI_ACE_STEP_PROFILE")
        or os.getenv("SONG_AI_AUDIO_MODEL_PROFILE")
        or "turbo"
    )
    normalized = raw.strip().lower().replace("_", "-")
    if normalized in {"turbo", "fast", "speed", "igpu", "xpu", "2b", "2b-turbo"}:
        return TURBO_PROFILE
    if normalized in {"base", "quality", "cpu", "heavy", "3.5b", "3.5b-default", "default"}:
        return BASE_PROFILE
    raise ValueError(
        "Perfil ACE-Step no soportado. Usa 'turbo' para iGPU/velocidad o 'base' para CPU/calidad."
    )


def apply_ace_step_profile_env(env: dict[str, str], profile: AceStepProfile) -> dict[str, str]:
    env["ACESTEP_MODEL_REPO"] = profile.model_repo
    env["ACESTEP_CONFIG_PATH"] = profile.config_path
    env["ACESTEP_CHECKPOINTS_DIR"] = profile.checkpoint_root
    return env
