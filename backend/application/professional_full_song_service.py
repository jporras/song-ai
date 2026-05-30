from __future__ import annotations

import os
from pathlib import Path
import importlib.machinery
import signal
import shutil
import subprocess
import sys
import time

from audio.resource_monitor import ResourceMonitor
from config.resource_settings import ResourceMonitorSettings
from core.storage import StorageManager
from models.song_workflow import SongPhase, SongPhaseStatus


class ProfessionalFullSongService:
    def __init__(
        self,
        storage: StorageManager,
        command_template: str = "",
        timeout_seconds: int = 3600,
        resource_settings: ResourceMonitorSettings | None = None,
    ) -> None:
        self.storage = storage
        self.command_template = command_template.strip()
        self.timeout_seconds = timeout_seconds
        self.resource_monitor = ResourceMonitor(storage, resource_settings or ResourceMonitorSettings.load())

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
        diagnostics_path = project_dir / "ace_step_diagnostics.json"

        if not lyrics_path.exists():
            raise ValueError("La letra editable lyrics.md debe existir antes de generar la cancion completa.")
        self._assert_required_dependencies()

        prompt_path.write_text(self._build_prompt(project), encoding="utf-8")
        self._run_command(project, project_dir, prompt_path, lyrics_path, final_wav_path, log_path, diagnostics_path)
        after_audio = self.resource_monitor.capture(phase="after_audio", persist=True)
        self._assert_audio(final_wav_path)
        self._export_mp3(final_wav_path, final_mp3_path)
        self._export_flac(final_wav_path, final_flac_path)

        common_metadata = {
            "generation_mode": "local_full_song_command",
            "quality_status": "final_candidate",
            "prompt_path": str(prompt_path),
            "lyrics_path": str(lyrics_path),
            "log_path": str(log_path),
            "diagnostics_path": str(diagnostics_path),
            "after_audio_snapshot": after_audio["id"],
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
        project: dict[str, object],
        project_dir: Path,
        prompt_path: Path,
        lyrics_path: Path,
        output_path: Path,
        log_path: Path,
        diagnostics_path: Path,
    ) -> None:
        command = self.command_template.format(
            prompt_path=str(prompt_path),
            lyrics_path=str(lyrics_path),
            output_path=str(output_path),
            work_dir=str(project_dir),
            log_path=str(log_path),
            diagnostics_path=str(diagnostics_path),
            duration_seconds=self._duration_seconds(project),
        )
        prep = self.resource_monitor.prepare_for_audio(
            phase=SongPhase.MASTERING.value,
            event_callback=lambda message: self.storage.create_song_event(
                song_id=str(project["id"]),
                phase=SongPhase.MASTERING.value,
                status=SongPhaseStatus.RUNNING.value,
                progress=20,
                message=message,
                active_model="resource-monitor",
                payload={},
            ),
        )
        self.storage.create_song_event(
            song_id=str(project["id"]),
            phase=SongPhase.MASTERING.value,
            status=SongPhaseStatus.RUNNING.value,
            progress=30,
            message="ACE-Step: recursos preparados; iniciando proceso local de audio.",
            active_model="ace-step",
            payload={
                "command": command,
                "log_path": str(log_path),
                "diagnostics_path": str(diagnostics_path),
                "output_path": str(output_path),
                "duration_seconds": self._duration_seconds(project),
                "readiness": prep.get("readiness", {}),
            },
        )
        with log_path.open("w", encoding="utf-8") as log_file:
            log_file.write(f"$ {command}\n\n")
            log_file.write("ACE_STEP_INTEGRATION: mode=python_library_via_cli_process entrypoint=tools/acestep_generate.py service_api=false\n")
            log_file.write(f"ACE_STEP_DIAGNOSTICS: {diagnostics_path}\n")
            log_file.write(f"MODEL: checkpoint_path={self._checkpoint_path_from_command(command)}\n")
            log_file.write(f"DURATION_REQUESTED_SECONDS: {self._duration_seconds(project)}\n")
            log_file.write("OUTPUT_TYPE: full_song_with_vocals\n")
            log_file.write("PROMPT_BEGIN\n")
            log_file.write(prompt_path.read_text(encoding="utf-8"))
            log_file.write("\nPROMPT_END\n")
            log_file.write("LYRICS_BEGIN\n")
            log_file.write(lyrics_path.read_text(encoding="utf-8"))
            log_file.write("\nLYRICS_END\n\n")
            log_file.write(f"RESOURCE_READINESS: {prep['readiness']}\n\n")
            log_file.flush()
            process = None
            return_code = 1
            snapshots: list[dict[str, object]] = []
            started_at = time.monotonic()
            last_progress_event = started_at
            try:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=self._command_env(),
                    start_new_session=True,
                )
                self.storage.create_song_event(
                    song_id=str(project["id"]),
                    phase=SongPhase.MASTERING.value,
                    status=SongPhaseStatus.RUNNING.value,
                    progress=40,
                    message="ACE-Step: proceso iniciado; generando audio con voz integrada.",
                    active_model="ace-step",
                    payload={"pid": process.pid, "log_path": str(log_path), "output_path": str(output_path)},
                )
                while True:
                    return_code = process.poll()
                    if return_code is not None:
                        break
                    now = time.monotonic()
                    if now - started_at > self.timeout_seconds:
                        self._terminate_process(process)
                        log_file.write(f"\nTIMEOUT despues de {self.timeout_seconds} segundos.\n")
                        log_file.flush()
                        raise ValueError(f"El provider full-song tardo demasiado. Timeout: {self.timeout_seconds} segundos.")
                    snapshot = self.resource_monitor.capture(phase="audio_generation", persist=True)
                    snapshots.append(snapshot)
                    log_file.write(
                        "RESOURCE_SAMPLE: "
                        f"ram_available_mb={snapshot['ram_available_mb']} "
                        f"ram_used_percent={snapshot['ram_used_percent']} "
                        f"ram_total_mb={snapshot['ram_total_mb']} "
                        f"swap_used_mb={snapshot.get('swap_used_mb', 0)} "
                        f"swap_free_mb={snapshot.get('swap_free_mb', 0)} "
                        f"cpu_percent={snapshot['cpu_percent']} "
                        f"vram={snapshot.get('vram', [])}\n"
                    )
                    if now - last_progress_event >= 60:
                        last_progress_event = now
                        elapsed = now - started_at
                        self.storage.create_song_event(
                            song_id=str(project["id"]),
                            phase=SongPhase.MASTERING.value,
                            status=SongPhaseStatus.RUNNING.value,
                            progress=55,
                            message=(
                                "ACE-Step: generando audio "
                                f"({elapsed / 60:.1f} min). "
                                f"RAM libre {float(snapshot['ram_available_mb']):.0f} MB, "
                                f"swap libre {float(snapshot.get('swap_free_mb', 0)):.0f} MB, "
                                f"CPU {float(snapshot['cpu_percent']):.0f}%."
                            ),
                            active_model="ace-step",
                            payload={
                                "elapsed_seconds": elapsed,
                                "ram_available_mb": snapshot["ram_available_mb"],
                                "swap_free_mb": snapshot.get("swap_free_mb", 0),
                                "swap_total_mb": snapshot.get("swap_total_mb", 0),
                                "cpu_percent": snapshot["cpu_percent"],
                                "log_path": str(log_path),
                            },
                        )
                    log_file.flush()
            finally:
                self.resource_monitor.restore_text_models(
                    event_callback=lambda message: self.storage.create_song_event(
                        song_id=str(project["id"]),
                        phase=SongPhase.MASTERING.value,
                        status=SongPhaseStatus.RUNNING.value,
                        progress=80,
                        message=message,
                        active_model="resource-monitor",
                        payload={},
                    )
                )
            duration = time.monotonic() - started_at
            if snapshots:
                min_ram = min(float(item["ram_available_mb"]) for item in snapshots)
                peak_ram_percent = max(float(item["ram_used_percent"]) for item in snapshots)
                min_swap = min(float(item.get("swap_free_mb", 0)) for item in snapshots)
                peak_swap_used = max(float(item.get("swap_used_mb", 0)) for item in snapshots)
                avg_cpu = sum(float(item["cpu_percent"]) for item in snapshots) / len(snapshots)
                log_file.write(
                    "\nRESOURCE_SUMMARY: "
                    f"duration_seconds={duration:.1f} "
                    f"min_ram_available_mb={min_ram:.0f} "
                    f"min_swap_free_mb={min_swap:.0f} "
                    f"peak_swap_used_mb={peak_swap_used:.0f} "
                    f"peak_ram_used_percent={peak_ram_percent:.1f} "
                    f"avg_cpu_percent={avg_cpu:.1f}\n"
                )
                self.storage.create_song_event(
                    song_id=str(project["id"]),
                    phase=SongPhase.MASTERING.value,
                    status=SongPhaseStatus.RUNNING.value,
                    progress=75,
                    message=(
                        "ResourceMonitor audio: "
                        f"RAM minima {min_ram:.0f} MB, swap libre minimo {min_swap:.0f} MB, "
                        f"CPU promedio {avg_cpu:.0f}%, duracion {duration:.0f}s."
                    ),
                    active_model="resource-monitor",
                    payload={
                        "duration_seconds": duration,
                        "min_ram_available_mb": min_ram,
                        "min_swap_free_mb": min_swap,
                        "peak_swap_used_mb": peak_swap_used,
                        "peak_ram_used_percent": peak_ram_percent,
                        "avg_cpu_percent": avg_cpu,
                    },
                )

        if return_code != 0:
            detail = log_path.read_text(encoding="utf-8")[-4000:].strip()
            raise ValueError(f"El provider full-song fallo: {detail}")

    def _terminate_process(self, process: subprocess.Popen[str]) -> None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except Exception:
            process.kill()

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

    def _duration_seconds(self, project: dict[str, object]) -> int:
        spec = dict(dict(project.get("spec") or {}).get("json_spec", {}))
        try:
            duration = int(float(spec.get("duration_seconds", 60)))
        except (TypeError, ValueError):
            duration = 60
        try:
            max_duration = int(os.getenv("SONG_AI_MAX_FULL_SONG_DURATION_SECONDS", "360"))
        except ValueError:
            max_duration = 360
        return max(5, min(duration, max(5, max_duration)))

    def _command_env(self) -> dict[str, str]:
        env = os.environ.copy()
        provider_cache = os.getenv("SONG_AI_PROVIDER_CACHE", str(Path.cwd() / "data" / "provider-cache"))
        provider_path = str(Path(provider_cache) / "python")
        existing_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = provider_path + (os.pathsep + existing_pythonpath if existing_pythonpath else "")
        return env

    def _checkpoint_path_from_command(self, command: str) -> str:
        parts = command.split()
        for index, part in enumerate(parts):
            if part == "--checkpoint-path" and index + 1 < len(parts):
                return parts[index + 1]
        return ""

    def _assert_required_dependencies(self) -> None:
        if "acestep_generate.py" not in self.command_template and "ace-step" not in self.command_template.lower():
            return
        provider_cache = os.getenv("SONG_AI_PROVIDER_CACHE", str(Path.cwd() / "data" / "provider-cache"))
        provider_path = Path(provider_cache) / "python"
        search_paths = [str(provider_path), *sys.path]
        if importlib.machinery.PathFinder.find_spec("torchcodec", search_paths) is None:
            raise ValueError("Falta torchcodec. Ejecuta scripts\\install-local-prereqs.ps1 antes de generar con ACE-Step.")

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
