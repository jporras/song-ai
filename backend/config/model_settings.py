from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class LocalModelSettings:
    llama_cpp_enabled: bool
    llama_cpp_dir: Path
    llama_cpp_base_url: str
    llama_cpp_interpreter_base_url: str
    llama_cpp_technical_base_url: str
    gemma_gguf_path: Path
    qwen_gguf_path: Path
    llama_cpp_timeout_seconds: int
    llama_cpp_n_predict: int
    llama_cpp_temperature: float
    interpreter_model: str
    lyrics_model: str
    technical_model: str
    soundtrack_model: str
    singing_voice_engine: str
    stems_model: str
    mixer_engine: str
    full_song_command: str
    soundtrack_command: str
    singing_voice_command: str
    voice_conversion_command: str
    local_command_timeout_seconds: int
    allow_cpu_full_song: bool
    max_loaded_models: int

    @classmethod
    def load(cls, project_root: Path) -> "LocalModelSettings":
        return cls(
            llama_cpp_enabled=True,
            llama_cpp_dir=Path(os.getenv("SONG_AI_LLAMA_CPP_DIR", str(project_root / "models" / "llama.cpp"))),
            llama_cpp_base_url=os.getenv("SONG_AI_LLAMA_CPP_BASE_URL", "http://localhost:8080"),
            llama_cpp_interpreter_base_url=os.getenv(
                "SONG_AI_LLAMA_CPP_INTERPRETER_BASE_URL",
                os.getenv("SONG_AI_LLAMA_CPP_BASE_URL", "http://localhost:8080"),
            ),
            llama_cpp_technical_base_url=os.getenv(
                "SONG_AI_LLAMA_CPP_TECHNICAL_BASE_URL",
                os.getenv("SONG_AI_LLAMA_CPP_BASE_URL", "http://localhost:8080"),
            ),
            gemma_gguf_path=Path(os.getenv("SONG_AI_GEMMA_GGUF_PATH", "/app/models/llm/gemma/gemma.gguf")),
            qwen_gguf_path=Path(os.getenv("SONG_AI_QWEN_GGUF_PATH", "/app/models/llm/qwen/qwen.gguf")),
            llama_cpp_timeout_seconds=int(os.getenv("SONG_AI_LLAMA_CPP_TIMEOUT_SECONDS", "45")),
            llama_cpp_n_predict=int(os.getenv("SONG_AI_LLAMA_CPP_N_PREDICT", "512")),
            llama_cpp_temperature=float(os.getenv("SONG_AI_LLAMA_CPP_TEMPERATURE", "0.35")),
            interpreter_model=os.getenv("SONG_AI_INTERPRETER_MODEL", "Gemma 4 E4B IT GGUF"),
            lyrics_model=os.getenv("SONG_AI_LYRICS_MODEL", "Gemma 4 E4B IT GGUF"),
            technical_model=os.getenv("SONG_AI_TECHNICAL_MODEL", "Qwen3 4B GGUF"),
            soundtrack_model=os.getenv("SONG_AI_SOUNDTRACK_MODEL", "MusicGen small"),
            singing_voice_engine=os.getenv("SONG_AI_SINGING_VOICE_ENGINE", "RVC / ACE-Step"),
            stems_model=os.getenv("SONG_AI_STEMS_MODEL", "Demucs"),
            mixer_engine=os.getenv("SONG_AI_MIXER_ENGINE", "ffmpeg"),
            full_song_command=os.getenv("SONG_AI_FULL_SONG_COMMAND", ""),
            soundtrack_command=os.getenv("SONG_AI_SOUNDTRACK_COMMAND", ""),
            singing_voice_command=os.getenv("SONG_AI_SINGING_VOICE_COMMAND", ""),
            voice_conversion_command=os.getenv("SONG_AI_VOICE_CONVERSION_COMMAND", ""),
            local_command_timeout_seconds=int(os.getenv("SONG_AI_LOCAL_COMMAND_TIMEOUT_SECONDS", "3600")),
            allow_cpu_full_song=os.getenv("SONG_AI_ALLOW_CPU_FULL_SONG", "false").lower() == "true",
            max_loaded_models=int(os.getenv("SONG_AI_MAX_LOADED_MODELS", "1")),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "llama_cpp_mode": "auto",
            "llama_cpp_enabled": self.llama_cpp_enabled,
            "llama_cpp_dir": str(self.llama_cpp_dir),
            "llama_cpp_base_url": self.llama_cpp_base_url,
            "llama_cpp_interpreter_base_url": self.llama_cpp_interpreter_base_url,
            "llama_cpp_technical_base_url": self.llama_cpp_technical_base_url,
            "gemma_gguf_path": str(self.gemma_gguf_path),
            "qwen_gguf_path": str(self.qwen_gguf_path),
            "llama_cpp_timeout_seconds": self.llama_cpp_timeout_seconds,
            "llama_cpp_n_predict": self.llama_cpp_n_predict,
            "llama_cpp_temperature": self.llama_cpp_temperature,
            "interpreter_model": self.interpreter_model,
            "lyrics_model": self.lyrics_model,
            "technical_model": self.technical_model,
            "soundtrack_model": self.soundtrack_model,
            "singing_voice_engine": self.singing_voice_engine,
            "stems_model": self.stems_model,
            "mixer_engine": self.mixer_engine,
            "full_song_command_configured": bool(self.full_song_command.strip()),
            "soundtrack_command_configured": bool(self.soundtrack_command.strip()),
            "singing_voice_command_configured": bool(self.singing_voice_command.strip()),
            "voice_conversion_command_configured": bool(self.voice_conversion_command.strip()),
            "local_command_timeout_seconds": self.local_command_timeout_seconds,
            "allow_cpu_full_song": self.allow_cpu_full_song,
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
