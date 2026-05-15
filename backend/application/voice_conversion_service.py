from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

from core.storage import StorageManager
from models.song_workflow import SongPhase, SongPhaseStatus


class VoiceConversionService:
    def __init__(self, storage: StorageManager, command_template: str = "", timeout_seconds: int = 3600) -> None:
        self.storage = storage
        self.command_template = command_template.strip()
        self.timeout_seconds = timeout_seconds

    def run(self, song_id: str, voice_style: str) -> dict[str, object]:
        project_dir = self.storage.data_dir / "projects" / song_id
        vocals_path = project_dir / "vocals.wav"
        converted_path = project_dir / "vocals_converted.wav"
        log_path = project_dir / "voice_conversion.log"
        if not vocals_path.exists():
            raise ValueError("No existe vocals.wav para convertir.")

        if self.command_template:
            mode = "local_command"
            status = SongPhaseStatus.COMPLETED.value
            message = "Conversion de voz aplicada con provider local."
            self._run_command(project_dir, vocals_path, converted_path, log_path)
        else:
            mode = "skipped_passthrough"
            status = SongPhaseStatus.SKIPPED.value
            message = "Conversion de voz omitida: no hay provider configurado; se usa vocals.wav como voz final."
            shutil.copyfile(vocals_path, converted_path)
            log_path.write_text(
                "VOICE_CONVERSION omitida porque SONG_AI_VOICE_CONVERSION_COMMAND no esta configurado.\n",
                encoding="utf-8",
            )

        artifact = self.storage.create_song_artifact(
            artifact_id=f"{song_id}_vocals_converted_wav",
            song_id=song_id,
            phase=SongPhase.VOICE_CONVERSION.value,
            artifact_type="vocals_converted_wav",
            file_path=str(Path(converted_path)),
            metadata={"mode": mode, "voice_style": voice_style, "log_path": str(log_path)},
        )
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.VOICE_CONVERSION.value,
            status=status,
            progress=100,
            message=message,
            active_model="rvc-or-compatible" if self.command_template else "none",
            payload={"vocals_converted": str(converted_path), "mode": mode, "log": str(log_path)},
            artifact_id=str(artifact["artifact_id"]),
        )
        project = self.storage.update_song_project_phase(song_id, SongPhase.MIXING.value, SongPhaseStatus.READY.value)
        return {
            "project": project,
            "vocals_converted": str(converted_path),
            "mode": mode,
            "artifact": artifact,
            "log": str(log_path),
        }

    def get(self, song_id: str) -> dict[str, object]:
        converted_path = self.storage.data_dir / "projects" / song_id / "vocals_converted.wav"
        if not converted_path.exists():
            raise ValueError("Este proyecto aun no tiene vocals_converted.wav.")
        return {
            "song_id": song_id,
            "vocals_converted": str(converted_path),
            "size_bytes": converted_path.stat().st_size,
        }

    def _run_command(self, project_dir: Path, vocals_path: Path, converted_path: Path, log_path: Path) -> None:
        command = self.command_template.format(
            input_path=str(vocals_path),
            vocals_path=str(vocals_path),
            output_path=str(converted_path),
            work_dir=str(project_dir),
        )
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
        )
        log_path.write_text(
            f"$ {command}\n\nSTDOUT:\n{result.stdout or ''}\n\nSTDERR:\n{result.stderr or ''}",
            encoding="utf-8",
        )
        if result.returncode != 0:
            raise ValueError(f"El provider local de conversion de voz fallo: {(result.stderr or result.stdout).strip()}")
        if not converted_path.exists() or converted_path.stat().st_size == 0:
            raise ValueError("El provider local de conversion de voz no genero vocals_converted.wav.")
