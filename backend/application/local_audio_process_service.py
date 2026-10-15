from __future__ import annotations

import os
import json
import re
from pathlib import Path
import importlib.machinery
import signal
import shutil
import subprocess
import time

from audio.ace_step_profiles import AceStepProfile, apply_ace_step_profile_env, resolve_ace_step_profile
from audio.resource_monitor import ResourceMonitor
from config.resource_settings import ResourceMonitorSettings
from core.storage import StorageManager
from models.song_workflow import SongPhase, SongPhaseStatus
from audio.ace_step_commands import normalize_ace_step_template
from adapters.ace_step_memory_budget import estimate_ace_step_memory


class LocalAudioProcessService:
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


    def _run_command(
        self,
        project: dict[str, object],
        project_dir: Path,
        prompt_path: Path,
        lyrics_path: Path,
        output_path: Path,
        log_path: Path,
        diagnostics_path: Path,
        profile: AceStepProfile,
        process_arguments: list[str] | None = None,
        revalidate=None,
        execution_phase: str = SongPhase.MASTERING.value,
        cancellation_check=None,
    ) -> None:
        command = subprocess.list2cmdline(process_arguments) if process_arguments is not None else self._format_command(project, project_dir, prompt_path, lyrics_path, output_path, log_path, diagnostics_path, profile)
        exploratory = process_arguments is not None and "exploratory_candidate" in process_arguments
        memory_budget = None
        if process_arguments is not None and any(str(arg).replace("\\", "/").endswith("tools/acestep_generate.py") for arg in process_arguments):
            lm_model = None
            if "--generation-api" in process_arguments and process_arguments[process_arguments.index("--generation-api") + 1] == "high_level_lm":
                if "--lm-model-path" not in process_arguments:
                    raise ValueError("El plan LM necesita un modelo explicito.")
                lm_model = process_arguments[process_arguments.index("--lm-model-path") + 1]
            memory_budget = estimate_ace_step_memory(Path(__file__).resolve().parents[2], profile, lm_model)
        prep = self.resource_monitor.prepare_for_audio(
            phase=execution_phase,
            required_ram_mb=memory_budget["required_ram_mb"] if memory_budget else None,
            event_callback=lambda message: self.storage.create_song_event(
                song_id=str(project["id"]),
                phase=execution_phase,
                status=SongPhaseStatus.RUNNING.value,
                progress=20,
                message=message,
                active_model="resource-monitor",
                payload={},
            ),
        )
        self.storage.create_song_event(
            song_id=str(project["id"]),
            phase=execution_phase,
            status=SongPhaseStatus.RUNNING.value,
            progress=30,
            message=("ACE-Step: recursos preparados; iniciando proceso local de audio."
                     if prep.get("readiness", {}).get("ready") is not False else
                     "ACE-Step: inicio bloqueado. " + str(prep["readiness"].get("message", "Revisa los recursos disponibles."))),
            active_model="ace-step",
            payload={
                "command": command,
                "log_path": str(log_path),
                "diagnostics_path": str(diagnostics_path),
                "output_path": str(output_path),
                "duration_seconds": self._duration_seconds(project),
                "provider_name": "ACE-Step",
                "ace_step_profile": profile.name,
                "ace_step_model_type": profile.model_type,
                "ace_step_model_repo": profile.model_repo,
                "infer_steps": profile.infer_steps,
                "threads": profile.threads,
                "requested_device": self._requested_device_from_command(command),
                "readiness": prep.get("readiness", {}),
                "memory_budget": memory_budget,
            },
        )
        with log_path.open("w", encoding="utf-8") as log_file:
            log_file.write(f"$ {command}\n\n")
            log_file.write("ACE_STEP_INTEGRATION: mode=python_library_via_cli_process entrypoint=tools/acestep_generate.py service_api=false\n")
            log_file.write(f"ACE_STEP_DIAGNOSTICS: {diagnostics_path}\n")
            log_file.write(
                "ACE_STEP_PROFILE: "
                f"name={profile.name} model_type={profile.model_type} model_repo={profile.model_repo} "
                f"infer_steps={profile.infer_steps} threads={profile.threads}\n"
            )
            log_file.write(f"MODEL: checkpoint_path={self._checkpoint_path_from_command(command)}\n")
            log_file.write(f"DURATION_REQUESTED_SECONDS: {self._duration_seconds(project)}\n")
            log_file.write(f"OUTPUT_TYPE: {'exploratory_candidate' if exploratory else 'full_song_with_vocals'}\n")
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
                if prep.get("readiness", {}).get("ready") is False:
                    raise ValueError("No hay recursos suficientes para iniciar audio. " + str(prep["readiness"].get("message", "Revisa memoria disponible.")))
                if cancellation_check is not None:
                    cancellation_check()
                if revalidate is not None:
                    revalidate()
                process = subprocess.Popen(
                    process_arguments if process_arguments is not None else command,
                    shell=process_arguments is None,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=self._command_env(profile),
                    start_new_session=True,
                )
                self.storage.create_song_event(
                    song_id=str(project["id"]),
                    phase=execution_phase,
                    status=SongPhaseStatus.RUNNING.value,
                    progress=40,
                    message="ACE-Step: proceso iniciado; generando borrador exploratorio." if exploratory else "ACE-Step: proceso iniciado; generando audio con voz integrada.",
                    active_model="ace-step",
                    payload={"pid": process.pid, "log_path": str(log_path), "output_path": str(output_path)},
                )
                while True:
                    if cancellation_check is not None:
                        cancellation_check()
                    return_code = process.poll()
                    if return_code is not None:
                        break
                    now = time.monotonic()
                    if now - started_at > self.timeout_seconds:
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
                            phase=execution_phase,
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
                                "intel_gpu": snapshot.get("accelerators", {}).get("intel_gpu", []),
                                "active_device": self._active_device_from_diagnostics(diagnostics_path),
                                "log_path": str(log_path),
                            },
                        )
                    log_file.flush()
            finally:
                # Monitoring, event persistence or validation may fail while the
                # child is still alive. Reap it before restoring text models.
                if process is not None and process.poll() is None:
                    self._terminate_process(process)
                self.resource_monitor.restore_text_models(
                    event_callback=lambda message: self.storage.create_song_event(
                        song_id=str(project["id"]),
                        phase=execution_phase,
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
                    phase=execution_phase,
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
            diagnostics = self._read_diagnostics(diagnostics_path)
            if diagnostics:
                runtime = dict(diagnostics.get("runtime", {}))
                error = dict(diagnostics.get("error", {}))
                self.storage.create_song_event(
                    song_id=str(project["id"]),
                    phase=execution_phase,
                    status=SongPhaseStatus.FAILED.value,
                    progress=75,
                    message=(
                        "ACE-Step fallo. "
                        f"Dispositivo activo: {runtime.get('active_device', 'desconocido')}. "
                        f"Fallback: {runtime.get('fallback_reason', '')}. "
                        f"Error: {error.get('message', '')}"
                    ),
                    active_model="ace-step",
                    payload={
                        "runtime": runtime,
                        "error": error,
                        "diagnostics_path": str(diagnostics_path),
                    },
                )
            detail = self._read_log_tail(log_path)
            raise ValueError(f"El provider full-song fallo: {detail}")


    def _format_command(
        self,
        project: dict[str, object],
        project_dir: Path,
        prompt_path: Path,
        lyrics_path: Path,
        output_path: Path,
        log_path: Path,
        diagnostics_path: Path,
        profile: AceStepProfile,
    ) -> str:
        values: dict[str, object] = {
            "python_executable": self._python_executable(),
            "prompt_path": str(prompt_path),
            "lyrics_path": str(lyrics_path),
            "output_path": str(output_path),
            "work_dir": str(project_dir),
            "log_path": str(log_path),
            "diagnostics_path": str(diagnostics_path),
            "duration_seconds": self._duration_seconds(project),
            **profile.format_values(),
        }
        try:
            return normalize_ace_step_template(self.command_template).format(**values)
        except KeyError as error:
            missing = str(error).strip("'")
            raise ValueError(
                f"Falta valor para el token {{{missing}}} en SONG_AI_FULL_SONG_COMMAND. "
                f"Tokens disponibles: {', '.join(sorted(values))}."
            ) from error
        except (IndexError, ValueError) as error:
            raise ValueError(f"SONG_AI_FULL_SONG_COMMAND tiene formato invalido: {error}") from error


    def _python_executable(self) -> str:
        venv_python = Path(".venv") / "Scripts" / "python.exe"
        if venv_python.exists():
            return str(venv_python)
        return "python"


    def _read_log_tail(self, log_path: Path, size: int = 4000) -> str:
        try:
            return log_path.read_text(encoding="utf-8", errors="replace")[-size:].strip()
        except OSError:
            return ""


    def _terminate_process(self, process: subprocess.Popen[str]) -> None:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15, check=False)
            if process.poll() is None:
                process.kill()
            process.wait(timeout=15)
            return
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except Exception:
            process.kill()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=15)


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


    def _command_env(self, profile: AceStepProfile | None = None) -> dict[str, str]:
        env = os.environ.copy()
        if profile is not None:
            apply_ace_step_profile_env(env, profile)
        return env


    def _checkpoint_path_from_command(self, command: str) -> str:
        parts = command.split()
        for index, part in enumerate(parts):
            if part == "--checkpoint-path" and index + 1 < len(parts):
                return parts[index + 1]
        return ""


    def _requested_device_from_command(self, command: str) -> str:
        parts = command.split()
        for index, part in enumerate(parts):
            if part == "--device" and index + 1 < len(parts):
                return parts[index + 1]
        return os.getenv("SONG_AI_ACE_DEVICE", "auto")


    def _read_diagnostics(self, path: Path) -> dict[str, object]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}


    def _active_device_from_diagnostics(self, path: Path) -> str:
        runtime = dict(self._read_diagnostics(path).get("runtime", {}))
        return str(runtime.get("active_device", ""))
