from config.model_settings import HuggingFaceModelSettings
from providers.base import InterpreterProvider, LyricsProvider, MusicProvider, VoiceProvider


class HuggingFaceProviderStatus:
    def __init__(self, settings: HuggingFaceModelSettings) -> None:
        self.settings = settings

    def to_dict(self) -> dict[str, object]:
        return {
            "enabled": self.settings.enabled,
            "device": self.settings.device,
            "cache_dir": str(self.settings.cache_dir),
            "cache_exists": self.settings.cache_dir.exists(),
            "models": {
                "interpreter": self.settings.interpreter_model,
                "lyrics": self.settings.lyrics_model,
                "music": self.settings.music_model,
                "voice": self.settings.voice_model,
            },
            "download_policy": "manual_or_future_worker",
        }


class HuggingFaceInterpreterProvider(InterpreterProvider):
    def __init__(self, settings: HuggingFaceModelSettings) -> None:
        self.settings = settings

    def name(self) -> str:
        return "huggingface-interpreter-local"

    def capabilities(self) -> list[str]:
        return ["intent_interpretation", "option_guidance", "parameter_suggestion"]

    def interpret(self, text: str, target: str) -> dict[str, object]:
        return {
            "target": target,
            "input": text,
            "mode": "hf_placeholder",
            "model": self.settings.interpreter_model,
            "note": "Modelo HuggingFace no cargado todavia; esta respuesta preserva el contrato del provider.",
        }


class HuggingFaceMusicProvider(MusicProvider):
    def __init__(self, settings: HuggingFaceModelSettings) -> None:
        self.settings = settings

    def name(self) -> str:
        return "huggingface-music-local"

    def capabilities(self) -> list[str]:
        return ["future_local_instrumental", "future_local_audio_batch", "future_local_stems"]


class HuggingFaceVoiceProvider(VoiceProvider):
    def __init__(self, settings: HuggingFaceModelSettings) -> None:
        self.settings = settings

    def name(self) -> str:
        return "huggingface-voice-local"

    def capabilities(self) -> list[str]:
        return ["future_local_voice_preview", "future_local_vocal_guide"]


class HuggingFaceLyricsProvider(LyricsProvider):
    def __init__(self, settings: HuggingFaceModelSettings) -> None:
        self.settings = settings

    def name(self) -> str:
        return "huggingface-lyrics-local"

    def capabilities(self) -> list[str]:
        return ["future_local_lyrics_generation", "future_local_variations"]
