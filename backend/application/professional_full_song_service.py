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
from application.local_audio_process_service import LocalAudioProcessService
from application.final_production_gate import FinalProductionGate
from audio.ace_step_commands import normalize_ace_step_template
from application.ace_step_plan_compiler import PreviewAceStepPlan
from application.ace_step_plan_review import ReviewAceStepPlan
from adapters.ace_step_source_audio import AceStepSourceAudio
from adapters.ace_step_execution import AceStepExecutionArguments
from adapters.sqlite.ace_step_plan_repository import AceStepPlanRepository
from audio.execution_lock import exclusive_audio
from adapters.ace_step_memory_budget import estimate_ace_step_memory


class ProfessionalFullSongService(LocalAudioProcessService):


    def generate(self, song_id: str, generation_profile: str | None = None) -> dict[str, object]:
        with exclusive_audio():
            return self._generate(song_id, generation_profile)

    def _generate(self, song_id: str, generation_profile: str | None = None) -> dict[str, object]:
        if not self.configured():
            raise ValueError("No hay provider full-song configurado.")

        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        FinalProductionGate(self.storage).require_for_project(project)

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
        self._assert_final_lyrics(lyrics_path)
        self._assert_required_dependencies()
        profile = resolve_ace_step_profile(generation_profile)

        plan_item = None
        process_arguments = None
        if "tools/acestep_generate.py" in self.command_template.replace("\\", "/"):
            plan_item, process_arguments = self._approved_execution(song_id, profile, project_dir, final_wav_path)
            prompt_path = project_dir / "ace_plan_caption.txt"
            lyrics_path = project_dir / "ace_plan_lyrics.md"
        else:
            prompt_path.write_text(self._build_prompt(project), encoding="utf-8")
        self._run_command(project, project_dir, prompt_path, lyrics_path, final_wav_path, log_path, diagnostics_path, profile,
                          process_arguments=process_arguments)
        after_audio = self.resource_monitor.capture(phase="after_audio", persist=True)
        self._assert_audio(final_wav_path)
        self._export_mp3(final_wav_path, final_mp3_path)
        self._export_flac(final_wav_path, final_flac_path)
        diagnostics = self._read_diagnostics(diagnostics_path)
        runtime = dict(diagnostics.get("runtime", {}))

        common_metadata = {
            "ace_plan_id": plan_item["plan_id"] if plan_item else "",
            "ace_plan_sha256": plan_item["plan"]["plan_sha256"] if plan_item else "",
            "spec_revision_id": plan_item["plan"]["spec_revision_id"] if plan_item else "",
            "generation_mode": "local_full_song_command",
            "quality_status": "final_candidate",
            "provider_name": "ACE-Step",
            "ace_step_profile": profile.name,
            "ace_step_model_type": profile.model_type,
            "ace_step_model_repo": profile.model_repo,
            "ace_step_infer_steps": profile.infer_steps,
            "ace_step_threads": profile.threads,
            "requested_device": runtime.get("requested_device", ""),
            "active_device": runtime.get("active_device", ""),
            "backend_active": runtime.get("backend_active", ""),
            "fallback_reason": runtime.get("fallback_reason", ""),
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
                "provider_name": "ACE-Step",
                "ace_step_profile": profile.name,
                "ace_step_model_type": profile.model_type,
                "ace_step_model_repo": profile.model_repo,
                "requested_device": runtime.get("requested_device", ""),
                "active_device": runtime.get("active_device", ""),
                "backend_active": runtime.get("backend_active", ""),
                "fallback_reason": runtime.get("fallback_reason", ""),
                "duration_seconds": diagnostics.get("duration_seconds", 0),
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
            "ace_step_profile": profile.name,
            "log": str(log_path),
        }


    def _approved_execution(self, song_id: str, profile: AceStepProfile, directory: Path, output: Path):
        review = ReviewAceStepPlan(PreviewAceStepPlan(self.storage, AceStepSourceAudio(self.storage.data_dir)),
                                  AceStepPlanRepository(self.storage.db_path))
        item = review.latest(song_id)
        if not item or item["effective_status"] != "approved":
            raise ValueError("Prepara y aprueba un plan ACE-Step vigente antes de generar la cancion.")
        if item["plan"]["payload"]["task_type"] != "text2music":
            raise ValueError("Esta ruta final crea desde la idea; las operaciones de edicion requieren su runner de candidatos.")
        lyrics_path = directory / "lyrics.md"
        if not lyrics_path.is_file() or lyrics_path.read_text(encoding="utf-8") != item["plan"]["payload"]["lyrics"]:
            raise ValueError("La letra del proyecto no coincide con el plan aprobado; sincroniza y revisa la letra.")
        argv = AceStepExecutionArguments().build(item, profile, self._python_executable(), directory, output)
        return item, argv





    def _build_prompt(self, project: dict[str, object]) -> str:
        spec = dict(dict(project.get("spec") or {}).get("json_spec", {}))
        music_plan_path = self.storage.data_dir / "projects" / str(project["id"]) / "music_plan.json"
        music_plan = self.storage.read_json(music_plan_path) if music_plan_path.exists() else {}
        voice_style = str(spec.get("voice_style", "")).strip()
        constraints = [
            "Use exactly the provided lyrics file; do not invent, translate, replace or omit lyrics.",
            "Keep one consistent lead singer identity for the full song.",
        ]
        lowered_voice = voice_style.lower()
        if "female" in lowered_voice:
            constraints.append("Lead vocal gender: female only; do not switch to male vocals.")
        elif "male" in lowered_voice:
            constraints.append("Lead vocal gender: male only; do not switch to female vocals.")
        return "\n".join(
            [
                f"Title: {spec.get('title', project.get('title', 'Song AI'))}",
                f"Song type: {spec.get('song_type', '')}",
                f"Language: {spec.get('language', '')}",
                f"Emotion: {spec.get('emotion', '')}",
                f"Voice style: {voice_style}",
                f"Duration seconds: {spec.get('duration_seconds', music_plan.get('duration_seconds', ''))}",
                f"BPM: {spec.get('bpm', music_plan.get('bpm', ''))}",
                f"Key: {spec.get('key', music_plan.get('key', ''))}",
                f"Instruments: {', '.join(str(item) for item in list(spec.get('instruments', [])))}",
                "Goal: complete finished song with coherent instrumental, sung vocals, melody, lyrics and final mix.",
                "Constraints: " + " ".join(constraints),
            ]
        )




    def _assert_required_dependencies(self) -> None:
        if "acestep_generate.py" not in self.command_template and "ace-step" not in self.command_template.lower():
            return
        torchcodec_ready = importlib.machinery.PathFinder.find_spec("torchcodec") is not None
        soundfile_ready = importlib.machinery.PathFinder.find_spec("soundfile") is not None
        if not torchcodec_ready and not soundfile_ready:
            raise ValueError(
                "Falta dependencia de audio I/O para ACE-Step: instala torchcodec o soundfile. "
                "En Intel XPU, ACE-Step usa soundfile porque torchcodec no esta disponible para XPU. "
                "Ejecuta scripts\\install-intel-xpu-prereqs.ps1 o scripts\\install-local-prereqs.ps1."
            )

    def _assert_final_lyrics(self, lyrics_path: Path) -> None:
        lyrics = lyrics_path.read_text(encoding="utf-8")
        if "# Letra mock" in lyrics or "Pendiente de completar" in lyrics:
            raise ValueError("La letra final todavia es mock o incompleta. Guarda la fase Lyrics antes de generar.")
        unresolved = sorted(set(re.findall(r"\{[^{}\n]+\}", lyrics)))
        if unresolved:
            raise ValueError(
                "La letra final contiene placeholders sin resolver: "
                + ", ".join(unresolved)
                + ". Completa esos campos antes de generar."
            )




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
