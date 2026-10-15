from __future__ import annotations

import re
from pathlib import Path

from application.set_music_spec_projection import SetMusicSpecProjection
from application.creative_agent_service import CreativeAgentService
from application.instrumental_generation_service import InstrumentalGenerationService
from application.lyrics_review_service import LyricsReviewService
from application.lyrics_service import LyricsService
from application.mastering_service import MasteringService
from application.midi_generation_service import MidiGenerationService
from application.mixing_service import MixingService
from application.model_manager_service import ModelManagerService
from application.model_orchestrator import ModelOrchestrator
from application.music_plan_service import MusicPlanService
from application.professional_export_service import ProfessionalExportService
from application.professional_full_song_service import ProfessionalFullSongService
from application.song_specification_service import SongSpecificationService
from application.technical_director_service import TechnicalDirectorService
from application.vocal_synthesis_service import VocalSynthesisService
from application.voice_conversion_service import VoiceConversionService
from config.resource_settings import ResourceMonitorSettings
from core.storage import StorageManager
from models.song_workflow import PHASE_LABELS, PHASE_SEQUENCE, SongPhase, SongPhaseStatus


class ProfessionalSongService(SetMusicSpecProjection):
    def __init__(
        self,
        storage: StorageManager,
        model_manager: ModelManagerService | None = None,
        soundtrack_command: str = "",
        full_song_command: str = "",
        singing_voice_command: str = "",
        voice_conversion_command: str = "",
        local_command_timeout_seconds: int = 3600,
        resource_settings: ResourceMonitorSettings | None = None,
        model_orchestrator: ModelOrchestrator | None = None,
    ) -> None:
        self.storage = storage
        self.creative_agent = CreativeAgentService()
        self.technical_director = TechnicalDirectorService(self.creative_agent)
        self.song_specifications = SongSpecificationService()
        self.model_orchestrator = model_orchestrator
        self.model_manager = model_manager or ModelManagerService()
        self.lyrics_service = LyricsService(storage)
        self.lyrics_review_service = LyricsReviewService(storage)
        self.music_plan_service = MusicPlanService(storage)
        self.midi_generation_service = MidiGenerationService(storage)
        self.instrumental_generation_service = InstrumentalGenerationService(
            storage,
            command_template=soundtrack_command,
            timeout_seconds=local_command_timeout_seconds,
        )
        self.vocal_synthesis_service = VocalSynthesisService(
            storage,
            command_template=singing_voice_command,
            timeout_seconds=local_command_timeout_seconds,
            resource_settings=resource_settings,
        )
        self.full_song_service = ProfessionalFullSongService(
            storage,
            command_template=full_song_command,
            timeout_seconds=local_command_timeout_seconds,
            resource_settings=resource_settings,
        )
        self.voice_conversion_service = VoiceConversionService(
            storage,
            command_template=voice_conversion_command,
            timeout_seconds=local_command_timeout_seconds,
        )
        self.mixing_service = MixingService(storage)
        self.mastering_service = MasteringService(storage)
        self.export_service = ProfessionalExportService(storage)

    def phases(self) -> list[dict[str, object]]:
        total = len(PHASE_SEQUENCE)
        return [
            {
                "number": index,
                "total": total,
                "phase": phase.value,
                "label": PHASE_LABELS[phase],
                "required": phase.value != "VOICE_CONVERSION",
            }
            for index, phase in enumerate(PHASE_SEQUENCE, start=1)
        ]

    def create_project(self, payload: dict[str, object]) -> dict[str, object]:
        title = str(payload.get("title") or payload.get("project_name") or "Nueva cancion")
        user_id = str(payload.get("user_id") or "local-user")
        project = self.storage.create_song_project(title=title, user_id=user_id)
        source_set_id = str(payload.get("source_set_id") or "").strip()
        if source_set_id:
            project = self._seed_project_from_set(str(project["id"]), source_set_id, payload)
        return {
            "project": project,
            "phases": self.phases(),
            "progress": self.progress_for(project),
        }

    def list_projects(self) -> dict[str, object]:
        projects = []
        for listed_project in self.storage.list_song_projects():
            full_project = self.storage.get_song_project(str(listed_project["id"])) or listed_project
            projects.append(self._ensure_project_seeded_from_link(full_project))
        return {
            "projects": projects,
            "phases": self.phases(),
        }

    def get_project(self, song_id: str) -> dict[str, object]:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        project = self._ensure_project_seeded_from_link(project)
        return {
            "project": project,
            "phases": self.phases(),
            "progress": self.progress_for(project),
        }

    def list_events(self, song_id: str) -> dict[str, object]:
        if self.storage.get_song_project(song_id) is None:
            raise ValueError("Proyecto profesional no encontrado.")
        return {
            "song_id": song_id,
            "events": self.storage.list_song_project_events(song_id),
        }

    def generate_lyrics(self, song_id: str) -> dict[str, object]:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        project = self._ensure_project_seeded_from_link(project)
        self._require_confirmed_spec(project)
        spec_record = project.get("spec")
        if not spec_record or not bool(dict(spec_record).get("approved_by_qwen")):
            raise ValueError("La especificacion debe estar aprobada por el director tecnico antes de generar letra.")
        self.model_manager.run_model("gemma", {"song_id": song_id, "phase": SongPhase.LYRICS_GENERATION.value})
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.LYRICS_GENERATION.value,
            status=SongPhaseStatus.RUNNING.value,
            progress=35,
            message="Gemma esta generando una letra cantable segun la especificacion aprobada.",
            active_model="gemma",
            payload={"source": "song_spec"},
        )
        result = self.lyrics_service.generate(song_id, dict(dict(spec_record).get("json_spec", {})))
        self.model_manager.unload_model("gemma")
        result["progress"] = self.progress_for(result["project"])
        return result

    def get_lyrics(self, song_id: str) -> dict[str, object]:
        if self.storage.get_song_project(song_id) is None:
            raise ValueError("Proyecto profesional no encontrado.")
        return self.lyrics_service.get(song_id)

    def update_lyrics(self, song_id: str, payload: dict[str, object]) -> dict[str, object]:
        if self.storage.get_song_project(song_id) is None:
            raise ValueError("Proyecto profesional no encontrado.")
        content = str(payload.get("content", ""))
        result = self.lyrics_service.update_markdown(song_id, content)
        result["progress"] = self.progress_for(result["project"])
        return result

    def review_lyrics(self, song_id: str) -> dict[str, object]:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        project = self._ensure_project_seeded_from_link(project)
        self._require_confirmed_spec(project)
        spec_record = project.get("spec")
        if not spec_record or not bool(dict(spec_record).get("approved_by_qwen")):
            raise ValueError("La especificacion debe estar aprobada antes de revisar la letra.")
        lyrics = self.lyrics_service.get(song_id)
        self.model_manager.run_model("qwen", {"song_id": song_id, "phase": SongPhase.LYRICS_TECHNICAL_REVIEW.value})
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.LYRICS_TECHNICAL_REVIEW.value,
            status=SongPhaseStatus.RUNNING.value,
            progress=35,
            message="El director tecnico esta revisando estructura, repeticion, duracion y compatibilidad musical de la letra.",
            active_model="qwen",
            payload={"lyrics_json_path": lyrics["lyrics_json_path"]},
        )
        result = self.lyrics_review_service.review(
            song_id,
            dict(dict(spec_record).get("json_spec", {})),
            dict(lyrics.get("lyrics", {})),
        )
        self.model_manager.unload_model("qwen")
        result["progress"] = self.progress_for(result["project"])
        return result

    def generate_music_plan(self, song_id: str) -> dict[str, object]:
        from application.local_planning_commands import GenerateLocalMusicPlan
        return GenerateLocalMusicPlan(_HistoricalProductionContext(self), self.music_plan_service).execute(song_id)

    def get_music_plan(self, song_id: str) -> dict[str, object]:
        if self.storage.get_song_project(song_id) is None:
            raise ValueError("Proyecto profesional no encontrado.")
        return self.music_plan_service.get(song_id)

    def generate_midi(self, song_id: str) -> dict[str, object]:
        from application.local_planning_commands import GenerateLocalMidi
        return GenerateLocalMidi(_HistoricalProductionContext(self), self.midi_generation_service).execute(song_id)

    def get_midi(self, song_id: str) -> dict[str, object]:
        if self.storage.get_song_project(song_id) is None:
            raise ValueError("Proyecto profesional no encontrado.")
        return self.midi_generation_service.get(song_id)

    def generate_instrumental(self, song_id: str) -> dict[str, object]:
        from application.local_stem_commands import GenerateLocalInstrumental
        return GenerateLocalInstrumental(_HistoricalProductionContext(self), self.instrumental_generation_service).execute(song_id)

    def get_instrumental(self, song_id: str) -> dict[str, object]:
        if self.storage.get_song_project(song_id) is None:
            raise ValueError("Proyecto profesional no encontrado.")
        return self.instrumental_generation_service.get(song_id)

    def generate_vocals(self, song_id: str) -> dict[str, object]:
        from application.local_stem_commands import GenerateLocalVocals
        return GenerateLocalVocals(_HistoricalProductionContext(self), self.vocal_synthesis_service).execute(song_id)

    def get_vocals(self, song_id: str) -> dict[str, object]:
        if self.storage.get_song_project(song_id) is None:
            raise ValueError("Proyecto profesional no encontrado.")
        return self.vocal_synthesis_service.get(song_id)

    def convert_voice(self, song_id: str) -> dict[str, object]:
        from application.local_stem_commands import ConvertLocalVoice
        return ConvertLocalVoice(_HistoricalProductionContext(self), self.voice_conversion_service).execute(song_id)

    def get_converted_voice(self, song_id: str) -> dict[str, object]:
        if self.storage.get_song_project(song_id) is None:
            raise ValueError("Proyecto profesional no encontrado.")
        return self.voice_conversion_service.get(song_id)

    def mix_song(self, song_id: str) -> dict[str, object]:
        from application.local_mix_command import MixLocalSong
        return MixLocalSong(_HistoricalProductionContext(self), self.mixing_service).execute(song_id)

    def get_mix(self, song_id: str) -> dict[str, object]:
        if self.storage.get_song_project(song_id) is None:
            raise ValueError("Proyecto profesional no encontrado.")
        return self.mixing_service.get(song_id)

    def master_song(self, song_id: str, generation_profile: str | None = None) -> dict[str, object]:
        from application.local_master_command import MasterLocalSong
        return MasterLocalSong(_HistoricalProductionContext(self), self.full_song_service, self.mixing_service, self.mastering_service).execute(song_id, generation_profile=generation_profile)

    def get_master(self, song_id: str) -> dict[str, object]:
        if self.storage.get_song_project(song_id) is None:
            raise ValueError("Proyecto profesional no encontrado.")
        return self.mastering_service.get(song_id)

    def export_song(self, song_id: str) -> dict[str, object]:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        project = self._ensure_project_seeded_from_link(project)
        self._require_confirmed_spec(project)
        self._require_approved_linked_sample(project)
        self.mastering_service.get(song_id)
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.EXPORT.value,
            status=SongPhaseStatus.RUNNING.value,
            progress=45,
            message="Preparando manifest de export y enlaces de descarga.",
            active_model="export-service",
            payload={},
        )
        return self.export_service.export(song_id)

    def get_export(self, song_id: str) -> dict[str, object]:
        if self.storage.get_song_project(song_id) is None:
            raise ValueError("Proyecto profesional no encontrado.")
        return self.export_service.get(song_id)

    def artifact_download_file(self, song_id: str, artifact_type: str) -> tuple[Path, str, str]:
        return self.export_service.download_file(song_id, artifact_type)

    def list_artifacts(self, song_id: str) -> dict[str, object]:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        verified = [
            self.storage.verify_song_artifact(song_id, str(artifact.get("type", "")))
            for artifact in list(project.get("artifacts", []))
        ]
        return {"song_id": song_id, "artifacts": verified}

    def verify_artifact(self, song_id: str, artifact_type: str) -> dict[str, object]:
        return self.storage.verify_song_artifact(song_id, artifact_type)

    def regenerate_artifact(self, song_id: str, artifact_type: str) -> dict[str, object]:
        from application.artifact_regeneration import ArtifactRegeneration
        return ArtifactRegeneration({
            'lyrics':self.generate_lyrics, 'lyrics_review':self.review_lyrics,
            'music_plan':self.generate_music_plan, 'midi':self.generate_midi,
            'instrumental':self.generate_instrumental, 'vocals':self.generate_vocals,
            'voice_conversion':self.convert_voice, 'mix':self.mix_song,
            'master':self.master_song, 'export':self.export_song,
        }).execute(song_id, artifact_type)

    def collect_spec(self, song_id: str, payload: dict[str, object]) -> dict[str, object]:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        user_message = str(payload.get("message", "")).strip()
        if not user_message:
            raise ValueError("El mensaje para Gemma no puede estar vacio.")

        existing_spec = None
        if project.get("spec"):
            existing_spec = dict(dict(project["spec"]).get("json_spec", {}))
        self.model_manager.run_model("gemma", {"song_id": song_id, "message": user_message})
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.SONG_SPEC_COLLECTION.value,
            status=SongPhaseStatus.RUNNING.value,
            progress=20,
            message="Gemma recibio la intencion creativa del usuario y la tradujo a especificacion inicial.",
            active_model="gemma",
            payload={"user_message": user_message},
        )

        candidate_spec = self.creative_agent.build_initial_spec(user_message, existing_spec)
        candidate_spec = self.song_specifications.add_provenance(existing_spec, candidate_spec, user_message)
        self.model_manager.unload_model("gemma")
        self.model_manager.run_model("qwen", {"song_id": song_id, "candidate_spec": candidate_spec})
        qwen_result = self.technical_director.validate_song_spec(candidate_spec)
        self.model_manager.unload_model("qwen")

        handoff: dict[str, object] | None = None
        if self.model_orchestrator is not None:
            handoff = self.model_orchestrator.run_handoff(
                {
                    "model_role": "technical",
                    "task_type": "review_song_spec",
                    "project_id": song_id,
                    "project_name": str(project.get("title", song_id)),
                    "phase": SongPhase.SONG_SPEC_COLLECTION.value,
                    "question": "Revisa coherencia, viabilidad y faltantes de esta especificacion de cancion.",
                    "context": {
                        "candidate_spec": qwen_result["song_spec"],
                        "deterministic_validation": {
                            "status": qwen_result["status"],
                            "missing_fields": qwen_result["missing_fields"],
                        },
                    },
                }
            )
        handoff_result = dict(handoff.get("result", {})) if handoff else {}
        model_review_executed = bool(handoff_result.get("provider_executed", False))
        technical_review_mode = "provider_review" if model_review_executed else str(handoff_result.get("mode", "rule_validation"))
        qwen_result.update(
            {
                "technical_review_mode": technical_review_mode,
                "model_review_executed": model_review_executed,
                "handoff_task_id": str(dict(handoff.get("task", {})).get("task_id", "")) if handoff else "",
                "handoff_run_id": str(dict(handoff.get("model_run", {})).get("run_id", "")) if handoff else "",
                "model_review_summary": str(handoff_result.get("summary", "")),
            }
        )

        approved = bool(qwen_result["approved_by_qwen"])
        missing_fields = [str(item) for item in qwen_result["missing_fields"]]
        spec = self.storage.upsert_song_spec(
            song_id=song_id,
            json_spec=dict(qwen_result["song_spec"]),
            approved_by_qwen=approved,
            missing_fields=missing_fields,
            technical_review_mode=technical_review_mode,
            user_confirmation_status="pending" if approved else "not_ready",
        )
        artifact = self._write_song_spec_snapshot(song_id, dict(qwen_result["song_spec"]), approved, missing_fields)
        if approved:
            status = SongPhaseStatus.WAITING_USER_INPUT.value
            progress = 90
            project_status = SongPhaseStatus.WAITING_USER_INPUT.value
            current_phase = SongPhase.SONG_SPEC_COLLECTION.value
            message = "La ficha esta completa y validada. El usuario debe confirmarla antes de generar la letra."
        else:
            status = SongPhaseStatus.WAITING_USER_INPUT.value
            progress = 55
            project_status = SongPhaseStatus.WAITING_USER_INPUT.value
            current_phase = SongPhase.SONG_SPEC_COLLECTION.value
            message = "El director tecnico detecto informacion faltante. Gemma debe preguntarla al usuario en lenguaje natural."
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.SONG_SPEC_COLLECTION.value,
            status=status,
            progress=progress,
            message=message,
            active_model="qwen",
            payload=qwen_result,
            artifact_id=str(artifact["artifact_id"]),
        )
        project = self.storage.update_song_project_phase(song_id, current_phase, project_status)
        gemma_message = self.creative_agent.compose_user_response(qwen_result)
        return {
            "project": project,
            "spec": spec,
            "qwen": qwen_result,
            "gemma": {
                "message": gemma_message,
                "questions_for_user": qwen_result["questions_for_user"],
            },
            "artifact": artifact,
            "catalog": self.song_specifications.catalog(dict(qwen_result["song_spec"])),
            "handoff": handoff,
            "progress": self.progress_for(project),
        }

    def confirm_song_specification(self, song_id: str, payload: dict[str, object]) -> dict[str, object]:
        from application.music_spec_revision_service import MusicSpecRevisionService
        return MusicSpecRevisionService(self.storage).confirm_song_specification(song_id, payload)

    def get_song_specification(self, song_id: str) -> dict[str, object]:
        from application.music_spec_revision_service import MusicSpecRevisionService
        return MusicSpecRevisionService(self.storage).get_song_specification(song_id)

    def _require_confirmed_spec(self, project: dict[str, object]) -> dict[str, object]:
        from application.music_spec_revision_service import require_confirmed_music_spec
        return require_confirmed_music_spec(project)

    def _require_approved_linked_sample(self, project: dict[str, object]) -> dict[str, object] | None:
        from application.sample_gate import SampleGate
        return SampleGate(self.storage).require_for_project(project)

    def progress_for(self, project: dict[str, object]) -> dict[str, object]:
        from application.music_spec_revision_service import MusicSpecRevisionService
        return MusicSpecRevisionService(self.storage).progress_for(project)

    def _write_song_spec_snapshot(
        self,
        song_id: str,
        spec: dict[str, object],
        approved: bool,
        missing_fields: list[str],
    ) -> dict[str, object]:
        project_dir = self.storage.data_dir / "projects" / song_id
        path = project_dir / "song_spec.json"
        markdown_path = project_dir / "song_spec.md"
        self.storage.write_json(
            path,
            {
                "song_id": song_id,
                "approved_by_qwen": approved,
                "missing_fields": missing_fields,
                "song_spec": spec,
            },
        )
        catalog = self.song_specifications.catalog(spec)
        markdown_lines = [
            f"# Especificacion de cancion: {spec.get('title', song_id)}",
            "",
            f"Estado: {'completa para esta etapa' if approved else 'requiere informacion'}",
            "",
        ]
        for group in catalog["groups"]:
            markdown_lines.extend([f"## {group['label']}", ""])
            for field in group["fields"]:
                value = field.get("value")
                rendered = ", ".join(str(item) for item in value) if isinstance(value, list) else str(value or "Por decidir")
                markdown_lines.append(f"- **{field['label']}:** {rendered}")
            markdown_lines.append("")
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text("\n".join(markdown_lines), encoding="utf-8")
        return self.storage.create_song_artifact(
            artifact_id=f"{song_id}_song_spec",
            song_id=song_id,
            phase=SongPhase.SONG_SPEC_COLLECTION.value,
            artifact_type="song_spec",
            file_path=str(Path(path)),
            metadata={
                "approved_by_qwen": approved,
                "missing_fields": missing_fields,
                "validation_basis": "deterministic_rules",
                "model_review_executed": False,
                "markdown_path": str(markdown_path),
            },
        )

    def _seed_project_from_set(
        self,
        song_id: str,
        source_set_id: str,
        payload: dict[str, object],
    ) -> dict[str, object]:
        song_set = self.storage.get_indexed_set(source_set_id)
        if song_set is None:
            raise ValueError("Set/proyecto activo no encontrado para preparar Production.")

        phase_data = self.storage.list_project_phase_data(source_set_id)
        assets = self._assets_for_set(song_set)
        spec = self._spec_from_set_data(song_set, phase_data, assets, payload)
        spec_record = self.storage.upsert_song_spec(
            song_id=song_id,
            json_spec=spec,
            approved_by_qwen=True,
            missing_fields=[],
            technical_review_mode="sqlite_import",
            user_confirmation_status="confirmed",
        )
        spec_artifact = self._write_song_spec_snapshot(song_id, spec, True, [])

        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.SONG_SPEC_COLLECTION.value,
            status=SongPhaseStatus.COMPLETED.value,
            progress=100,
            message="Production preparo la especificacion desde las fases guardadas del proyecto activo.",
            active_model="sqlite-project-bridge",
            payload={
                "source_set_id": source_set_id,
                "song_spec_id": str(spec_record.get("id", "")),
                "source": "active_set_phase_data",
            },
            artifact_id=str(spec_artifact["artifact_id"]),
        )

        lyrics_markdown = self._lyrics_markdown_from_set(song_set, phase_data, assets)
        lyrics_payload = self.lyrics_service.from_markdown(
            song_id=song_id,
            title=str(spec.get("title", song_set.get("project_name", "Letra"))),
            markdown=lyrics_markdown,
        )
        lyrics_result = self.lyrics_service.write(
            song_id,
            lyrics_payload,
            lyrics_markdown,
            "Letra preparada desde la fase Lyrics del proyecto activo.",
        )
        approved_artifact = self._write_approved_lyrics_snapshot(song_id, lyrics_payload, source_set_id)
        self._write_music_plan_from_set(song_id, phase_data, spec, source_set_id)

        target_phase = self._target_phase_from_editor_data(song_id)
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.LYRICS_TECHNICAL_REVIEW.value,
            status=SongPhaseStatus.COMPLETED.value,
            progress=100,
            message="La letra del proyecto activo quedo disponible como lyrics_approved.json para Production.",
            active_model="sqlite-project-bridge",
            payload={
                "source_set_id": source_set_id,
                "lyrics_markdown_artifacts": [
                    str(item.get("artifact_id", "")) for item in list(lyrics_result.get("artifacts", []))
                ],
            },
            artifact_id=str(approved_artifact["artifact_id"]),
        )
        return self.storage.update_song_project_phase(song_id, target_phase.value, SongPhaseStatus.READY.value)

    def _ensure_project_seeded_from_link(
        self,
        project: dict[str, object],
        *,
        force_refresh: bool = False,
    ) -> dict[str, object]:
        user_id = str(project.get("user_id", ""))
        if not user_id.startswith("set:"):
            return project
        song_id = str(project["id"])
        if "spec" not in project:
            project = self.storage.get_song_project(song_id) or project
        music_plan_path = self.storage.data_dir / "projects" / song_id / "music_plan.json"
        spec = project.get("spec")
        source_set_id = user_id.split(":", 1)[1].strip()
        if force_refresh and source_set_id:
            return self._seed_project_from_set(
                song_id,
                source_set_id,
                {"title": str(project.get("title") or "Cancion")},
            )
        if spec and (spec.get('json_spec', {}).get('_editor_phases') or spec.get('json_spec', {}).get('_consolidation')):
            return project
        if spec and bool(dict(spec).get("approved_by_qwen")):
            if source_set_id and not music_plan_path.exists():
                phase_data = self.storage.list_project_phase_data(source_set_id)
                if self._phase_payload(phase_data, "music-plan").get("musicPlan"):
                    spec_data = dict(dict(spec).get("json_spec", {}))
                    self._write_music_plan_from_set(song_id, phase_data, spec_data, source_set_id)
                    return self.storage.update_song_project_phase(
                        song_id,
                        SongPhase.MIDI_GENERATION.value,
                        SongPhaseStatus.READY.value,
                    )
            return project
        if not source_set_id:
            return project
        return self._seed_project_from_set(
            song_id,
            source_set_id,
            {"title": str(project.get("title") or "Cancion")},
        )










    def _refresh_linked_project_for_mastering(self, project: dict[str, object]) -> dict[str, object]:
        refreshed = self._ensure_project_seeded_from_link(project, force_refresh=True)
        song_id = str(refreshed["id"])
        lyrics_path = self.storage.data_dir / "projects" / song_id / "lyrics.md"
        if lyrics_path.exists():
            lyrics_text = lyrics_path.read_text(encoding="utf-8")
            if "# Letra mock" in lyrics_text or "Pendiente de completar" in lyrics_text:
                raise ValueError("La letra final todavia apunta a un mock. Guarda la fase Lyrics antes de generar.")
            unresolved = sorted(set(re.findall(r"\{[^{}\n]+\}", lyrics_text)))
            if unresolved:
                raise ValueError(
                    "La letra final contiene placeholders sin resolver: "
                    + ", ".join(unresolved)
                    + ". Completa esos campos antes de generar."
                )
        return refreshed

    def _write_approved_lyrics_snapshot(
        self,
        song_id: str,
        lyrics_payload: dict[str, object],
        source_set_id: str,
    ) -> dict[str, object]:
        path = self.storage.data_dir / "projects" / song_id / "lyrics_approved.json"
        self.storage.write_json(
            path,
            {
                "song_id": song_id,
                "approved_by_qwen": True,
                "status": "approved",
                "issues": [],
                "recommendations_for_gemma": [],
                "metrics": {"source": "active_set_phase_data"},
                "lyrics": lyrics_payload,
                "source_set_id": source_set_id,
            },
        )
        return self.storage.create_song_artifact(
            artifact_id=f"{song_id}_lyrics_approved",
            song_id=song_id,
            phase=SongPhase.LYRICS_TECHNICAL_REVIEW.value,
            artifact_type="lyrics_approved_json",
            file_path=str(Path(path)),
            metadata={"approved_by_qwen": True, "source_set_id": source_set_id},
        )

    def _write_music_plan_from_set(
        self,
        song_id: str,
        phase_data: dict[str, object],
        spec: dict[str, object],
        source_set_id: str,
    ) -> dict[str, object] | None:
        path = self.storage.data_dir / "projects" / song_id / "music_plan.json"
        if path.exists():
            return self.storage.read_json(path)
        editor_plan = self._phase_payload(phase_data, "music-plan").get("musicPlan")
        if not isinstance(editor_plan, dict) or not editor_plan:
            return None
        sections = [dict(item) for item in list(editor_plan.get("sections", []))]
        duration = sum(int(self._first_number(item.get("seconds"), item.get("duration"), 0)) for item in sections)
        duration = duration or int(spec.get("duration_seconds", 120))
        timeline: list[dict[str, object]] = []
        cursor = 0
        for item in sections:
            section_duration = int(self._first_number(item.get("seconds"), item.get("duration"), 0)) or 8
            section_name = self._section_id(str(item.get("name") or item.get("section") or "section"))
            timeline.append(
                {
                    "section": section_name,
                    "start_seconds": cursor,
                    "end_seconds": cursor + section_duration,
                    "duration_seconds": section_duration,
                }
            )
            cursor += section_duration
        if not timeline:
            timeline = self.music_plan_service._timeline([str(item) for item in list(spec.get("structure", []))], duration)
        plan = {
            "song_id": song_id,
            "title": str(spec.get("title", "Nueva cancion")),
            "bpm": int(self._first_number(editor_plan.get("bpm"), spec.get("bpm"), 80)),
            "key": self._first_text(editor_plan.get("key"), spec.get("key"), "C major"),
            "time_signature": self._first_text(editor_plan.get("timeSignature"), editor_plan.get("time_signature"), "4/4"),
            "chord_progression": [
                item.strip()
                for item in self._first_text(editor_plan.get("progression"), "I - V - vi - IV").replace("-", ",").split(",")
                if item.strip()
            ],
            "duration_seconds": duration,
            "structure_timeline": timeline,
            "section_intensity": {
                str(item["section"]): str(sections[index].get("intensity", "medium"))
                for index, item in enumerate(timeline)
                if index < len(sections)
            },
            "instrumentation_prompt": self._first_text(
                editor_plan.get("instrumentationNotes"),
                ", ".join(str(item) for item in list(spec.get("instruments", []))),
            ),
            "midi_requirements": {
                "must_include_vocal_melody": True,
                "must_include_chords": True,
                "must_include_section_markers": True,
                "tempo_bpm": int(self._first_number(editor_plan.get("bpm"), spec.get("bpm"), 80)),
                "key": self._first_text(editor_plan.get("key"), spec.get("key"), "C major"),
            },
            "source_set_id": source_set_id,
            "source_of_truth": "sqlite_music_plan_phase",
        }
        self.storage.write_json(path, plan)
        artifact = self.storage.create_song_artifact(
            artifact_id=f"{song_id}_music_plan",
            song_id=song_id,
            phase=SongPhase.MUSIC_PLAN_GENERATION.value,
            artifact_type="music_plan_json",
            file_path=str(Path(path)),
            metadata={
                "bpm": plan["bpm"],
                "key": plan["key"],
                "duration_seconds": duration,
                "source_set_id": source_set_id,
            },
        )
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.MUSIC_PLAN_GENERATION.value,
            status=SongPhaseStatus.COMPLETED.value,
            progress=100,
            message="Production preparo music_plan.json desde la fase Music Plan del proyecto activo.",
            active_model="sqlite-project-bridge",
            payload={"source_set_id": source_set_id, "music_plan": str(path)},
            artifact_id=str(artifact["artifact_id"]),
        )
        return plan

    def _target_phase_from_editor_data(self, song_id: str) -> SongPhase:
        if (self.storage.data_dir / "projects" / song_id / "music_plan.json").exists():
            return SongPhase.MIDI_GENERATION
        return SongPhase.MUSIC_PLAN_GENERATION


from application.local_production_context import LocalProductionContext


class _HistoricalProductionContext(LocalProductionContext):
    """Keep old preparation side effects behind explicit compatibility access."""
    def __init__(self, service):
        super().__init__(service.storage)
        self.service = service

    def require_project(self, project):
        project = self.service._ensure_project_seeded_from_link(project)
        return super().require_project(project)

    def prepare_final_project(self, project):
        project = self.service._refresh_linked_project_for_mastering(project)
        self.service._require_confirmed_spec(project)
        return project
