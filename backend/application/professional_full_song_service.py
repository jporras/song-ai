from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess

from core.storage import StorageManager
from models.song_workflow import SongPhase, SongPhaseStatus


class ProfessionalFullSongService:
    def __init__(self, storage: StorageManager, command_template: str = "", timeout_seconds: int = 3600) -> None:
        self.storage = storage
        self.command_template = command_template.strip()
        self.timeout_seconds = timeout_seconds

    def configured(self) -> bool:
        return bool(self.command_template)

    def generate(self, song_id: str) -> dict[str, object]:
        if not self.configured():
            raise ValueError("No hay provider full-song configurado.")

        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")

        project_dir = self.storage.data_dir / "projects" / song_id
        final_wav_path = project_dir / "final_song.wav"
        final_mp3_path = project_dir / "final_song.mp3"
        final_flac_path = project_dir / "final_song.flac"
        prompt_path = project_dir / "full_song_prompt.txt"
        lyrics_path = project_dir / "lyrics.md"
        log_path = project_dir / "full_song_generation.log"

        if not lyrics_path.exists():
            raise ValueError("La letra editable lyrics.md debe existir antes de generar la cancion completa.")

        prompt_path.write_text(self._build_prompt(project), encoding="utf-8")
        self._run_command(project_dir, prompt_path, lyrics_path, final_wav_path, log_path)
        self._assert_audio(final_wav_path)
        self._export_mp3(final_wav_path, final_mp3_path)
        self._export_flac(final_wav_path, final_flac_path)

        common_metadata = {
            "generation_mode": "local_full_song_command",
            "quality_status": "final_candidate",
            "prompt_path": str(prompt_path),
            "lyrics_path": str(lyrics_path),
            "log_path": str(log_path),
        }
        wav_artifact = self.storage.create_song_artifact(
            artifact_id=f"{song_id}_final_song_wav",
            song_id=song_id,
            phase=SongPhase.MASTERING.value,
            artifact_type="final_song_wav",
            file_path=str(final_wav_path),
            metadata={**common_metadata, "source": "full_song_provider"},
        )
        mp3_artifact = self.storage.create_song_artifact(
            artifact_id=f"{song_id}_final_song_mp3",
            song_id=song_id,
            phase=SongPhase.MASTERING.value,
            artifact_type="final_song_mp3",
            file_path=str(final_mp3_path),
            metadata={**common_metadata, "source_wav": str(final_wav_path)},
        )
        flac_artifact = self.storage.create_song_artifact(
            artifact_id=f"{song_id}_final_song_flac",
            song_id=song_id,
            phase=SongPhase.MASTERING.value,
            artifact_type="final_song_flac",
            file_path=str(final_flac_path),
            metadata={**common_metadata, "source_wav": str(final_wav_path)},
        )
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.MASTERING.value,
            status=SongPhaseStatus.COMPLETED.value,
            progress=100,
            message="Cancion completa generada con provider full-song local y exportada a WAV/MP3/FLAC.",
            active_model="local-full-song-provider",
            payload={
                "final_wav": str(final_wav_path),
                "final_mp3": str(final_mp3_path),
                "final_flac": str(final_flac_path),
                "generation_mode": "local_full_song_command",
                "log": str(log_path),
            },
            artifact_id=str(mp3_artifact["artifact_id"]),
        )
        project = self.storage.update_song_project_phase(song_id, SongPhase.EXPORT.value, SongPhaseStatus.READY.value)
        return {
            "project": project,
            "final_wav": str(final_wav_path),
            "final_mp3": str(final_mp3_path),
            "final_flac": str(final_flac_path),
            "artifacts": [wav_artifact, mp3_artifact, flac_artifact],
            "generation_mode": "local_full_song_command",
            "log": str(log_path),
        }

    def _run_command(
        self,
        project_dir: Path,
        prompt_path: Path,
        lyrics_path: Path,
        output_path: Path,
        log_path: Path,
    ) -> None:
        command = self.command_template.format(
            prompt_path=str(prompt_path),
            lyrics_path=str(lyrics_path),
            output_path=str(output_path),
            work_dir=str(project_dir),
            log_path=str(log_path),
        )
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                env=self._command_env(),
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as error:
            log_path.write_text(
                f"$ {command}\nTIMEOUT despues de {self.timeout_seconds} segundos.\n"
                f"{error.stdout or ''}\n{error.stderr or ''}",
                encoding="utf-8",
            )
            raise ValueError(f"El provider full-song tardo demasiado. Timeout: {self.timeout_seconds} segundos.") from error

        log_path.write_text(
            f"$ {command}\n\nSTDOUT:\n{result.stdout or ''}\n\nSTDERR:\n{result.stderr or ''}",
            encoding="utf-8",
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or command).strip()
            raise ValueError(f"El provider full-song fallo: {detail}")

    def _build_prompt(self, project: dict[str, object]) -> str:
        spec = dict(dict(project.get("spec") or {}).get("json_spec", {}))
        music_plan_path = self.storage.data_dir / "projects" / str(project["id"]) / "music_plan.json"
        music_plan = self.storage.read_json(music_plan_path) if music_plan_path.exists() else {}
        return "\n".join(
            [
                f"Title: {spec.get('title', project.get('title', 'Song AI'))}",
                f"Song type: {spec.get('song_type', '')}",
                f"Language: {spec.get('language', '')}",
                f"Emotion: {spec.get('emotion', '')}",
                f"Voice style: {spec.get('voice_style', '')}",
                f"Duration seconds: {spec.get('duration_seconds', music_plan.get('duration_seconds', ''))}",
                f"BPM: {spec.get('bpm', music_plan.get('bpm', ''))}",
                f"Key: {spec.get('key', music_plan.get('key', ''))}",
                f"Instruments: {', '.join(str(item) for item in list(spec.get('instruments', [])))}",
                "Goal: complete finished song with coherent instrumental, sung vocals, melody, lyrics and final mix.",
            ]
        )

    def _command_env(self) -> dict[str, str]:
        env = os.environ.copy()
        provider_cache = os.getenv("SONG_AI_PROVIDER_CACHE", "/app/provider-cache")
        provider_path = str(Path(provider_cache) / "python")
        existing_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = provider_path + (os.pathsep + existing_pythonpath if existing_pythonpath else "")
        return env

    def _assert_audio(self, path: Path) -> None:
        if not path.exists() or path.stat().st_size == 0:
            raise ValueError("El provider full-song no genero final_song.wav.")

    def _export_mp3(self, final_wav_path: Path, final_mp3_path: Path) -> None:
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path is None:
            raise ValueError("ffmpeg no esta disponible para exportar final_song.mp3.")
        subprocess.run(
            [ffmpeg_path, "-y", "-hide_banner", "-loglevel", "error", "-i", str(final_wav_path), str(final_mp3_path)],
            check=True,
        )

    def _export_flac(self, final_wav_path: Path, final_flac_path: Path) -> None:
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path is None:
            raise ValueError("ffmpeg no esta disponible para exportar final_song.flac.")
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
                "flac",
                str(final_flac_path),
            ],
            check=True,
        )
