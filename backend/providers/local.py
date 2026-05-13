from providers.base import InterpreterProvider, LyricsProvider, MusicProvider, VoiceProvider


class LocalInterpreterProvider(InterpreterProvider):
    def name(self) -> str:
        return "llamacpp-gemma-interpreter-mock"

    def capabilities(self) -> list[str]:
        return [
            "understand_user_intent",
            "infer_missing_song_details",
            "choose_lullaby_style_tone_structure",
            "coordinate_handoffs_without_prompt_chaining",
        ]

    def interpret(self, text: str, target: str) -> dict[str, object]:
        return {
            "target": target,
            "input": text,
            "mode": "local_mock",
            "summary": "Interpretacion local sin API real, lista para persistirse como estado.",
        }


class LocalMusicProvider(MusicProvider):
    def name(self) -> str:
        return "musicgen-soundtrack-mock"

    def capabilities(self) -> list[str]:
        return [
            "lullaby_soundtrack_prompt",
            "instrumental_draft",
            "music_box_piano_pads_strings",
            "sample_mock",
            "full_song_mock",
        ]


class LocalVoiceProvider(VoiceProvider):
    def name(self) -> str:
        return "singing-voice-rvc-acestep-mock"

    def capabilities(self) -> list[str]:
        return ["sung_vocal_mock", "vocal_guide_mock", "timbre_adaptation_placeholder", "not_tts_spoken_voice"]


class LocalLyricsProvider(LyricsProvider):
    def name(self) -> str:
        return "llamacpp-gemma-lyrics-mock"

    def capabilities(self) -> list[str]:
        return [
            "complete_original_lyrics",
            "meter_and_rhyme_guidance",
            "verse_chorus_bridge_structure",
            "avoid_poor_repetition",
            "music_prompt_generation",
        ]
