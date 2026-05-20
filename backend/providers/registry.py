from config.model_settings import HuggingFaceModelSettings, LocalModelSettings
from providers.base import InterpreterProvider, LyricsProvider, MusicProvider, VoiceProvider
from providers.local import (
    LocalInterpreterProvider,
    LocalLyricsProvider,
    LocalMusicProvider,
    LocalTechnicalProvider,
    LocalVoiceProvider,
)
from providers.llamacpp import LlamaCppInterpreterProvider, LlamaCppLyricsProvider, LlamaCppTechnicalProvider


class ProviderRegistry:
    def __init__(
        self,
        hf_settings: HuggingFaceModelSettings | None = None,
        local_settings: LocalModelSettings | None = None,
    ) -> None:
        self.hf_settings = hf_settings
        self.local_settings = local_settings
        self.interpreter_providers: list[InterpreterProvider] = []
        self.technical_providers: list[InterpreterProvider] = []
        self.music_providers: list[MusicProvider] = [LocalMusicProvider()]
        self.voice_providers: list[VoiceProvider] = [LocalVoiceProvider()]
        self.lyrics_providers: list[LyricsProvider] = []
        if local_settings is not None and local_settings.llama_cpp_enabled:
            self.interpreter_providers.append(LlamaCppInterpreterProvider(local_settings))
            self.technical_providers.append(LlamaCppTechnicalProvider(local_settings))
            self.lyrics_providers.append(LlamaCppLyricsProvider(local_settings))
        self.interpreter_providers.append(LocalInterpreterProvider())
        self.technical_providers.append(LocalTechnicalProvider())
        self.lyrics_providers.append(LocalLyricsProvider())

    def summary(self) -> dict[str, list[dict[str, object]]]:
        summary = {
            "interpreter": self._summarize(self.interpreter_providers),
            "technical": self._summarize(self.technical_providers),
            "music": self._summarize(self.music_providers),
            "voice": self._summarize(self.voice_providers),
            "lyrics": self._summarize(self.lyrics_providers),
        }
        return summary

    def active_providers(self) -> dict[str, dict[str, object]]:
        return {
            "interpreter": self._active_provider("interpreter", self.interpreter_providers),
            "technical": self._active_provider("technical", self.technical_providers),
            "music": self._active_provider("music", self.music_providers),
            "voice": self._active_provider("voice", self.voice_providers),
            "lyrics": self._active_provider("lyrics", self.lyrics_providers),
        }

    def studio_status(self) -> dict[str, object]:
        active_providers = self.active_providers()
        return {
            "source_of_truth": "sqlite",
            "json_policy": "snapshots_regenerables",
            "mode": "local_only",
            "final_modes": {
                "available": ["local"],
                "disabled": {
                    "pro": "Desactivado en esta version. No se registran providers pagos ni remotos.",
                },
            },
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
            "local_pipeline": self.local_pipeline_status(),
            "llama_cpp": self.llama_cpp_status(),
            "ready_roles": [
                role
                for role, provider in active_providers.items()
                if provider.get("status") in {"ready", "placeholder_ready"}
            ],
        }

    def interpret_with_active_provider(self, prompt: str, target: str) -> dict[str, object]:
        provider = self.interpreter_providers[0]
        return provider.interpret(prompt, target)

    def technical_with_active_provider(self, prompt: str, target: str) -> dict[str, object]:
        provider = self.technical_providers[0]
        return provider.interpret(prompt, target)

    def llama_cpp_status(self) -> dict[str, object]:
        if self.local_settings is None:
            return {"enabled": False, "available": False, "reason": "No local settings loaded"}
        if not self.local_settings.llama_cpp_enabled:
            return {
                "enabled": False,
                "available": False,
                "base_url": self.local_settings.llama_cpp_base_url,
                "reason": "Set SONG_AI_LLAMA_CPP_ENABLED=true para activar Gemma via llama.cpp.",
            }
        provider = next(
            (item for item in self.interpreter_providers if isinstance(item, LlamaCppInterpreterProvider)),
            None,
        )
        if provider is None:
            return {"enabled": True, "available": False, "reason": "Proveedor llama.cpp no registrado."}
        return {"enabled": True, "base_url": self.local_settings.llama_cpp_base_url, **provider.status()}

    def model_status(self) -> dict[str, object]:
        local = self.local_settings.to_dict() if self.local_settings is not None else {}
        if self.hf_settings is None:
            return {
                "local": local,
                "external": {"enabled": False, "reason": "Build local-only: providers remotos/pro desactivados."},
            }
        return {
            "local": local,
            "external": {
                "enabled": False,
                "configured": self.hf_settings.enabled,
                "reason": "Build local-only: no se registran providers HuggingFace/pro en el pipeline activo.",
            },
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

    def local_pipeline_status(self) -> dict[str, object]:
        if self.local_settings is None:
            return {
                "mode": "local_only",
                "ready": False,
                "missing": ["settings"],
                "requirements": [],
            }
        full_song_configured = bool(self.local_settings.full_song_command.strip())
        soundtrack_configured = bool(self.local_settings.soundtrack_command.strip())
        singing_voice_configured = bool(self.local_settings.singing_voice_command.strip())
        stems_required = not full_song_configured
        requirements = [
            {
                "role": "full_song",
                "engine": "ACE-Step",
                "model": "ACE-Step local command",
                "required_for_real_output": True,
                "configured": full_song_configured,
                "detail": "Ruta principal: genera cancion completa con voz integrada.",
            },
            {
                "role": "interpreter_and_lyrics",
                "engine": "llama.cpp",
                "model": self.local_settings.interpreter_model,
                "required_for_real_output": False,
                "configured": self.local_settings.llama_cpp_enabled,
                "detail": "Recomendado para Gemma/Qwen reales; la app conserva guia local si llama.cpp no responde.",
            },
            {
                "role": "soundtrack",
                "engine": "MusicGen",
                "model": self.local_settings.soundtrack_model,
                "required_for_real_output": stems_required,
                "configured": soundtrack_configured,
                "detail": "Ruta alternativa por stems; no es necesaria si Full Song esta configurado.",
            },
            {
                "role": "singing_voice",
                "engine": self.local_settings.singing_voice_engine,
                "model": self.local_settings.singing_voice_engine,
                "required_for_real_output": stems_required,
                "configured": singing_voice_configured,
                "detail": "Ruta alternativa para vocals.wav separado; no es necesaria si Full Song esta configurado.",
            },
            {
                "role": "stems",
                "engine": "Demucs",
                "model": self.local_settings.stems_model,
                "required_for_real_output": False,
                "configured": True,
            },
            {
                "role": "mix_and_export",
                "engine": "ffmpeg",
                "model": self.local_settings.mixer_engine,
                "required_for_real_output": True,
                "configured": True,
            },
        ]
        missing = [
            str(item["role"])
            for item in requirements
            if item["required_for_real_output"] and not item["configured"]
        ]
        return {
            "mode": "local_only",
            "ready": len(missing) == 0,
            "missing": missing,
            "requirements": requirements,
            "note": "El pipeline final de esta version debe ejecutarse localmente; el modo pro no esta disponible.",
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
        if provider_name == "local-soundtrack-command":
            if self.local_settings is not None and self.local_settings.soundtrack_command.strip():
                return "configured"
            return "requires_configuration"
        if provider_name == "local-singing-voice-command":
            if self.local_settings is not None and self.local_settings.singing_voice_command.strip():
                return "configured"
            return "requires_configuration"
        if provider_name.startswith(("local-", "llamacpp-", "musicgen-", "singing-voice-")):
            if provider_name.startswith("llamacpp-") and self.local_settings is not None:
                return "configured" if self.local_settings.llama_cpp_enabled else "disabled"
            return "ready"
        return "unknown"
