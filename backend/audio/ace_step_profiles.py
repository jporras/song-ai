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

    def format_values(self) -> dict[str, object]:
        return {
            "model_type": self.model_type,
            "infer_steps": self.infer_steps,
            "threads": self.threads,
            "device": self.device,
        }


TURBO_PROFILE = AceStepProfile(
    name="turbo",
    model_type="2b-turbo",
    infer_steps=4,
    threads=4,
    device="xpu",
    model_repo="ACE-Step/ACE-Step-v1-2B-turbo",
)
BASE_PROFILE = AceStepProfile(
    name="base",
    model_type="3.5b-default",
    infer_steps=8,
    threads=14,
    device="cpu",
    model_repo="ACE-Step/ACE-Step-v1-3.5B",
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
    return env
