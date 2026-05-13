from pathlib import Path
import shutil

from core.storage import StorageManager


class AudioMixer:
    def __init__(self, storage: StorageManager) -> None:
        self.storage = storage

    def prepare_latest_song_mix(self) -> Path:
        latest_song = self.storage.get_latest_song()
        if latest_song is None:
            raise ValueError("No hay cancion completa. Crea una cancion antes de preparar mezcla.")

        song_dir = Path(str(latest_song["path"]))
        mix_dir = song_dir / "mix"
        mix_dir.mkdir(parents=True, exist_ok=True)
        ffmpeg_path = shutil.which("ffmpeg")
        self.storage.write_json(
            mix_dir / "mix_manifest.json",
            {
                "song_id": latest_song["song_id"],
                "mode": "mock_mix",
                "ffmpeg_available": ffmpeg_path is not None,
                "ffmpeg_path": ffmpeg_path or "",
                "inputs": ["soundtrack/instrumental", "sung_voice", "optional_demucs_stems"],
                "outputs": ["final_mix.wav", "final_mix.mp3"],
                "note": "La mezcla real debe combinar voz cantada e instrumental, normalizar volumen y exportar WAV/MP3.",
            },
        )
        (mix_dir / "mix.mock.txt").write_text(
            "Mock mix prepared for complete song.\n"
            f"Song: {latest_song['song_id']}\n"
            f"ffmpeg available: {ffmpeg_path is not None}\n"
            "Expected real mix: sung voice + soundtrack, normalized and exported as WAV/MP3.\n",
            encoding="utf-8",
        )
        return mix_dir
