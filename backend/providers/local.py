from providers.base import InterpreterProvider, LyricsProvider, MusicProvider, VoiceProvider


class LocalInterpreterProvider(InterpreterProvider):
    def name(self) -> str:
        return "local-gemma-interpreter-fallback"

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
        return "local-soundtrack-command"

    def capabilities(self) -> list[str]:
        return [
            "generate_instrumental_wav_from_local_command",
            "uses_song_intent_and_music_prompt",
            "requires_song_ai_soundtrack_command",
            "local_only_no_pro_api",
        ]


class LocalVoiceProvider(VoiceProvider):
    def name(self) -> str:
        return "local-singing-voice-command"

    def capabilities(self) -> list[str]:
        return [
            "generate_sung_vocals_wav_from_local_command",
            "uses_lyrics_and_music_prompt",
            "requires_song_ai_singing_voice_command",
            "not_tts_spoken_voice",
        ]


class LocalLyricsProvider(LyricsProvider):
    def name(self) -> str:
        return "local-gemma-lyrics-fallback"

    def capabilities(self) -> list[str]:
        return [
            "complete_original_lyrics",
            "meter_and_rhyme_guidance",
            "verse_chorus_bridge_structure",
            "avoid_poor_repetition",
            "music_prompt_generation",
        ]


class LocalTechnicalProvider(InterpreterProvider):
    def name(self) -> str:
        return "local-qwen-technical-fallback"

    def capabilities(self) -> list[str]:
        return [
            "technical_adjustments",
            "debugging",
            "architecture_review",
            "pipeline_support",
            "ffmpeg_and_worker_guidance",
        ]

    def interpret(self, text: str, target: str) -> dict[str, object]:
        return {
            "target": target,
            "input": text,
            "mode": "local_mock",
            "summary": "Qwen tecnico mock: revisa arquitectura, errores, workers y pipeline sin intervenir en la letra creativa.",
        }
