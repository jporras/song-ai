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
                "status": "mock_full_song",
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
            f"Set: {latest_sample['set_id']}\n",
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
            "- versiones `.flac` cuando se requiera compresion lossless.\n",
            encoding="utf-8",
        )
        return song_dir

