from __future__ import annotations

from array import array
from pathlib import Path
import shutil
import subprocess
import wave

from core.storage import StorageManager
from models.song_workflow import SongPhase, SongPhaseStatus


class MasteringService:
    SAMPLE_RATE = 44100

    def __init__(self, storage: StorageManager) -> None:
        self.storage = storage

    def master(self, song_id: str) -> dict[str, object]:
        project_dir = self.storage.data_dir / "projects" / song_id
        mix_path = project_dir / "mix.wav"
        final_wav_path = project_dir / "final_song.wav"
        final_mp3_path = project_dir / "final_song.mp3"
        log_path = project_dir / "mastering.log"
        if not mix_path.exists():
            raise ValueError("No existe mix.wav para masterizar.")

        frames = self._read_wav(mix_path)
        mastered = self._master_frames(frames)
        self._write_wav(final_wav_path, mastered)
        self._export_mp3(final_wav_path, final_mp3_path)
        log_path.write_text(
            "Mastering local: filtro de limpieza DC, normalizacion, limitador suave y export MP3.\n"
            f"Mix: {mix_path}\nWAV final: {final_wav_path}\nMP3 final: {final_mp3_path}\n",
            encoding="utf-8",
        )
        wav_artifact = self.storage.create_song_artifact(
            artifact_id=f"{song_id}_final_song_wav",
            song_id=song_id,
            phase=SongPhase.MASTERING.value,
            artifact_type="final_song_wav",
            file_path=str(Path(final_wav_path)),
            metadata={"source_mix": str(mix_path), "log_path": str(log_path)},
        )
        mp3_artifact = self.storage.create_song_artifact(
            artifact_id=f"{song_id}_final_song_mp3",
            song_id=song_id,
            phase=SongPhase.MASTERING.value,
            artifact_type="final_song_mp3",
            file_path=str(Path(final_mp3_path)),
            metadata={"source_wav": str(final_wav_path), "log_path": str(log_path)},
        )
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.MASTERING.value,
            status=SongPhaseStatus.COMPLETED.value,
            progress=100,
            message="Mastering terminado: final_song.wav y final_song.mp3 listos para export.",
            active_model="local-mastering",
            payload={
                "final_wav": str(final_wav_path),
                "final_mp3": str(final_mp3_path),
                "log": str(log_path),
            },
            artifact_id=str(mp3_artifact["artifact_id"]),
        )
        project = self.storage.update_song_project_phase(song_id, SongPhase.EXPORT.value, SongPhaseStatus.READY.value)
        return {
            "project": project,
            "final_wav": str(final_wav_path),
            "final_mp3": str(final_mp3_path),
            "artifacts": [wav_artifact, mp3_artifact],
            "log": str(log_path),
        }

    def get(self, song_id: str) -> dict[str, object]:
        project_dir = self.storage.data_dir / "projects" / song_id
        final_wav_path = project_dir / "final_song.wav"
        final_mp3_path = project_dir / "final_song.mp3"
        if not final_wav_path.exists() or not final_mp3_path.exists():
            raise ValueError("Este proyecto aun no tiene final_song.wav y final_song.mp3.")
        return {
            "song_id": song_id,
            "final_wav": str(final_wav_path),
            "final_mp3": str(final_mp3_path),
            "wav_size_bytes": final_wav_path.stat().st_size,
            "mp3_size_bytes": final_mp3_path.stat().st_size,
        }

    def _read_wav(self, path: Path) -> list[int]:
        with wave.open(str(path), "rb") as wav_file:
            frames = wav_file.readframes(wav_file.getnframes())
            samples = array("h")
            samples.frombytes(frames)
            if wav_file.getnchannels() > 1:
                samples = array("h", samples[:: wav_file.getnchannels()])
            return list(samples)

    def _write_wav(self, path: Path, frames: list[int]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.SAMPLE_RATE)
            wav_file.writeframes(array("h", frames).tobytes())

    def _master_frames(self, frames: list[int]) -> list[int]:
        if not frames:
            raise ValueError("mix.wav no contiene audio.")
        dc_offset = sum(frames) / len(frames)
        cleaned = [sample - dc_offset for sample in frames]
        peak = max(1.0, max(abs(value) for value in cleaned))
        target_peak = 31000.0
        gain = target_peak / peak
        mastered: list[int] = []
        for value in cleaned:
            boosted = value * gain
            limited = target_peak * (boosted / (target_peak + abs(boosted)))
            mastered.append(self._clip(limited * 1.18))
        return mastered

    def _export_mp3(self, final_wav_path: Path, final_mp3_path: Path) -> None:
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path is None:
            raise ValueError("ffmpeg no esta disponible para exportar final_song.mp3.")
        subprocess.run(
            [
                ffmpeg_path,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(final_wav_path),
                "-codec:a",
                "libmp3lame",
                "-q:a",
                "2",
                str(final_mp3_path),
            ],
            check=True,
        )

    def _clip(self, value: float) -> int:
        return max(-32767, min(32767, int(value)))
