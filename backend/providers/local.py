from providers.base import LyricsProvider, MusicProvider, VoiceProvider


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
