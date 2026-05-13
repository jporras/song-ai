from pathlib import Path
import math
import shutil
import subprocess
import wave

from audio.formats import planned_final_mix_exports, planned_stem_exports
from core.storage import StorageManager


class ExportBuilder:
    def __init__(self, storage: StorageManager) -> None:
        self.storage = storage

    def prepare_latest_song_exports(self) -> Path:
        latest_song = self.storage.get_latest_song()
        if latest_song is None:
            raise ValueError("No hay cancion completa para exportar.")

        song_dir = Path(str(latest_song["path"]))
        exports_dir = song_dir / "exports"
        stems_dir = song_dir / "stems"
        exports_dir.mkdir(parents=True, exist_ok=True)
        stems_dir.mkdir(parents=True, exist_ok=True)

        self.storage.write_json(
            exports_dir / "manifest.json",
            {
                "song_id": latest_song["song_id"],
                "mode": "mock_export",
                "final_mix_formats": planned_final_mix_exports(),
                "stem_formats": planned_stem_exports(),
            },
        )
        (exports_dir / "lyrics.md").write_text(
            "# Lyrics export placeholder\n\nLa letra final se copiara aqui cuando el builder use assets reales.\n",
            encoding="utf-8",
        )
        return exports_dir

    def generate_latest_song_audio_exports(self) -> Path:
        latest_song = self.storage.get_latest_song()
        if latest_song is None:
            raise ValueError("No hay cancion completa para exportar.")

        song_dir = Path(str(latest_song["path"]))
        exports_dir = self.prepare_latest_song_exports()
        wav_path = exports_dir / "final_mix.wav"
        mp3_path = exports_dir / "final_mix.mp3"
        self._write_mock_wav(wav_path)

        ffmpeg_path = shutil.which("ffmpeg")
        mp3_generated = False
        if ffmpeg_path:
            try:
                subprocess.run(
                    [
                        ffmpeg_path,
                        "-y",
                        "-hide_banner",
                        "-loglevel",
                        "error",
                        "-i",
                        str(wav_path),
                        str(mp3_path),
                    ],
                    check=True,
                )
                mp3_generated = True
            except subprocess.CalledProcessError:
                mp3_generated = False

        if not mp3_generated:
            (exports_dir / "final_mix.mp3.pending.txt").write_text(
                "MP3 pendiente: instala ffmpeg o usa el contenedor con ffmpeg para convertir final_mix.wav.\n",
                encoding="utf-8",
            )

        self.storage.write_json(
            exports_dir / "audio_export_manifest.json",
            {
                "song_id": latest_song["song_id"],
                "mode": "mock_audio_export",
                "source_song_dir": str(song_dir),
                "wav": str(wav_path),
                "mp3": str(mp3_path) if mp3_generated else "",
                "mp3_pending": not mp3_generated,
                "ffmpeg_available": ffmpeg_path is not None,
                "ffmpeg_path": ffmpeg_path or "",
                "note": (
                    "WAV mock valido para probar el flujo. Cuando existan providers reales, "
                    "este paso exportara la mezcla final de voz cantada + instrumental."
                ),
            },
        )
        return exports_dir

    def _write_mock_wav(self, path: Path) -> None:
        sample_rate = 44100
        duration_seconds = 2
        amplitude = 12000
        frequency = 440
        frame_count = sample_rate * duration_seconds
        with wave.open(str(path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            for frame in range(frame_count):
                value = int(amplitude * math.sin(2 * math.pi * frequency * frame / sample_rate))
                wav_file.writeframesraw(value.to_bytes(2, byteorder="little", signed=True))
