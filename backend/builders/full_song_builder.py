from pathlib import Path

from audio.formats import planned_final_mix_exports, planned_stem_exports
from core.storage import StorageManager
from utils.ids import generate_id


class FullSongBuilder:
    def __init__(self, storage: StorageManager) -> None:
        self.storage = storage

    def create_from_latest_sample(self) -> Path:
        latest_sample = self.storage.get_latest_sample()
        if latest_sample is None:
            raise ValueError("No hay sample valido. Genera un sample antes de crear la cancion completa.")

        song_id = generate_id("song")
        song_dir = self.storage.data_dir / "songs" / song_id
        exports_dir = song_dir / "exports"
        stems_dir = song_dir / "stems"
        song_dir.mkdir(parents=True, exist_ok=True)
        exports_dir.mkdir(parents=True, exist_ok=True)
        stems_dir.mkdir(parents=True, exist_ok=True)
        self.storage.write_json(
            song_dir / "song.json",
            {
                "song_id": song_id,
                "sample_id": latest_sample["sample_id"],
                "set_id": latest_sample["set_id"],
                "provider": "mock-local",
                "status": "mock_complete_song_pipeline",
                "scope": "complete_lullaby_or_children_emotional_song",
                "priority_order": [
                    "good_lyrics",
                    "emotional_intent",
                    "musical_structure",
                    "coherent_soundtrack",
                    "sung_voice",
                    "final_mix",
                ],
                "required_pipeline": {
                    "interpreter": "Gemma 2 2B IT GGUF via llama.cpp",
                    "lyrics": "Gemma 2 2B IT GGUF via llama.cpp",
                    "technical": "Qwen3 4B GGUF via llama.cpp",
                    "soundtrack": "MusicGen small, MusicGen medium if hardware allows",
                    "singing_voice": "RVC / ACE-Step, so-vits-svc optional",
                    "stems": "Demucs",
                    "mixer": "ffmpeg",
                },
                "restrictions": {
                    "not_short_format": True,
                    "avoid_poor_repetition": True,
                    "voice_must_be_sung": True,
                    "video_optional": True,
                    "load_models_on_demand": True,
                },
                "exports_dir": str(exports_dir),
                "stems_dir": str(stems_dir),
                "planned_exports": planned_final_mix_exports(),
                "planned_stems": planned_stem_exports(),
                "mock_exports": [
                    "exports/final_mix.mock.txt",
                    "exports/README.md",
                ],
            },
        )
        (exports_dir / "final_mix.mock.txt").write_text(
            "Mock full song placeholder.\n"
            f"Sample: {latest_sample['sample_id']}\n"
            f"Set: {latest_sample['set_id']}\n"
            "Scope: complete lullaby / emotional children song.\n"
            "Pipeline: lyrics, structure, soundtrack, sung voice, stems, mix, WAV/MP3 export.\n"
            "Video is optional and not required for song completion.\n",
            encoding="utf-8",
        )
        (exports_dir / "README.md").write_text(
            "# Song Exports\n\n"
            "Aqui quedaran los archivos reales cuando exista el pipeline de audio:\n\n"
            "- `final_mix.mp3`\n"
            "- `final_mix.m4a`\n"
            "- `final_mix.ogg`\n"
            "- `final_mix.wav`\n"
            "- `final_mix.flac`\n"
            "- `final_mix.aiff`\n"
            "- `lyrics.md`\n"
            "- `manifest.json`\n\n"
            "MP3/M4A/OGG son formatos comprimidos para distribucion. WAV/FLAC/AIFF son formatos de alta calidad o lossless.\n\n"
            "La cancion final debe ser una pieza completa con letra original, estructura musical, soundtrack, voz cantada y mezcla.\n"
            "No se considera completo un Short, una repeticion simple o TTS hablado.\n\n"
            "En esta fase mock solo se genera `final_mix.mock.txt`.\n",
            encoding="utf-8",
        )
        (stems_dir / "README.md").write_text(
            "# Song Stems\n\n"
            "Aqui quedaran stems reales cuando exista el pipeline de audio:\n\n"
            "- `instrumental.wav`\n"
            "- `vocals.wav`\n"
            "- `melody_guide.wav`\n"
            "- `drums.wav`\n"
            "- `bass.wav`\n"
            "- `music.wav`\n"
            "- versiones `.flac` cuando se requiera compresion lossless.\n"
            "- `demucs/` para separaciones futuras cuando el pipeline use Demucs.\n",
            encoding="utf-8",
        )
        return song_dir

