from __future__ import annotations

from pathlib import Path

from application.creative_agent_service import CreativeAgentService
from application.instrumental_generation_service import InstrumentalGenerationService
from application.lyrics_review_service import LyricsReviewService
from application.lyrics_service import LyricsService
from application.midi_generation_service import MidiGenerationService
from application.model_manager_service import ModelManagerService
from application.music_plan_service import MusicPlanService
from application.technical_director_service import TechnicalDirectorService
from application.vocal_synthesis_service import VocalSynthesisService
from application.voice_conversion_service import VoiceConversionService
from core.storage import StorageManager
from models.song_workflow import PHASE_LABELS, PHASE_SEQUENCE, SongPhase, SongPhaseStatus


class ProfessionalSongService:
    def __init__(
        self,
        storage: StorageManager,
        model_manager: ModelManagerService | None = None,
        soundtrack_command: str = "",
        singing_voice_command: str = "",
        voice_conversion_command: str = "",
        local_command_timeout_seconds: int = 3600,
    ) -> None:
        self.storage = storage
        self.creative_agent = CreativeAgentService()
        self.technical_director = TechnicalDirectorService(self.creative_agent)
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
        )
        self.voice_conversion_service = VoiceConversionService(
            storage,
            command_template=voice_conversion_command,
            timeout_seconds=local_command_timeout_seconds,
        )

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
        return {
            "project": project,
            "phases": self.phases(),
            "progress": self.progress_for(project),
        }

    def list_projects(self) -> dict[str, object]:
        projects = self.storage.list_song_projects()
        return {
            "projects": projects,
            "phases": self.phases(),
        }

    def get_project(self, song_id: str) -> dict[str, object]:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
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
        spec_record = project.get("spec")
        if not spec_record or not bool(dict(spec_record).get("approved_by_qwen")):
            raise ValueError("La especificacion debe estar aprobada por Qwen antes de generar letra.")
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
            message="Qwen esta revisando estructura, repeticion, duracion y compatibilidad musical de la letra.",
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
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        spec_record = project.get("spec")
        if not spec_record or not bool(dict(spec_record).get("approved_by_qwen")):
            raise ValueError("La especificacion debe estar aprobada antes de generar el plan musical.")
        lyrics_approved_path = self.storage.data_dir / "projects" / song_id / "lyrics_approved.json"
        if not lyrics_approved_path.exists():
            raise ValueError("La letra debe estar aprobada por Qwen antes de generar el plan musical.")
        lyrics_approved = self.storage.read_json(lyrics_approved_path)
        if not bool(lyrics_approved.get("approved_by_qwen")):
            raise ValueError("La letra aprobada no esta disponible; revisa la fase LYRICS_TECHNICAL_REVIEW.")

        self.model_manager.run_model("qwen", {"song_id": song_id, "phase": SongPhase.MUSIC_PLAN_GENERATION.value})
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.MUSIC_PLAN_GENERATION.value,
            status=SongPhaseStatus.RUNNING.value,
            progress=40,
            message="Qwen esta creando el plan musical tecnico para MIDI e instrumental.",
            active_model="qwen",
            payload={"lyrics_approved": str(lyrics_approved_path)},
        )
        result = self.music_plan_service.generate(
            song_id,
            dict(dict(spec_record).get("json_spec", {})),
            lyrics_approved,
        )
        self.model_manager.unload_model("qwen")
        result["progress"] = self.progress_for(result["project"])
        return result

    def get_music_plan(self, song_id: str) -> dict[str, object]:
        if self.storage.get_song_project(song_id) is None:
            raise ValueError("Proyecto profesional no encontrado.")
        return self.music_plan_service.get(song_id)

    def generate_midi(self, song_id: str) -> dict[str, object]:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        music_plan = self.music_plan_service.get(song_id)["music_plan"]
        self.model_manager.run_model("qwen", {"song_id": song_id, "phase": SongPhase.MIDI_GENERATION.value})
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.MIDI_GENERATION.value,
            status=SongPhaseStatus.RUNNING.value,
            progress=45,
            message="Qwen esta coordinando el MIDI base con acordes, melodia vocal guia y marcadores.",
            active_model="qwen",
            payload={"music_plan": str(self.storage.data_dir / "projects" / song_id / "music_plan.json")},
        )
        result = self.midi_generation_service.generate(song_id, dict(music_plan))
        self.model_manager.unload_model("qwen")
        result["progress"] = self.progress_for(result["project"])
        return result

    def get_midi(self, song_id: str) -> dict[str, object]:
        if self.storage.get_song_project(song_id) is None:
            raise ValueError("Proyecto profesional no encontrado.")
        return self.midi_generation_service.get(song_id)

    def generate_instrumental(self, song_id: str) -> dict[str, object]:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        music_plan = self.music_plan_service.get(song_id)["music_plan"]
        midi = self.midi_generation_service.get(song_id)
        active_model = "musicgen" if self.instrumental_generation_service.command_template else "local-procedural"
        self.model_manager.run_model(active_model, {"song_id": song_id, "phase": SongPhase.INSTRUMENTAL_GENERATION.value})
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.INSTRUMENTAL_GENERATION.value,
            status=SongPhaseStatus.RUNNING.value,
            progress=45,
            message="Generando instrumental desde music_plan.json y song_base.mid.",
            active_model=active_model,
            payload={
                "music_plan": str(self.storage.data_dir / "projects" / song_id / "music_plan.json"),
                "midi": str(midi["midi"]),
            },
        )
        result = self.instrumental_generation_service.generate(song_id, dict(music_plan), str(midi["midi"]))
        self.model_manager.unload_model(active_model)
        result["progress"] = self.progress_for(result["project"])
        return result

    def get_instrumental(self, song_id: str) -> dict[str, object]:
        if self.storage.get_song_project(song_id) is None:
            raise ValueError("Proyecto profesional no encontrado.")
        return self.instrumental_generation_service.get(song_id)

    def generate_vocals(self, song_id: str) -> dict[str, object]:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        spec_record = project.get("spec")
        if not spec_record:
            raise ValueError("La especificacion debe existir antes de generar voz.")
        lyrics_approved_path = self.storage.data_dir / "projects" / song_id / "lyrics_approved.json"
        if not lyrics_approved_path.exists():
            raise ValueError("La letra aprobada debe existir antes de generar voz.")
        lyrics_approved = self.storage.read_json(lyrics_approved_path)
        midi = self.midi_generation_service.get(song_id)
        self.instrumental_generation_service.get(song_id)
        active_model = "singing-voice-provider" if self.vocal_synthesis_service.command_template else "local-vocal-guide"
        self.model_manager.run_model(active_model, {"song_id": song_id, "phase": SongPhase.VOCAL_SYNTHESIS.value})
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.VOCAL_SYNTHESIS.value,
            status=SongPhaseStatus.RUNNING.value,
            progress=45,
            message="Generando voz cantada/guia desde lyrics_approved.json y melodia vocal MIDI.",
            active_model=active_model,
            payload={"lyrics_approved": str(lyrics_approved_path), "midi_metadata": str(self.storage.data_dir / "projects" / song_id / "midi_metadata.json")},
        )
        spec = dict(dict(spec_record).get("json_spec", {}))
        result = self.vocal_synthesis_service.generate(
            song_id,
            lyrics_approved,
            dict(midi["metadata"]),
            str(spec.get("voice_style", "soft vocal")),
        )
        self.model_manager.unload_model(active_model)
        result["progress"] = self.progress_for(result["project"])
        return result

    def get_vocals(self, song_id: str) -> dict[str, object]:
        if self.storage.get_song_project(song_id) is None:
            raise ValueError("Proyecto profesional no encontrado.")
        return self.vocal_synthesis_service.get(song_id)

    def convert_voice(self, song_id: str) -> dict[str, object]:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        spec_record = project.get("spec")
        if not spec_record:
            raise ValueError("La especificacion debe existir antes de convertir voz.")
        self.vocal_synthesis_service.get(song_id)
        spec = dict(dict(spec_record).get("json_spec", {}))
        active_model = "rvc-or-compatible" if self.voice_conversion_service.command_template else "none"
        self.model_manager.run_model(active_model, {"song_id": song_id, "phase": SongPhase.VOICE_CONVERSION.value})
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.VOICE_CONVERSION.value,
            status=SongPhaseStatus.RUNNING.value if self.voice_conversion_service.command_template else SongPhaseStatus.SKIPPED.value,
            progress=50,
            message="Evaluando conversion de voz opcional.",
            active_model=active_model,
            payload={"voice_style": str(spec.get("voice_style", ""))},
        )
        result = self.voice_conversion_service.run(song_id, str(spec.get("voice_style", "soft vocal")))
        self.model_manager.unload_model(active_model)
        result["progress"] = self.progress_for(result["project"])
        return result

    def get_converted_voice(self, song_id: str) -> dict[str, object]:
        if self.storage.get_song_project(song_id) is None:
            raise ValueError("Proyecto profesional no encontrado.")
        return self.voice_conversion_service.get(song_id)

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
        self.model_manager.unload_model("gemma")
        self.model_manager.run_model("qwen", {"song_id": song_id, "candidate_spec": candidate_spec})
        qwen_result = self.technical_director.validate_song_spec(candidate_spec)
        self.model_manager.unload_model("qwen")

        approved = bool(qwen_result["approved_by_qwen"])
        missing_fields = [str(item) for item in qwen_result["missing_fields"]]
        spec = self.storage.upsert_song_spec(
            song_id=song_id,
            json_spec=dict(qwen_result["song_spec"]),
            approved_by_qwen=approved,
            missing_fields=missing_fields,
        )
        artifact = self._write_song_spec_snapshot(song_id, dict(qwen_result["song_spec"]), approved, missing_fields)
        if approved:
            status = SongPhaseStatus.READY.value
            progress = 100
            project_status = SongPhaseStatus.READY.value
            current_phase = SongPhase.LYRICS_GENERATION.value
            message = "Qwen aprobo la especificacion. El proyecto puede avanzar a generacion de letra cantable."
        else:
            status = SongPhaseStatus.WAITING_USER_INPUT.value
            progress = 55
            project_status = SongPhaseStatus.WAITING_USER_INPUT.value
            current_phase = SongPhase.SONG_SPEC_COLLECTION.value
            message = "Qwen detecto informacion faltante. Gemma debe preguntarla al usuario en lenguaje natural."
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
            "progress": self.progress_for(project),
        }

    def progress_for(self, project: dict[str, object]) -> dict[str, object]:
        current_phase = str(project.get("current_phase", PHASE_SEQUENCE[0].value))
        total = len(PHASE_SEQUENCE)
        index_by_phase = {phase.value: index for index, phase in enumerate(PHASE_SEQUENCE, start=1)}
        current_number = index_by_phase.get(current_phase, 1)
        return {
            "current": current_number,
            "total": total,
            "label": PHASE_LABELS.get(PHASE_SEQUENCE[current_number - 1], "Fase desconocida"),
            "status": str(project.get("status", "pending")),
        }

    def _write_song_spec_snapshot(
        self,
        song_id: str,
        spec: dict[str, object],
        approved: bool,
        missing_fields: list[str],
    ) -> dict[str, object]:
        project_dir = self.storage.data_dir / "projects" / song_id
        path = project_dir / "song_spec.json"
        self.storage.write_json(
            path,
            {
                "song_id": song_id,
                "approved_by_qwen": approved,
                "missing_fields": missing_fields,
                "song_spec": spec,
            },
        )
        return self.storage.create_song_artifact(
            artifact_id=f"{song_id}_song_spec",
            song_id=song_id,
            phase=SongPhase.SONG_SPEC_COLLECTION.value,
            artifact_type="song_spec",
            file_path=str(Path(path)),
            metadata={"approved_by_qwen": approved, "missing_fields": missing_fields},
        )
