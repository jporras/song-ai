from providers.base import LyricsProvider, MusicProvider, VoiceProvider


class ProMusicProvider(MusicProvider):
    def name(self) -> str:
        return "pro-music-placeholder"

    def capabilities(self) -> list[str]:
        return ["future_remote_instrumental", "future_remote_stems", "future_remote_master"]


class ProVoiceProvider(VoiceProvider):
    def name(self) -> str:
        return "pro-voice-placeholder"

    def capabilities(self) -> list[str]:
        return ["future_remote_voice_preview", "future_remote_final_voice"]


class ProLyricsProvider(LyricsProvider):
    def name(self) -> str:
        return "pro-lyrics-placeholder"

    def capabilities(self) -> list[str]:
        return ["future_remote_lyrics", "future_remote_variations"]
