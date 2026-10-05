from __future__ import annotations

from dataclasses import dataclass
import importlib.machinery
import os
from pathlib import Path
import shutil
import subprocess
import sys

from audio.ace_step_profiles import AceStepProfile, apply_ace_step_profile_env, resolve_ace_step_profile
from audio.ace_step_commands import normalize_ace_step_template
from audio.mock_song_renderer import MockSongRenderContext
from audio.accelerator_detection import torch_accelerator_snapshot
from audio.resource_monitor import ResourceMonitor
from config.model_settings import LocalModelSettings


@dataclass(frozen=True)
class LocalPipelineStatus:
    ready: bool
    missing: list[str]
    requirements: list[dict[str, object]]


class LocalSongPipeline:
    def __init__(self, settings: LocalModelSettings, resource_monitor: ResourceMonitor | None = None) -> None:
        self.settings = settings
        self.resource_monitor = resource_monitor
        self._full_song_available_cache: bool | None = None
        self._full_song_unavailable_reason = ""

    def status(self) -> LocalPipelineStatus:
        full_song_configured = bool(self.settings.full_song_command.strip())
        full_song_available = self._full_song_command_available()
        requirements = [
            {
                "role": "full_song",
                "engine": "ACE-Step or compatible local command",
                "configured": full_song_configured and full_song_available,
                "detail": self._full_song_detail(full_song_configured, full_song_available),
                "path": "preferred",
                "runtime": self._full_song_runtime_status(full_song_configured and full_song_available),
                "device": self._recommended_device(),
                "accelerator": self._accelerator_summary(),
            },
            {
                "role": "soundtrack",
                "engine": self.settings.soundtrack_model,
                "configured": bool(self.settings.soundtrack_command.strip()),
                "detail": "Configura SONG_AI_SOUNDTRACK_COMMAND para generar instrumental.wav localmente.",
                "path": "stems",
            },
            {
                "role": "singing_voice",
                "engine": self.settings.singing_voice_engine,
                "configured": bool(self.settings.singing_voice_command.strip()),
                "detail": "Configura SONG_AI_SINGING_VOICE_COMMAND para generar vocals.wav localmente.",
                "path": "stems",
            },
            {
                "role": "mix_and_export",
                "engine": self.settings.mixer_engine,
                "configured": shutil.which("ffmpeg") is not None,
                "detail": "ffmpeg debe estar disponible para mezclar y exportar MP3.",
            },
        ]
        ffmpeg_ready = bool(requirements[-1]["configured"])
        full_song_ready = bool(requirements[0]["configured"]) and ffmpeg_ready
        stems_ready = bool(requirements[1]["configured"]) and bool(requirements[2]["configured"]) and ffmpeg_ready
        if full_song_configured:
            for requirement in requirements:
                if requirement["role"] in {"soundtrack", "singing_voice"}:
                    requirement["required_for_real_output"] = False
                    requirement["detail"] = (
                        f"{requirement['engine']} es ruta alternativa por stems; no es requerido "
                        "si Full Song por ACE-Step queda listo. Configuralo solo si quieres usar "
                        "instrumental y voz cantada como proveedores separados."
                    )
        missing = self._missing(requirements, full_song_ready, stems_ready)
        return LocalPipelineStatus(ready=full_song_ready or stems_ready, missing=missing, requirements=requirements)

    def generate(
        self,
        context: MockSongRenderContext,
        song_dir: Path,
        generation_profile: str | None = None,
    ) -> dict[str, object]:
        status = self.status()
        if not status.ready:
            raise ValueError(
                "No se puede generar una cancion final local todavia. Falta: "
                + ", ".join(status.missing)
                + ". Revisa /api/local-pipeline/status."
            )

        work_dir = song_dir / "local_pipeline"
        exports_dir = song_dir / "exports"
        stems_dir = song_dir / "stems"
        work_dir.mkdir(parents=True, exist_ok=True)
        exports_dir.mkdir(parents=True, exist_ok=True)
        stems_dir.mkdir(parents=True, exist_ok=True)

        prompt_path = work_dir / "music_prompt.txt"
        command_log_path = work_dir / "local_command.log"
        lyrics_path = exports_dir / "lyrics.md"
        instrumental_path = stems_dir / "instrumental.wav"
        vocals_path = stems_dir / "vocals.wav"
        final_wav_path = exports_dir / "final_mix.wav"
        final_mp3_path = exports_dir / "final_mix.mp3"

        prompt_path.write_text(self._build_music_prompt(context), encoding="utf-8")
        lyrics_path.write_text(context.lyrics_markdown.rstrip() + "\n", encoding="utf-8")

        if self.settings.full_song_command.strip() and self._full_song_command_available():
            profile = resolve_ace_step_profile(generation_profile)
            diagnostics_path = work_dir / "ace_step_diagnostics.json"
            self._prepare_audio_resources("full_song")
            try:
                self._run_template(
                    self.settings.full_song_command,
                    {
                        "prompt_path": prompt_path,
                        "lyrics_path": lyrics_path,
                        "output_path": final_wav_path,
                        "work_dir": work_dir,
                        "log_path": command_log_path,
                        "diagnostics_path": diagnostics_path,
                        "python_executable": Path(sys.executable),
                        "duration_seconds": self._estimated_duration_seconds(context),
                    },
                    profile,
                )
            finally:
                self._restore_text_models()
            self._assert_file(final_wav_path, "El comando local de cancion completa no genero final_mix.wav.")
            self._export_mp3(final_wav_path, final_mp3_path)
            return {
                "mode": "local_final_song",
                "wav": str(final_wav_path),
                "mp3": str(final_mp3_path),
                "stems": {},
                "prompt": str(prompt_path),
                "command_log": str(command_log_path),
                "ace_step_profile": profile.name,
                "ace_step_model_type": profile.model_type,
                "ace_step_model_repo": profile.model_repo,
                "note": "Cancion final generada con un comando local completo; no usa modo pro.",
            }

        self._prepare_audio_resources("singing_voice")
        try:
            self._run_template(
                self.settings.soundtrack_command,
                {
                    "prompt_path": prompt_path,
                    "lyrics_path": lyrics_path,
                    "output_path": instrumental_path,
                    "work_dir": work_dir,
                    "log_path": command_log_path,
                },
            )
            self._assert_file(instrumental_path, "El comando local de soundtrack no genero instrumental.wav.")

            self._run_template(
                self.settings.singing_voice_command,
                {
                    "prompt_path": prompt_path,
                    "lyrics_path": lyrics_path,
                    "instrumental_path": instrumental_path,
                    "output_path": vocals_path,
                    "work_dir": work_dir,
                    "log_path": command_log_path,
                },
            )
        finally:
            self._restore_text_models()
        self._assert_file(vocals_path, "El comando local de voz cantada no genero vocals.wav.")

        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path is None:
            raise ValueError("ffmpeg no esta disponible para mezclar/exportar.")
        if final_mp3_path.exists():
            final_mp3_path.unlink()

        subprocess.run(
            [
                ffmpeg_path,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(instrumental_path),
                "-i",
                str(vocals_path),
                "-filter_complex",
                "amix=inputs=2:duration=longest:normalize=1",
                str(final_wav_path),
            ],
            check=True,
        )
        self._export_mp3(final_wav_path, final_mp3_path)

        return {
            "mode": "local_final_song",
            "wav": str(final_wav_path),
            "mp3": str(final_mp3_path),
            "stems": {
                "instrumental": str(instrumental_path),
                "vocals": str(vocals_path),
            },
            "prompt": str(prompt_path),
            "command_log": str(command_log_path),
            "note": "Cancion final generada con herramientas locales configuradas; no usa modo pro.",
        }

    def _estimated_duration_seconds(self, context: MockSongRenderContext) -> int:
        lyric_lines = [
            line.strip()
            for line in context.lyrics_markdown.splitlines()
            if line.strip() and not line.lstrip().startswith("#") and ":" not in line
        ]
        estimated = max(18, len(lyric_lines) * 4)
        return min(self.settings.max_full_song_duration_seconds, estimated)

    def _run_template(self, template: str, values: dict[str, object], profile: AceStepProfile | None = None) -> None:
        format_values: dict[str, object] = {key: str(value) for key, value in values.items()}
        if profile is not None:
            format_values.update(profile.format_values())
        try:
            command = (normalize_ace_step_template(template) if profile else template).format(**format_values)
        except KeyError as error:
            missing = str(error).strip("'")
            raise ValueError(
                f"Falta valor para el token {{{missing}}} en el comando local de audio. "
                f"Tokens disponibles: {', '.join(sorted(format_values))}."
            ) from error
        except (IndexError, ValueError) as error:
            raise ValueError(f"El comando local de audio tiene formato invalido: {error}") from error
        log_path = values.get("log_path")
        if log_path is not None:
            Path(log_path).write_text(f"$ {command}\n", encoding="utf-8")
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                env=self._command_env(profile),
                timeout=self.settings.local_command_timeout_seconds,
            )
        except subprocess.TimeoutExpired as error:
            if log_path is not None:
                Path(log_path).write_text(
                    f"$ {command}\nTIMEOUT despues de {self.settings.local_command_timeout_seconds} segundos.\n"
                    f"{error.stdout or ''}\n{error.stderr or ''}",
                    encoding="utf-8",
                )
            raise ValueError(
                "El comando local tardo demasiado y fue detenido. "
                f"Timeout: {self.settings.local_command_timeout_seconds} segundos."
            ) from error
        if log_path is not None:
            Path(log_path).write_text(
                f"$ {command}\n\nSTDOUT:\n{result.stdout or ''}\n\nSTDERR:\n{result.stderr or ''}",
                encoding="utf-8",
            )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or command).strip()
            raise ValueError(f"El comando local fallo: {detail}")

    def _prepare_audio_resources(self, phase: str) -> None:
        if self.resource_monitor is None:
            return
        self.resource_monitor.prepare_for_audio(phase=phase)

    def _restore_text_models(self) -> None:
        if self.resource_monitor is None:
            return
        self.resource_monitor.restore_text_models()

    def _full_song_command_available(self) -> bool:
        command = self.settings.full_song_command.strip()
        self._full_song_unavailable_reason = ""
        if not command:
            return False
        if "acestep_generate.py" in command:
            if self._full_song_available_cache is True:
                return self._full_song_available_cache
            if importlib.machinery.PathFinder.find_spec("acestep") is None:
                self._full_song_unavailable_reason = (
                    "ACE-Step no esta importable en .venv. "
                    "Ejecuta scripts\\install-local-prereqs.ps1."
                )
                self._full_song_available_cache = False
                return False
            torchcodec_ready = importlib.machinery.PathFinder.find_spec("torchcodec") is not None
            soundfile_ready = importlib.machinery.PathFinder.find_spec("soundfile") is not None
            if not torchcodec_ready and not soundfile_ready:
                self._full_song_unavailable_reason = (
                    "Falta torchcodec o soundfile para audio I/O. "
                    "En Intel XPU ACE-Step usa soundfile como fallback; ejecuta scripts\\install-intel-xpu-prereqs.ps1 "
                    "o scripts\\install-local-prereqs.ps1."
                )
                self._full_song_available_cache = False
                return False
            self._full_song_available_cache = True
            return bool(self._full_song_available_cache)
        return True

    def _full_song_detail(self, configured: bool, available: bool) -> str:
        if not configured:
            return "Configura SONG_AI_FULL_SONG_COMMAND para generar final_mix.wav completo localmente."
        if not available:
            if self._full_song_unavailable_reason:
                return self._full_song_unavailable_reason
            return "ACE-Step esta configurado pero no instalado/importable. Ejecuta Preparar/reiniciar bootstrap o activa SONG_AI_INSTALL_ACE_STEP=true."
        if self._xpu_available():
            return "ACE-Step esta importable y Song-AI intentara Intel XPU automaticamente para acelerar la iGPU."
        if self._cuda_available():
            return "ACE-Step esta importable y hay CUDA disponible."
        if self.settings.allow_cpu_full_song:
            return (
                "ACE-Step esta importable y puede ejecutarse por CPU, pero es extremadamente lento. "
                "Instala PyTorch XPU/driver Intel para usar la iGPU o usa GPU compatible para duraciones largas."
            )
        return "Comando local completo disponible para generar final_mix.wav."

    def _full_song_runtime_status(self, available: bool) -> str:
        if not available:
            return "unavailable"
        if self._xpu_available():
            return "xpu_ready"
        if self._cuda_available():
            return "gpu_ready"
        if self.settings.allow_cpu_full_song:
            return "cpu_extremely_slow"
        return "gpu_required"

    def _cuda_available(self) -> bool:
        snapshot = self._torch_accelerator_snapshot()
        return bool(snapshot.get("cuda_available")) or Path("/dev/nvidia0").exists() or Path("/dev/nvidiactl").exists()

    def _xpu_available(self) -> bool:
        return bool(self._torch_accelerator_snapshot().get("xpu_available"))

    def _recommended_device(self) -> str:
        snapshot = self._torch_accelerator_snapshot()
        return str(snapshot.get("recommended_backend") or "cpu")

    def _accelerator_summary(self) -> dict[str, object]:
        snapshot = self._torch_accelerator_snapshot()
        return {
            "recommended_backend": snapshot.get("recommended_backend", "cpu"),
            "xpu_available": snapshot.get("xpu_available", False),
            "xpu_device_name": snapshot.get("xpu_device_name", ""),
            "cuda_available": snapshot.get("cuda_available", False),
            "cuda_device_name": snapshot.get("cuda_device_name", ""),
            "fallback_reason": snapshot.get("fallback_reason", ""),
            "soundfile_importable": snapshot.get("soundfile_importable", False),
            "torchcodec_importable": snapshot.get("torchcodec_importable", False),
        }

    def _torch_accelerator_snapshot(self) -> dict[str, object]:
        return torch_accelerator_snapshot(run_tensor_probe=False)

    def _command_env(self, profile: AceStepProfile | None = None) -> dict[str, str]:
        env = os.environ.copy()
        if profile is not None:
            apply_ace_step_profile_env(env, profile)
        return env

    def _assert_file(self, path: Path, message: str) -> None:
        if not path.exists() or path.stat().st_size == 0:
            raise ValueError(message)

    def _export_mp3(self, final_wav_path: Path, final_mp3_path: Path) -> None:
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path is None:
            raise ValueError("ffmpeg no esta disponible para exportar MP3.")
        subprocess.run(
            [
                ffmpeg_path,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(final_wav_path),
                str(final_mp3_path),
            ],
            check=True,
        )

    def _missing(
        self,
        requirements: list[dict[str, object]],
        full_song_ready: bool,
        stems_ready: bool,
    ) -> list[str]:
        if full_song_ready or stems_ready:
            return []
        missing: list[str] = []
        if not requirements[-1]["configured"]:
            missing.append("mix_and_export")
        if not requirements[0]["configured"]:
            missing.append("full_song")
        stems_are_optional = bool(requirements[1].get("required_for_real_output") is False) and bool(
            requirements[2].get("required_for_real_output") is False
        )
        if not stems_are_optional and (not requirements[1]["configured"] or not requirements[2]["configured"]):
            missing.append("soundtrack/singing_voice")
        return missing

    def _build_music_prompt(self, context: MockSongRenderContext) -> str:
        return "\n".join(
            [
                f"Project: {context.project_name}",
                f"Description: {context.description}",
                f"Instrumental intent: {context.instrumental_intent}",
                f"Vocal intent: {context.melody_intent}",
                f"Lyrical intent: {context.lyrics_intent}",
                "Goal: complete song with coherent soundtrack, sung voice, lyrics, melody and final mix.",
            ]
        )
