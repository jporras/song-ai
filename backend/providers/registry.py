from config.model_settings import HuggingFaceModelSettings
from providers.base import InterpreterProvider, LyricsProvider, MusicProvider, VoiceProvider
from providers.huggingface import (
    HuggingFaceInterpreterProvider,
    HuggingFaceLyricsProvider,
    HuggingFaceMusicProvider,
    HuggingFaceProviderStatus,
    HuggingFaceVoiceProvider,
)
from providers.local import LocalLyricsProvider, LocalMusicProvider, LocalVoiceProvider
from providers.pro import ProLyricsProvider, ProMusicProvider, ProVoiceProvider


class ProviderRegistry:
    def __init__(self, hf_settings: HuggingFaceModelSettings | None = None) -> None:
        self.hf_settings = hf_settings
        self.interpreter_providers: list[InterpreterProvider] = []
        self.music_providers: list[MusicProvider] = [LocalMusicProvider()]
        self.voice_providers: list[VoiceProvider] = [LocalVoiceProvider()]
        self.lyrics_providers: list[LyricsProvider] = [LocalLyricsProvider()]
        if hf_settings is not None:
            self.interpreter_providers.append(HuggingFaceInterpreterProvider(hf_settings))
            self.music_providers.append(HuggingFaceMusicProvider(hf_settings))
            self.voice_providers.append(HuggingFaceVoiceProvider(hf_settings))
            self.lyrics_providers.append(HuggingFaceLyricsProvider(hf_settings))
        self.music_providers.append(ProMusicProvider())
        self.voice_providers.append(ProVoiceProvider())
        self.lyrics_providers.append(ProLyricsProvider())

    def summary(self) -> dict[str, list[dict[str, object]]]:
        summary = {
            "interpreter": self._summarize(self.interpreter_providers),
            "music": self._summarize(self.music_providers),
            "voice": self._summarize(self.voice_providers),
            "lyrics": self._summarize(self.lyrics_providers),
        }
        return summary

    def model_status(self) -> dict[str, object]:
        if self.hf_settings is None:
            return {"huggingface": {"enabled": False, "reason": "No HuggingFace settings loaded"}}
        return {"huggingface": HuggingFaceProviderStatus(self.hf_settings).to_dict()}

    def _summarize(
        self,
        providers: list[InterpreterProvider] | list[MusicProvider] | list[VoiceProvider] | list[LyricsProvider],
    ) -> list[dict[str, object]]:
        return [{"name": provider.name(), "capabilities": provider.capabilities()} for provider in providers]
