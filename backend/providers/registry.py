from config.model_settings import HuggingFaceModelSettings, LocalModelSettings
from providers.base import InterpreterProvider, LyricsProvider, MusicProvider, VoiceProvider
from providers.huggingface import (
    HuggingFaceInterpreterProvider,
    HuggingFaceLyricsProvider,
    HuggingFaceMusicProvider,
    HuggingFaceProviderStatus,
    HuggingFaceVoiceProvider,
)
from providers.local import LocalInterpreterProvider, LocalLyricsProvider, LocalMusicProvider, LocalVoiceProvider
from providers.pro import ProLyricsProvider, ProMusicProvider, ProVoiceProvider


class ProviderRegistry:
    def __init__(
        self,
        hf_settings: HuggingFaceModelSettings | None = None,
        local_settings: LocalModelSettings | None = None,
    ) -> None:
        self.hf_settings = hf_settings
        self.local_settings = local_settings
        self.interpreter_providers: list[InterpreterProvider] = [LocalInterpreterProvider()]
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

    def active_providers(self) -> dict[str, dict[str, object]]:
        return {
            "interpreter": self._active_provider("interpreter", self.interpreter_providers),
            "music": self._active_provider("music", self.music_providers),
            "voice": self._active_provider("voice", self.voice_providers),
            "lyrics": self._active_provider("lyrics", self.lyrics_providers),
        }

    def studio_status(self) -> dict[str, object]:
        active_providers = self.active_providers()
        return {
            "source_of_truth": "sqlite",
            "json_policy": "snapshots_regenerables",
            "mode": "mock_first_provider_ready",
            "primary_goal": "complete_lullaby_or_children_emotional_song",
            "priority_order": [
                "good_lyrics",
                "emotional_intent",
                "musical_structure",
                "coherent_soundtrack",
                "sung_voice",
                "final_mix",
            ],
            "provider_contract": {
                "interchangeable": True,
                "direct_prompt_chaining": False,
                "handoffs_via_state": ["sqlite", "tasks", "intent.json", "manifest.json", "set.json"],
                "memory_policy": "load_on_demand_and_release",
            },
            "active_providers": active_providers,
            "model_status": self.model_status(),
            "recommended_stack": self.recommended_stack(),
            "ready_roles": [
                role
                for role, provider in active_providers.items()
                if provider.get("status") in {"ready", "placeholder_ready"}
            ],
        }

    def model_status(self) -> dict[str, object]:
        local = self.local_settings.to_dict() if self.local_settings is not None else {}
        if self.hf_settings is None:
            return {
                "local": local,
                "huggingface": {"enabled": False, "reason": "No HuggingFace settings loaded"},
            }
        return {
            "local": local,
            "huggingface": HuggingFaceProviderStatus(self.hf_settings).to_dict(),
        }

    def recommended_stack(self) -> dict[str, object]:
        if self.local_settings is None:
            return {}
        return {
            "llm": {
                "interpreter": self.local_settings.interpreter_model,
                "lyrics": self.local_settings.lyrics_model,
                "technical": self.local_settings.technical_model,
                "runtime": "llama.cpp",
            },
            "audio": {
                "soundtrack": self.local_settings.soundtrack_model,
                "singing_voice": self.local_settings.singing_voice_engine,
                "stems": self.local_settings.stems_model,
                "mixer": self.local_settings.mixer_engine,
            },
        }

    def _summarize(
        self,
        providers: list[InterpreterProvider] | list[MusicProvider] | list[VoiceProvider] | list[LyricsProvider],
    ) -> list[dict[str, object]]:
        return [
            {
                "name": provider.name(),
                "capabilities": provider.capabilities(),
                "status": self._provider_status(provider.name()),
            }
            for provider in providers
        ]

    def _active_provider(
        self,
        provider_type: str,
        providers: list[InterpreterProvider] | list[MusicProvider] | list[VoiceProvider] | list[LyricsProvider],
    ) -> dict[str, object]:
        if not providers:
            return {
                "type": provider_type,
                "name": f"{provider_type}-mock-provider",
                "capabilities": ["mock_handoff"],
                "status": "placeholder_ready",
                "reason": "No concrete provider configured yet; orchestrator keeps the contract alive with a mock.",
            }

        provider = providers[0]
        return {
            "type": provider_type,
            "name": provider.name(),
            "capabilities": provider.capabilities(),
            "status": self._provider_status(provider.name()),
            "reason": "First registered provider is active for this role.",
        }

    def _provider_status(self, provider_name: str) -> str:
        if provider_name.startswith(("local-", "llamacpp-", "musicgen-", "singing-voice-")):
            return "ready"
        if provider_name.startswith("huggingface-"):
            if self.hf_settings is not None and self.hf_settings.enabled:
                return "configured"
            return "disabled"
        if provider_name.startswith("pro-"):
            return "placeholder_ready"
        return "unknown"
