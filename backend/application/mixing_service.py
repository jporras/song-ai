from __future__ import annotations

from array import array
from pathlib import Path
import wave

from core.storage import StorageManager
from models.song_workflow import SongPhase, SongPhaseStatus


class MixingService:
    SAMPLE_RATE = 44100

    def __init__(self, storage: StorageManager) -> None:
        self.storage = storage

    def mix(self, song_id: str) -> dict[str, object]:
        project_dir = self.storage.data_dir / "projects" / song_id
        instrumental_path = project_dir / "instrumental.wav"
        vocals_path = self._voice_path(project_dir)
        mix_path = project_dir / "mix.wav"
        log_path = project_dir / "mixing.log"
        if not instrumental_path.exists():
            raise ValueError("No existe instrumental.wav para mezclar.")
        if not vocals_path.exists():
            raise ValueError("No existe voz para mezclar.")

        instrumental = self._read_wav(instrumental_path)
        vocals = self._read_wav(vocals_path)
        mix = self._mix_frames(instrumental, vocals)
        self._write_wav(mix_path, mix)
        log_path.write_text(
            "Mezcla local: instrumental gain 0.72, vocal gain 0.88, reverb suave y normalizacion.\n"
            f"Instrumental: {instrumental_path}\nVoz: {vocals_path}\nSalida: {mix_path}\n",
            encoding="utf-8",
        )
        artifact = self.storage.create_song_artifact(
            artifact_id=f"{song_id}_mix_wav",
            song_id=song_id,
            phase=SongPhase.MIXING.value,
            artifact_type="mix_wav",
            file_path=str(Path(mix_path)),
            metadata={
                "instrumental": str(instrumental_path),
                "vocals": str(vocals_path),
                "log_path": str(log_path),
            },
        )
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.MIXING.value,
            status=SongPhaseStatus.COMPLETED.value,
            progress=100,
            message="Mezcla preparada con instrumental y voz, lista para mastering.",
            active_model="local-mixer",
            payload={"mix": str(mix_path), "log": str(log_path)},
            artifact_id=str(artifact["artifact_id"]),
        )
        project = self.storage.update_song_project_phase(song_id, SongPhase.MASTERING.value, SongPhaseStatus.READY.value)
        return {
            "project": project,
            "mix": str(mix_path),
            "artifact": artifact,
            "log": str(log_path),
        }

    def get(self, song_id: str) -> dict[str, object]:
        path = self.storage.data_dir / "projects" / song_id / "mix.wav"
        if not path.exists():
            raise ValueError("Este proyecto aun no tiene mix.wav.")
        return {
            "song_id": song_id,
            "mix": str(path),
            "size_bytes": path.stat().st_size,
        }

    def _voice_path(self, project_dir: Path) -> Path:
        converted = project_dir / "vocals_converted.wav"
        return converted if converted.exists() else project_dir / "vocals.wav"

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

    def _mix_frames(self, instrumental: list[int], vocals: list[int]) -> list[int]:
        length = max(len(instrumental), len(vocals))
        padded_instrumental = instrumental + [0] * (length - len(instrumental))
        padded_vocals = vocals + [0] * (length - len(vocals))
        delay = int(self.SAMPLE_RATE * 0.12)
        raw: list[float] = []
        for index in range(length):
            voice = padded_vocals[index] * 0.88
            if index >= delay:
                voice += padded_vocals[index - delay] * 0.12
            raw.append(padded_instrumental[index] * 0.72 + voice)
        peak = max(1.0, max(abs(value) for value in raw))
        scale = min(1.0, 30000 / peak)
        return [self._clip(value * scale) for value in raw]

    def _clip(self, value: float) -> int:
        return max(-32767, min(32767, int(value)))
