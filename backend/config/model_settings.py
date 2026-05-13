from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class LocalModelSettings:
    llama_cpp_enabled: bool
    llama_cpp_dir: Path
    interpreter_model: str
    lyrics_model: str
    technical_model: str
    soundtrack_model: str
    singing_voice_engine: str
    stems_model: str
    mixer_engine: str
    max_loaded_models: int

    @classmethod
    def load(cls, project_root: Path) -> "LocalModelSettings":
        return cls(
            llama_cpp_enabled=os.getenv("SONG_AI_LLAMA_CPP_ENABLED", "false").lower() == "true",
            llama_cpp_dir=Path(os.getenv("SONG_AI_LLAMA_CPP_DIR", str(project_root / "models" / "llama.cpp"))),
            interpreter_model=os.getenv("SONG_AI_INTERPRETER_MODEL", "Gemma 4 E4B IT GGUF"),
            lyrics_model=os.getenv("SONG_AI_LYRICS_MODEL", "Gemma 4 E4B IT GGUF"),
            technical_model=os.getenv("SONG_AI_TECHNICAL_MODEL", "Qwen3 4B GGUF"),
            soundtrack_model=os.getenv("SONG_AI_SOUNDTRACK_MODEL", "MusicGen small"),
            singing_voice_engine=os.getenv("SONG_AI_SINGING_VOICE_ENGINE", "RVC / ACE-Step"),
            stems_model=os.getenv("SONG_AI_STEMS_MODEL", "Demucs"),
            mixer_engine=os.getenv("SONG_AI_MIXER_ENGINE", "ffmpeg"),
            max_loaded_models=int(os.getenv("SONG_AI_MAX_LOADED_MODELS", "1")),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "llama_cpp_enabled": self.llama_cpp_enabled,
            "llama_cpp_dir": str(self.llama_cpp_dir),
            "interpreter_model": self.interpreter_model,
            "lyrics_model": self.lyrics_model,
            "technical_model": self.technical_model,
            "soundtrack_model": self.soundtrack_model,
            "singing_voice_engine": self.singing_voice_engine,
            "stems_model": self.stems_model,
            "mixer_engine": self.mixer_engine,
            "max_loaded_models": self.max_loaded_models,
        }


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
