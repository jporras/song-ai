from providers.base import InterpreterProvider, LyricsProvider, MusicProvider, VoiceProvider


class LocalInterpreterProvider(InterpreterProvider):
    def name(self) -> str:
        return "local-interpreter-mock"

    def capabilities(self) -> list[str]:
        return ["intent_interpretation_mock", "project_guidance_mock", "handoff_planning_mock"]

    def interpret(self, text: str, target: str) -> dict[str, object]:
        return {
            "target": target,
            "input": text,
            "mode": "local_mock",
            "summary": "Interpretacion local sin API real, lista para persistirse como estado.",
        }


class LocalMusicProvider(MusicProvider):
    def name(self) -> str:
        return "local-music-mock"

    def capabilities(self) -> list[str]:
        return ["instrumental_draft", "sample_mock", "full_song_mock", "stems_mock"]


class LocalVoiceProvider(VoiceProvider):
    def name(self) -> str:
        return "local-voice-mock"

    def capabilities(self) -> list[str]:
        return ["voice_preview_mock", "vocal_guide_mock"]


class LocalLyricsProvider(LyricsProvider):
    def name(self) -> str:
        return "local-lyrics-mock"

    def capabilities(self) -> list[str]:
        return ["markdown_lyrics", "placeholder_variations", "promptless_mock_generation"]
