from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class HuggingFaceModelSettings:
    enabled: bool
    cache_dir: Path
    interpreter_model: str
    lyrics_model: str
    music_model: str
    voice_model: str
    device: str

    @classmethod
    def load(cls, project_root: Path) -> "HuggingFaceModelSettings":
        cache_dir = Path(os.getenv("HF_HOME", str(project_root / "data" / "models" / "huggingface")))
        return cls(
            enabled=os.getenv("SONG_AI_HF_ENABLED", "false").lower() == "true",
            cache_dir=cache_dir,
            interpreter_model=os.getenv("SONG_AI_HF_INTERPRETER_MODEL", "not-configured"),
            lyrics_model=os.getenv("SONG_AI_HF_LYRICS_MODEL", "not-configured"),
            music_model=os.getenv("SONG_AI_HF_MUSIC_MODEL", "not-configured"),
            voice_model=os.getenv("SONG_AI_HF_VOICE_MODEL", "not-configured"),
            device=os.getenv("SONG_AI_HF_DEVICE", "cpu"),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "cache_dir": str(self.cache_dir),
            "interpreter_model": self.interpreter_model,
            "lyrics_model": self.lyrics_model,
            "music_model": self.music_model,
            "voice_model": self.voice_model,
            "device": self.device,
        }
