from pathlib import Path
import re
import os
import shutil
from typing import Any

from audio.mixer import AudioMixer
from audio.local_song_pipeline import LocalSongPipeline
from audio.resource_monitor import ResourceMonitor
from application.model_orchestrator import ModelOrchestrator
from application.model_manager_service import ModelManagerService
from application.professional_song_service import ProfessionalSongService
from builders.export_builder import ExportBuilder
from builders.full_song_builder import FullSongBuilder
from builders.sample_builder import SampleBuilder
from builders.set_builder import SetBuilder
from builders.template_builder import TemplateBuilder
from core import creative_options as options
from core.storage import StorageManager
from explorers.mock_explorers import MockExplorerSuite
from models.song_workflow import PHASE_LABELS, PHASE_SEQUENCE, SongPhaseStatus
from providers.registry import ProviderRegistry
from config.settings import Settings


class SongService:
    DEFAULT_LULLABY_PROJECT = {
        "project_name": "Cancion de cuna para Isabella",
        "description": "Cancion de cuna completa, tierna y poetica con soundtrack suave y voz cantada.",
    }
    DEFAULT_LULLABY_INSTRUMENTAL = {
        "genre": "lullaby",
        "mood": "tender",
        "bpm": 72,
        "key": "C major",
        "instruments": ["piano", "music box", "soft pad", "strings"],
        "energy": "low",
    }
    DEFAULT_LULLABY_MELODY = {
        "vocal_style": "soft lullaby singing",
        "range_hint": "medium",
        "structure": "intro, verse 1, chorus, verse 2, final chorus, outro",
        "mood": "tender",
        "energy": "low",
    }
    DEFAULT_LULLABY_LYRICS = {
        "language": "Spanish",
        "tone": "tender",
        "theme": "lullaby for {name}",
        "structure": "intro, verse 1, chorus, verse 2, bridge, final chorus, outro",
        "placeholders": {"name": "Isabella", "image": "estrellita", "promise": "siempre cuidarte"},
    }

    def __init__(self, storage: StorageManager, settings: Settings | None = None) -> None:
        self.settings = settings
        self.storage = storage
        self.explorers = MockExplorerSuite(storage)
        self.set_builder = SetBuilder(storage)
        self.sample_builder = SampleBuilder(storage)
        self.full_song_builder = FullSongBuilder(storage)
        self.audio_mixer = AudioMixer(storage)
        self.export_builder = ExportBuilder(storage)
        self.resource_monitor = ResourceMonitor(storage, settings.resource_monitor) if settings else None
        self.local_song_pipeline = LocalSongPipeline(settings.local_models, self.resource_monitor) if settings else None
        self.template_builder = TemplateBuilder(storage)
        self.provider_registry = ProviderRegistry(
            settings.hf_models if settings else None,
            settings.local_models if settings else None,
        )
        self.model_orchestrator = ModelOrchestrator(storage, self.provider_registry)
        max_loaded_models = settings.local_models.max_loaded_models if settings else 1
        self.model_manager = ModelManagerService(max_loaded_models=max_loaded_models)
        self.professional_songs = ProfessionalSongService(
            storage,
            self.model_manager,
            soundtrack_command=settings.local_models.soundtrack_command if settings else "",
            full_song_command=settings.local_models.full_song_command if settings else "",
            singing_voice_command=settings.local_models.singing_voice_command if settings else "",
            voice_conversion_command=settings.local_models.voice_conversion_command if settings else "",
            local_command_timeout_seconds=settings.local_models.local_command_timeout_seconds if settings else 3600,
            resource_settings=settings.resource_monitor if settings else None,
        )

    def bootstrap(self) -> None:
        self.storage.ensure_project_layout()
        self._mark_interrupted_professional_runs()

    def _mark_interrupted_professional_runs(self) -> None:
        for project in self.storage.list_song_projects():
            status = str(project.get("status", "")).lower()
            if status not in {SongPhaseStatus.RUNNING.value, SongPhaseStatus.LOADING_MODEL.value}:
                continue
            song_id = str(project.get("id", ""))
            phase = str(project.get("current_phase") or "MASTERING")
            if not song_id:
                continue
            self.storage.create_song_event(
                song_id=song_id,
                phase=phase,
                status=SongPhaseStatus.FAILED.value,
                progress=100,
                message=(
                    "La tarea quedo interrumpida porque el servidor se reinicio o el proceso local "
                    "termino sin cerrar la fase. Vuelve a ejecutar esta fase para continuar."
                ),
                active_model="startup-recovery",
                payload={"previous_status": status},
            )
            self.storage.update_song_project_phase(song_id, phase, SongPhaseStatus.FAILED.value)

    def options(self) -> dict[str, object]:
        return {
            "genres": options.GENRES,
            "moods": options.MOODS,
            "energies": options.ENERGIES,
            "bpm_presets": options.BPM_PRESETS,
            "keys": options.KEYS,
            "instrument_families": options.INSTRUMENT_FAMILIES,
            "vocal_styles": options.VOCAL_STYLES,
            "vocal_ranges": options.VOCAL_RANGES,
            "song_structures": options.SONG_STRUCTURES,
            "languages": options.LANGUAGES,
            "lyric_themes": options.LYRIC_THEMES,
            "placeholder_presets": options.PLACEHOLDER_PRESETS,
            "help_texts": options.HELP_TEXTS,
        }

    def professional_phases(self) -> list[dict[str, object]]:
        return self.professional_songs.phases()

    def resource_status(self) -> dict[str, object]:
        if self.resource_monitor is None:
            return {"enabled": False, "reason": "Settings no cargados."}
        return self.resource_monitor.status()

    def resource_history(self, limit: int = 100) -> dict[str, object]:
        if self.resource_monitor is None:
            return {"snapshots": []}
        return self.resource_monitor.history(limit)

    def check_audio_readiness(self) -> dict[str, object]:
        if self.resource_monitor is None:
            return {"ready": False, "message": "Settings no cargados."}
        return self.resource_monitor.check_audio_readiness()

    def create_professional_project(self, payload: dict[str, object]) -> dict[str, object]:
        return self.professional_songs.create_project(payload)

    def list_professional_projects(self) -> dict[str, object]:
        return self.professional_songs.list_projects()

    def get_professional_project(self, song_id: str) -> dict[str, object]:
        return self.professional_songs.get_project(song_id)

    def list_professional_project_events(self, song_id: str) -> dict[str, object]:
        return self.professional_songs.list_events(song_id)

    def collect_professional_spec(self, song_id: str, payload: dict[str, object]) -> dict[str, object]:
        return self.professional_songs.collect_spec(song_id, payload)

    def generate_professional_lyrics(self, song_id: str) -> dict[str, object]:
        return self.professional_songs.generate_lyrics(song_id)

    def get_professional_lyrics(self, song_id: str) -> dict[str, object]:
        return self.professional_songs.get_lyrics(song_id)

    def update_professional_lyrics(self, song_id: str, payload: dict[str, object]) -> dict[str, object]:
        return self.professional_songs.update_lyrics(song_id, payload)

    def review_professional_lyrics(self, song_id: str) -> dict[str, object]:
        return self.professional_songs.review_lyrics(song_id)

    def generate_professional_music_plan(self, song_id: str) -> dict[str, object]:
        return self.professional_songs.generate_music_plan(song_id)

    def get_professional_music_plan(self, song_id: str) -> dict[str, object]:
        return self.professional_songs.get_music_plan(song_id)

    def generate_professional_midi(self, song_id: str) -> dict[str, object]:
        return self.professional_songs.generate_midi(song_id)

    def get_professional_midi(self, song_id: str) -> dict[str, object]:
        return self.professional_songs.get_midi(song_id)

    def generate_professional_instrumental(self, song_id: str) -> dict[str, object]:
        return self.professional_songs.generate_instrumental(song_id)

    def get_professional_instrumental(self, song_id: str) -> dict[str, object]:
        return self.professional_songs.get_instrumental(song_id)

    def generate_professional_vocals(self, song_id: str) -> dict[str, object]:
        return self.professional_songs.generate_vocals(song_id)

    def get_professional_vocals(self, song_id: str) -> dict[str, object]:
        return self.professional_songs.get_vocals(song_id)

    def convert_professional_voice(self, song_id: str) -> dict[str, object]:
        return self.professional_songs.convert_voice(song_id)

    def get_professional_converted_voice(self, song_id: str) -> dict[str, object]:
        return self.professional_songs.get_converted_voice(song_id)

    def mix_professional_song(self, song_id: str) -> dict[str, object]:
        return self.professional_songs.mix_song(song_id)

    def get_professional_mix(self, song_id: str) -> dict[str, object]:
        return self.professional_songs.get_mix(song_id)

    def master_professional_song(self, song_id: str) -> dict[str, object]:
        return self.professional_songs.master_song(song_id)

    def get_professional_master(self, song_id: str) -> dict[str, object]:
        return self.professional_songs.get_master(song_id)

    def export_professional_song(self, song_id: str) -> dict[str, object]:
        return self.professional_songs.export_song(song_id)

    def get_professional_export(self, song_id: str) -> dict[str, object]:
        return self.professional_songs.get_export(song_id)

    def professional_artifact_download_file(self, song_id: str, artifact_type: str) -> tuple[Path, str, str]:
        return self.professional_songs.artifact_download_file(song_id, artifact_type)

    def list_professional_artifacts(self, song_id: str) -> dict[str, object]:
        return self.professional_songs.list_artifacts(song_id)

    def verify_professional_artifact(self, song_id: str, artifact_type: str) -> dict[str, object]:
        return self.professional_songs.verify_artifact(song_id, artifact_type)

    def regenerate_professional_artifact(self, song_id: str, artifact_type: str) -> dict[str, object]:
        return self.professional_songs.regenerate_artifact(song_id, artifact_type)

    def create_instrumental(self, payload: dict[str, object]) -> dict[str, str]:
        path = self.explorers.instrumentals.create_from_intent(
            mood=str(payload.get("mood", "warm")),
            genre=str(payload.get("genre", "pop ballad")),
            bpm=int(payload.get("bpm", 96)),
            key=str(payload.get("key", "C major")),
            instruments=[str(item) for item in payload.get("instruments", ["piano", "soft drums", "bass"])],
            energy=str(payload.get("energy", "medium")),
            mode="web_guided",
        )
        return self.path_response(path)

    def create_melody(self, payload: dict[str, object]) -> dict[str, str]:
        path = self.explorers.melodies.create_from_intent(
            mood=str(payload.get("mood", "hopeful")),
            vocal_style=str(payload.get("vocal_style", "clear emotional delivery")),
            range_hint=str(payload.get("range_hint", "medium")),
            structure=str(payload.get("structure", "verse, chorus")),
            energy=str(payload.get("energy", "medium")),
            mode="web_guided",
        )
        return self.path_response(path)

    def create_lyrics(self, payload: dict[str, object]) -> dict[str, str]:
        placeholders = payload.get("placeholders", {"name": "Nombre", "occasion": "Ocasion"})
        path = self.explorers.lyrics.create_from_intent(
            theme=str(payload.get("theme", "song for {name} about {occasion}")),
            language=str(payload.get("language", "Spanish")),
            tone=str(payload.get("tone", "grateful")),
            structure=str(payload.get("structure", "verse, chorus")),
            placeholders={str(key): str(value) for key, value in dict(placeholders).items()},
            mode="web_guided",
        )
        return self.path_response(path)

    def get_lyrics(self, asset_id: str) -> dict[str, str]:
        return self.storage.get_lyrics_markdown(asset_id)

    def update_lyrics(self, asset_id: str, payload: dict[str, object]) -> dict[str, str]:
        content = str(payload.get("content", ""))
        return self.storage.update_lyrics_markdown(asset_id, content)

    def list_drafts(self) -> list[dict[str, str]]:
        return self.storage.list_asset_drafts()

    def list_favorites(self) -> list[dict[str, str]]:
        return self.storage.list_favorites()

    def favorite_asset(self, payload: dict[str, object]) -> dict[str, object]:
        asset_id = str(payload.get("asset_id", ""))
        favorite = self.storage.favorite_asset(asset_id)
        return {"ok": favorite is not None, "favorite": favorite}

    def create_set(self, payload: dict[str, object] | None = None) -> dict[str, str]:
        payload = payload or {}
        project_name = str(payload.get("project_name", "")).strip() or "Proyecto automatico"
        description = str(payload.get("description", "")).strip()
        if not description:
            description = "Cancion completa creada con los primeros drafts disponibles."
        return self.path_response(
            self.set_builder.create_first_valid_set(
                project_name=project_name,
                description=description,
            )
        )

    def create_default_lullaby_mp3(self) -> dict[str, Any]:
        instrumental_path = self.create_instrumental(self.DEFAULT_LULLABY_INSTRUMENTAL)
        melody_path = self.create_melody(self.DEFAULT_LULLABY_MELODY)
        lyrics_path = self.create_lyrics(self.DEFAULT_LULLABY_LYRICS)

        set_path = self.set_builder.create_from_asset_ids(
            instrumental_id=instrumental_path["id"],
            melody_id=melody_path["id"],
            lyrics_id=lyrics_path["id"],
            project_name=self.DEFAULT_LULLABY_PROJECT["project_name"],
            description=self.DEFAULT_LULLABY_PROJECT["description"],
            rule="default_lullaby_preset",
        )
        sample_path = self.sample_builder.create_from_latest_set()
        song_path = self.full_song_builder.create_from_latest_sample()
        mix_path = self.audio_mixer.prepare_latest_song_mix()
        exports_path = self.export_builder.generate_latest_song_audio_exports()
        manifest_path = exports_path / "audio_export_manifest.json"
        manifest = self.storage.read_json(manifest_path) if manifest_path.exists() else {}
        set_id = set_path.name
        return {
            "summary": "MP3 predefinido creado para Cancion de cuna para Isabella.",
            "set_id": set_id,
            "project": self.get_project(set_id),
            "instrumental": instrumental_path,
            "melody": melody_path,
            "lyrics": lyrics_path,
            "sample_path": str(sample_path),
            "song_path": str(song_path),
            "mix_path": str(mix_path),
            "exports_path": str(exports_path),
            "wav": manifest.get("wav", ""),
            "mp3": manifest.get("mp3", ""),
            "mp3_pending": manifest.get("mp3_pending", False),
            "ffmpeg_available": manifest.get("ffmpeg_available", False),
        }

    def list_sets(self) -> list[dict[str, object]]:
        return [self.describe_set(song_set) for song_set in self.storage.list_indexed_sets()]

    def get_set(self, set_id: str) -> dict[str, object]:
        song_set = self.storage.get_indexed_set(set_id)
        if song_set is None:
            raise ValueError("Set no encontrado.")
        return self.describe_set(song_set)

    def get_project(self, set_id: str) -> dict[str, object]:
        song_set = self.get_set(set_id)
        instrumental = self.storage.get_asset_draft_detail(str(song_set["instrumental_id"]))
        melody = self.storage.get_asset_draft_detail(str(song_set["melody_id"]))
        lyrics = self.storage.get_asset_draft_detail(str(song_set["lyrics_id"]))
        phase_data = self.storage.list_project_phase_data(set_id)
        if "music_plan" in phase_data and "music-plan" not in phase_data:
            phase_data["music-plan"] = dict(phase_data["music_plan"], phase="music-plan")
        phases = self._hydrate_project_phases(phase_data)
        return {
            "project": {
                "project_id": song_set["set_id"],
                "project_name": song_set["project_name"],
                "description": song_set["description"],
                "created_at": song_set["created_at"],
                "active_set_id": song_set["set_id"],
            },
            "set": song_set,
            "assets": {
                "instrumental": instrumental,
                "melody": melody,
                "lyrics": lyrics,
            },
            "samples": self.storage.list_samples_for_set(set_id),
            "songs": self.storage.list_songs_for_set(set_id),
            "events": self.storage.list_project_events(str(song_set["project_name"])),
            "phase_events": self.storage.list_project_phase_events(set_id),
            "phases": phases,
            "phase_data": phase_data,
            "ui_state": self.storage.get_project_ui_state(set_id),
            "source_of_truth": "sqlite",
            "snapshot_files": {
                "set_json": song_set.get("json_path", ""),
                "instrumental_intent": instrumental.get("intent", {}),
                "melody_intent": melody.get("intent", {}),
                "lyrics_intent": lyrics.get("intent", {}),
            },
        }

    def _hydrate_project_phases(self, phase_data: dict[str, object]) -> dict[str, object]:
        phases: dict[str, object] = {}
        for phase in ("intent", "lyrics", "music-plan", "midi", "instrumental", "voice", "voice-conversion", "mix", "mastering", "export", "production"):
            data = dict(phase_data.get(phase, {}))
            phases[phase] = {
                "phase_status": str(data.get("phase_status", "NOT_CREATED")),
                "change_source": str(data.get("change_source", "DEFAULT")),
                "validation_status": str(data.get("validation_status", "unknown")),
                "data": dict(data.get("data", {})),
                "updated_at": str(data.get("updated_at", "")),
                "completed_at": str(data.get("completed_at", "")),
            }
        return phases

    def update_project_description(self, set_id: str, payload: dict[str, object] | None = None) -> dict[str, object]:
        payload = payload or {}
        description = str(payload.get("description", "")).strip()
        updated = self.storage.update_indexed_set_description(set_id, description)
        if updated is None:
            raise ValueError("Set no encontrado.")
        return self.get_project(set_id)

    def save_project_phase_data(self, set_id: str, phase: str, payload: dict[str, object] | None = None) -> dict[str, object]:
        payload = payload or {}
        phase = self._canonical_editor_phase(phase)
        allowed_phases = {"intent", "lyrics", "music-plan", "midi", "instrumental", "voice", "voice-conversion", "mix", "mastering", "export", "production"}
        if phase not in allowed_phases:
            raise ValueError("Fase no soportada.")
        phase_status = {
            "intent": "intent_saved",
            "lyrics": "lyrics_saved",
            "music-plan": "style_saved",
            "midi": "midi_saved",
            "instrumental": "style_saved",
            "voice": "voice_saved",
            "voice-conversion": "voice_conversion_saved",
            "mix": "mix_saved",
            "mastering": "mastering_saved",
            "export": "export_saved",
            "production": "production_saved",
        }[phase]
        requested_phase_status = str(payload.get("phase_status", "COMPLETED")).upper()
        if requested_phase_status not in {"INITIALIZED", "DRAFT", "COMPLETED"}:
            requested_phase_status = "COMPLETED"
        change_source = str(payload.get("change_source", "USER")).upper()
        if change_source not in {"DEFAULT", "USER", "AI", "MIXED"}:
            change_source = "USER"
        saved = self.storage.save_project_phase_data(
            set_id,
            phase,
            dict(payload.get("data", {})),
            phase_status,
            phase_status=requested_phase_status,
            change_source=change_source,
            validation_status=str(payload.get("validation_status", "valid")),
        )
        if saved is None:
            raise ValueError("Set no encontrado.")
        return {"saved": saved, "project": self.get_project(set_id)}

    def initialize_project_phase(self, set_id: str, phase: str, payload: dict[str, object] | None = None) -> dict[str, object]:
        payload = payload or {}
        phase = self._canonical_editor_phase(phase)
        saved = self.storage.initialize_project_phase_data(set_id, phase, dict(payload.get("data", {})))
        if saved is None:
            raise ValueError("Set no encontrado.")
        return {"saved": saved, "project": self.get_project(set_id)}

    def reset_project_phase(self, set_id: str, phase: str) -> dict[str, object]:
        phase = self._canonical_editor_phase(phase)
        saved = self.storage.initialize_project_phase_data(set_id, phase, {})
        if saved is None:
            raise ValueError("Set no encontrado.")
        self.storage.create_project_phase_event(
            project_id=set_id,
            phase_name=phase,
            event_type="PHASE_RESET",
            source="USER",
            after=saved,
            message=f"Fase {phase} reiniciada a valores default.",
        )
        return {"saved": saved, "project": self.get_project(set_id)}

    def ai_suggest_project_phase(self, set_id: str, phase: str, payload: dict[str, object] | None = None) -> dict[str, object]:
        payload = payload or {}
        payload["phase_status"] = "DRAFT"
        payload["change_source"] = payload.get("change_source", "AI")
        return self.save_project_phase_data(set_id, phase, payload)

    def _canonical_editor_phase(self, phase: str) -> str:
        return {
            "music_plan": "music-plan",
            "musicPlan": "music-plan",
            "voice_conversion": "voice-conversion",
            "voiceConversion": "voice-conversion",
        }.get(str(phase), str(phase))

    def save_project_active_phase(self, set_id: str, payload: dict[str, object] | None = None) -> dict[str, object]:
        payload = payload or {}
        phase = str(payload.get("phase", "")).strip()
        allowed_phases = {"library", "intent", "lyrics", "music-plan", "midi", "instrumental", "voice", "production"}
        if phase not in allowed_phases:
            raise ValueError("Fase activa no soportada.")
        saved = self.storage.save_project_ui_state(set_id, phase)
        if saved is None:
            raise ValueError("Set no encontrado.")
        return {"ui_state": saved}

    def gemma_assistant(self, payload: dict[str, object] | None = None) -> dict[str, object]:
        payload = payload or {}
        set_id = str(payload.get("set_id", "")).strip()
        song_id = str(payload.get("song_id", "")).strip()
        active_professional_project = self.storage.get_song_project(song_id) if song_id else None
        project: dict[str, object] | None = None
        if set_id:
            project = self.get_project(set_id)
        else:
            sets = self.list_sets()
            if sets:
                project = self.get_project(str(sets[0]["set_id"]))

        readiness = self._workflow_readiness(project, active_professional_project, dict(payload.get("editor_phase_statuses", {})))
        if project is None:
            return {
                "model": self.settings.local_models.interpreter_model if self.settings else "Gemma 2 2B IT GGUF",
                "mode": "llama_cpp" if self.provider_registry.llama_cpp_status().get("enabled") else "local_guidance",
                "status": "needs_project",
                "message": self._run_gemma_or_fallback(
                    self._build_gemma_prompt(None, payload, readiness),
                    readiness,
                ),
                "context_used": [],
                "recommendations": readiness["recommendations"],
                "readiness": readiness,
                "technical_handoff_note": "Gemma conversa con el usuario; el director tecnico queda reservado para ajustes internos cuando exista proyecto activo.",
            }

        set_data = dict(project["set"])
        assets = dict(project["assets"])
        question = str(payload.get("question", "Que sigue para terminar esta cancion?")).strip()
        prompt = self._build_gemma_prompt(project, payload, readiness)
        grounded_status = self._asks_for_grounded_status(question)
        technical_review = self.model_orchestrator.review_sqlite_project_state(
            {
                "phase": "technical_review",
                "project_id": str(set_data["set_id"]),
                "project_name": str(set_data["project_name"]),
                "description": f"Revision tecnica interna para Gemma: {question}",
                "question": question,
                "context": self._technical_project_context(project, readiness),
            }
        )
        gemma_message = (
            self._deterministic_gemma_guidance(readiness, dict(technical_review.get("validation", {})))
            if grounded_status
            else self._run_gemma_or_fallback(prompt, readiness)
        )
        if grounded_status:
            return {
                "model": self.settings.local_models.interpreter_model if self.settings else "Gemma 2 2B IT GGUF",
                "mode": "sqlite_guidance",
                "status": "active_project_loaded",
                "question": question,
                "project_name": set_data["project_name"],
                "set_id": set_data["set_id"],
                "message": gemma_message,
                "context_used": [
                    "project_name",
                    "description",
                    "saved editor phases",
                    "professional project status",
                    "set.json snapshot",
                ],
                "recommendations": readiness["recommendations"],
                "missing_before_final": readiness["missing"],
                "readiness": readiness,
                "llama_cpp": self.provider_registry.llama_cpp_status(),
                "handoff": None,
                "technical_handoff": technical_review["handoff"],
                "technical_validation": technical_review["validation"],
                "technical_handoff_note": "Gemma respondio con base en SQLite y en una revision tecnica interna persistida por el orquestador.",
            }
        handoff = self.model_orchestrator.run_handoff(
            {
                "model_role": "assistant",
                "task_type": "transversal_project_assistance",
                "phase": "assistant_review",
                "project_id": str(set_data["set_id"]),
                "project_name": str(set_data["project_name"]),
                "description": str(set_data["description"]),
                "question": question,
                "context": {
                    "instrumental_intent": assets["instrumental"].get("intent", {}),
                    "melody_intent": assets["melody"].get("intent", {}),
                    "lyrics_intent": assets["lyrics"].get("intent", {}),
                    "saved_editor_phases": readiness.get("saved_editor_phases", {}),
                    "active_professional_project": readiness.get("professional_project", {}),
                    "set": set_data,
                },
            }
        )
        technical_handoff = self.model_orchestrator.run_handoff(
            {
                "model_role": "technical",
                "task_type": "gemma_to_technical_director_pipeline_review",
                "phase": "technical_review",
                "project_id": str(set_data["set_id"]),
                "project_name": str(set_data["project_name"]),
                "description": f"Gemma traduce la solicitud del usuario para revision tecnica interna: {question}",
                "question": question,
                "context": {
                    "missing_before_final": readiness["missing"],
                    "saved_editor_phases": readiness.get("saved_editor_phases", {}),
                    "active_professional_project": readiness.get("professional_project", {}),
                    "local_pipeline": self.local_pipeline_status(),
                    "sqlite_technical_validation": technical_review["validation"],
                },
            }
        )
        return {
            "model": self.settings.local_models.interpreter_model if self.settings else "Gemma 2 2B IT GGUF",
            "mode": "sqlite_guidance" if grounded_status else "llama_cpp" if self.provider_registry.llama_cpp_status().get("available") else "local_guidance",
            "status": "active_project_loaded",
            "question": question,
            "project_name": set_data["project_name"],
            "set_id": set_data["set_id"],
            "message": gemma_message,
            "context_used": [
                "project_name",
                "description",
                "instrumental intent",
                "vocal/melody intent",
                "lyrical intent",
                "selected assets",
                "saved editor phases",
                "professional project status",
                "set.json snapshot",
                "manifest.json",
                "intent.json",
            ],
            "recommendations": readiness["recommendations"],
            "missing_before_final": readiness["missing"],
            "readiness": readiness,
            "llama_cpp": self.provider_registry.llama_cpp_status(),
            "handoff": handoff,
            "technical_handoff": technical_handoff,
            "technical_validation": technical_review["validation"],
            "technical_handoff_note": "Gemma conversa con el usuario y envio un handoff interno al director tecnico para revisar el pipeline.",
        }

    def qwen_technical_assistant(self, payload: dict[str, object] | None = None) -> dict[str, object]:
        payload = payload or {}
        question = str(payload.get("question", "Que ajuste tecnico necesita el pipeline?")).strip()
        set_id = str(payload.get("set_id", "")).strip()
        project = self.get_project(set_id) if set_id else None
        prompt = (
            f"Pregunta tecnica: {question}\n"
            f"Proyecto activo: {project['project'] if project else 'sin proyecto cargado'}\n"
            f"Estado modelos locales: {self.provider_registry.model_status().get('local', {})}\n"
            "Responde como Qwen3 tecnico. Enfocate en codigo, arquitectura, workers, SQLite, ffmpeg, "
            "llama.cpp, memoria y debugging. No reemplaces el criterio creativo de Gemma."
        )
        try:
            result = self.provider_registry.technical_with_active_provider(prompt, "technical_song_pipeline")
            message = str(result["summary"])
            mode = str(result.get("mode", "local_guidance"))
        except Exception:
            message = (
                "Qwen tecnico esta en guia de respaldo porque llama.cpp no respondio. "
                "Siguiente ajuste recomendado: verificar variables SONG_AI_LLAMA_CPP_* y que ffmpeg/SQLite "
                "esten disponibles antes de workers reales."
            )
            mode = "local_guidance"
        handoff = self.model_orchestrator.run_handoff(
            {
                "model_role": "technical",
                "task_type": "technical_adjustment",
                "phase": "technical_review",
                "project_id": str(project["project"]["project_id"]) if project else "technical",
                "project_name": str(project["project"]["project_name"]) if project else "Proyecto tecnico",
                "description": question,
            }
        )
        return {
            "model": "Qwen3 4B GGUF",
            "mode": mode,
            "status": "technical_role_active",
            "message": message,
            "scope": ["codigo", "debugging", "arquitectura", "workers", "ffmpeg", "SQLite", "llama.cpp"],
            "handoff": handoff,
        }

    def _workflow_readiness(
        self,
        project: dict[str, object] | None,
        selected_professional_project: dict[str, object] | None = None,
        ui_editor_phase_statuses: dict[str, object] | None = None,
    ) -> dict[str, object]:
        drafts = self.list_drafts()
        counts = {
            "instrumental": len([item for item in drafts if item["asset_type"] == "instrumental"]),
            "melody": len([item for item in drafts if item["asset_type"] == "melody"]),
            "lyrics": len([item for item in drafts if item["asset_type"] == "lyrics"]),
        }
        sets = self.list_sets()
        samples = list(project["samples"]) if project is not None else []
        songs = list(project["songs"]) if project is not None else []
        phase_data = dict(project.get("phase_data", {})) if project is not None else {}
        ui_editor_phase_statuses = ui_editor_phase_statuses or {}
        saved_editor_phases = {
            phase: bool(dict(phase_data.get(phase, {})).get("status"))
            for phase in ("intent", "lyrics", "music-plan", "midi", "instrumental", "voice", "production")
        }
        ui_ready_phases = {
            phase: str(ui_editor_phase_statuses.get(phase, "")).upper() == "READY"
            for phase in ("intent", "lyrics", "music-plan", "midi", "instrumental", "voice", "production")
        }
        required_editor_phases = ("intent", "lyrics", "music-plan", "midi", "instrumental", "voice")
        editor_ready_for_production = all(saved_editor_phases.get(phase, False) for phase in required_editor_phases)
        professional_projects = self.storage.list_song_projects()
        active_professional_project = (
            selected_professional_project
            or next(
                (item for item in professional_projects if str(item.get("status")) != "completed"),
                professional_projects[0] if professional_projects else None,
            )
        )
        professional_next = self._professional_next_step(active_professional_project)
        missing: list[str] = []
        if active_professional_project is not None:
            if professional_next["status"] != "completed":
                missing.append(str(professional_next["missing_label"]))
        elif editor_ready_for_production:
            missing.append("Production")
        else:
            if counts["instrumental"] == 0:
                missing.append("instrumental")
            if counts["melody"] == 0:
                missing.append("melodia")
            if counts["lyrics"] == 0:
                missing.append("letra")
            if not sets:
                missing.append("proyecto activo")

        recommendations = [
            "Trabaja siempre sobre un proyecto activo para conservar intencion, letra, plan musical, MIDI y audio juntos.",
            "Revisa la letra editable antes de exportar para mejorar metrica, rima y narrativa.",
            "El cierre correcto del flujo profesional es especificacion, letra, revision, plan musical, MIDI, audio, mastering y export.",
        ]
        if active_professional_project is not None:
            recommendations.insert(0, str(professional_next["recommendation"]))
        elif editor_ready_for_production:
            recommendations.insert(
                0,
                "Ya tienes Intent, Lyrics, Music Plan, MIDI, Instrumental y Voice guardados. Ve a Production y ejecuta Enviar intent, Mastering/Full Song y Export sobre el proyecto activo.",
            )
        else:
            recommendations.insert(1, "Crea o carga un proyecto profesional desde Biblioteca y continua por fases.")
            if "instrumental" in missing:
                recommendations.insert(0, "Define el instrumental: genero, mood, BPM, tonalidad e instrumentos.")
            if "melodia" in missing:
                recommendations.insert(0, "Define la melodia vocal: estilo cantado, rango, energia y estructura.")
            if "letra" in missing:
                recommendations.insert(0, "Crea o edita una letra completa con versos, coro y cierre emocional.")

        return {
            "draft_counts": counts,
            "sets": len(sets),
            "samples": len(samples),
            "songs": len(songs),
            "saved_editor_phases": saved_editor_phases,
            "ui_ready_phases": ui_ready_phases,
            "ui_editor_phase_statuses": ui_editor_phase_statuses,
            "editor_ready_for_production": editor_ready_for_production,
            "professional_project": active_professional_project,
            "professional_next": professional_next,
            "missing": missing,
            "recommendations": recommendations,
        }

    def _professional_next_step(self, project: dict[str, object] | None) -> dict[str, object]:
        if project is None:
            return {
                "status": "missing_project",
                "missing_label": "proyecto profesional activo",
                "recommendation": "Crea o carga un proyecto desde Biblioteca antes de generar audio final.",
            }
        if str(project.get("status")) == "completed":
            return {
                "status": "completed",
                "missing_label": "",
                "recommendation": "El proyecto ya tiene export preparado. Revisa Production y descarga los artefactos finales.",
            }
        current_phase = str(project.get("current_phase") or PHASE_SEQUENCE[0].value)
        phase_by_value = {phase.value: phase for phase in PHASE_SEQUENCE}
        current = phase_by_value.get(current_phase, PHASE_SEQUENCE[0])
        label = PHASE_LABELS.get(current, current_phase)
        phase_actions = {
            "SONG_SPEC_COLLECTION": "Completa la intencion con Gemma hasta que el director tecnico apruebe song_spec.json.",
            "LYRICS_GENERATION": "Genera o edita la letra cantable por secciones.",
            "LYRICS_TECHNICAL_REVIEW": "Aprueba la letra con revision tecnica antes de planear musica.",
            "MUSIC_PLAN_GENERATION": "Genera el plan musical: BPM, tonalidad, acordes, estructura y transiciones.",
            "MIDI_GENERATION": "Crea el MIDI base obligatorio con melodia vocal guia y progresion armonica.",
            "INSTRUMENTAL_GENERATION": "Genera el instrumental o confirma la ruta Full Song si ACE-Step sera el proveedor principal.",
            "VOCAL_SYNTHESIS": "Genera la voz cantada real o continua por Full Song si ACE-Step integra voz e instrumental.",
            "VOICE_CONVERSION": "Resuelve la conversion vocal opcional o saltala si no aplica.",
            "MIXING": "Mezcla stems si usas ruta separada, o pasa a Mastering con Full Song.",
            "MASTERING": "Ejecuta Mastering/Full Song para producir final_song.wav y final_song.mp3.",
            "EXPORT": "Prepara export_manifest.json y descarga MP3/WAV/FLAC/MIDI/ZIP.",
        }
        return {
            "status": str(project.get("status", "pending")),
            "missing_label": label,
            "recommendation": phase_actions.get(current_phase, f"Continua la fase profesional: {label}."),
        }

    def _technical_project_context(
        self,
        project: dict[str, object],
        readiness: dict[str, object],
    ) -> dict[str, object]:
        return {
            "project": dict(project.get("project", {})),
            "set": dict(project.get("set", {})),
            "assets": dict(project.get("assets", {})),
            "phase_data": dict(project.get("phase_data", {})),
            "ui_state": dict(project.get("ui_state", {})),
            "saved_editor_phases": dict(readiness.get("saved_editor_phases", {})),
            "ui_ready_phases": dict(readiness.get("ui_ready_phases", {})),
            "ui_editor_phase_statuses": dict(readiness.get("ui_editor_phase_statuses", {})),
            "active_professional_project": dict(readiness.get("professional_project") or {}),
            "professional_next": dict(readiness.get("professional_next") or {}),
            "missing_before_final": list(readiness.get("missing", [])),
            "local_pipeline": self.local_pipeline_status(),
        }

    def _build_gemma_prompt(
        self,
        project: dict[str, object] | None,
        payload: dict[str, object],
        readiness: dict[str, object],
    ) -> str:
        question = str(payload.get("question", "Que sigue para terminar esta cancion?")).strip()
        if project is None:
            return (
                f"Pregunta del usuario: {question}\n"
                f"Estado de trabajo desde SQLite: {readiness}\n"
                "Ayuda al usuario a continuar el pipeline profesional. El flujo principal es proyecto, "
                "spec, letra, revision, plan musical, MIDI, audio, mastering y export. "
                "No presentes sample/checkpoint como requisito del flujo principal."
            )
        set_data = dict(project["set"])
        assets = dict(project["assets"])
        lyrics = dict(assets["lyrics"]).get("content", "")
        return (
            f"Pregunta del usuario: {question}\n"
            f"Proyecto activo: {set_data.get('project_name')}\n"
            f"Descripcion: {set_data.get('description')}\n"
            f"Set activo: {set_data}\n"
            f"Instrumental intent: {dict(assets['instrumental']).get('intent', {})}\n"
            f"Melodia intent: {dict(assets['melody']).get('intent', {})}\n"
            f"Letra intent: {dict(assets['lyrics']).get('intent', {})}\n"
            f"Letra editable lyrics.md:\n{lyrics}\n"
            f"Fases del editor guardadas: {readiness.get('saved_editor_phases', {})}\n"
            f"Proyecto profesional activo: {readiness.get('professional_project', {})}\n"
            f"Estado del flujo: {readiness}\n"
            "Responde en espanol, breve y accionable. Debes ayudar desde inicio de proyecto hasta MP3 final. "
            "No propongas cambios que rompan la intencion instrumental, vocal o lirica."
        )

    def _asks_for_grounded_status(self, question: str) -> bool:
        normalized = question.lower()
        return any(
            token in normalized
            for token in (
                "que sigue",
                "qué sigue",
                "siguiente",
                "terminar",
                "final",
                "completa",
                "proyecto activo",
                "estoy en",
                "estado",
                "falta",
                "faltan",
                "production",
                "seleccionado",
                "seleccionados",
                "cargar proyecto",
            )
        )

    def _deterministic_gemma_guidance(
        self,
        readiness: dict[str, object],
        technical_validation: dict[str, object] | None = None,
    ) -> str:
        technical_validation = technical_validation or {}
        saved = dict(readiness.get("saved_editor_phases", {}))
        saved_labels = [
            label
            for phase, label in (
                ("intent", "Intent"),
                ("lyrics", "Lyrics"),
                ("music-plan", "Music Plan"),
                ("midi", "MIDI"),
                ("instrumental", "Instrumental"),
                ("voice", "Voice"),
            )
            if saved.get(phase)
        ]
        prefix = ""
        if saved_labels:
            prefix = f"Si: veo guardado {', '.join(saved_labels)}. "
        instruction = str(technical_validation.get("gemma_instruction") or "").strip()
        next_action = str(technical_validation.get("next_action") or "").strip()
        missing_items = [str(item) for item in list(technical_validation.get("missing_items", []))]
        if instruction:
            action_text = f" Siguiente paso: {next_action}" if next_action else ""
            if next_action and next_action not in instruction:
                return f"{prefix}{instruction}.{action_text}".strip()
            return f"{prefix}{instruction}".strip()
        if readiness.get("professional_project"):
            project = dict(readiness["professional_project"])
            return (
                f"{prefix}Tambien hay un proyecto profesional activo: {project.get('title', project.get('id'))}. "
                f"El siguiente paso real es: {readiness['recommendations'][0]}"
            )
        if readiness.get("editor_ready_for_production"):
            return (
                f"{prefix}Si: estas en el proyecto activo. Las fases creativas ya estan definidas; ahora Production debe ejecutar "
                "las tareas sobre este mismo proyecto. Sigue con Enviar intent, luego Mastering/Full Song y Export para que "
                "ACE-Step intente generar la cancion completa final."
            )
        if readiness.get("sets", 0):
            return (
                f"{prefix}Si estas en un proyecto activo. Para convertirlo en cancion completa falta resolver "
                f"{', '.join(str(item) for item in readiness['missing']) or 'Production'}. "
                f"Siguiente accion: {readiness['recommendations'][0]}"
            )
        return f"{prefix}Pendiente: {', '.join(str(item) for item in readiness['missing'])}. Siguiente accion: {readiness['recommendations'][0]}"

    def _run_gemma_or_fallback(self, prompt: str, readiness: dict[str, object]) -> str:
        try:
            result = self.provider_registry.interpret_with_active_provider(prompt, "active_song_project")
            if str(result.get("mode", "")) == "llama_cpp":
                return str(result["summary"])
        except Exception:
            pass
        missing_items = [
            str(item)
            for item in readiness["missing"]
            if str(item) not in {"sample/checkpoint", "cancion completa"}
        ]
        missing = ", ".join(missing_items) or "ninguna fase critica bloqueada"
        llama_cpp = self.provider_registry.llama_cpp_status()
        reason = str(llama_cpp.get("reason") or llama_cpp.get("error") or "").strip()
        if llama_cpp.get("missing_models"):
            prefix = "Gemma esta usando guia local porque faltan los modelos GGUF de llama.cpp."
        elif not bool(llama_cpp.get("available")):
            prefix = "Gemma esta usando guia local porque llama.cpp no respondio."
        else:
            prefix = "Gemma esta usando guia local porque la respuesta de llama.cpp no fue usable."
        detail = f" Detalle: {reason}." if reason else ""
        return f"{prefix}{detail} Pendiente: {missing}. Siguiente accion: {readiness['recommendations'][0]}"

    def describe_set(self, song_set: dict[str, object]) -> dict[str, object]:
        compatibility = dict(song_set.get("compatibility_data", {}))
        return {
            **song_set,
            "ai_management": {
                "status": "ready_for_interpreter_provider",
                "required_steps": [
                    "1. Instrumental",
                    "2. Melodia",
                    "3. Letra",
                ],
                "completion_rule": (
                    "Para usar el flujo legado de set debe existir al menos un draft de instrumental, "
                    "melodia y letra. El flujo principal recomendado usa proyecto profesional y fases."
                ),
                "summary": (
                    f"Proyecto '{song_set.get('project_name', song_set['set_id'])}' compuesto por instrumental "
                    f"{song_set['instrumental_id']}, melodia {song_set['melody_id']} "
                    f"y letra {song_set['lyrics_id']}."
                ),
                "compatibility_status": compatibility.get("status", "unknown"),
                "next_suggestion": "El set ya tiene instrumental, melodia y letra. Para el flujo principal, cargalo como proyecto activo y continua las fases profesionales hasta MIDI, Mastering y Export.",
            },
        }

    def create_sample(self) -> dict[str, str]:
        return self.path_response(self.sample_builder.create_from_latest_set())

    def create_song(self) -> dict[str, str]:
        return self.path_response(self.full_song_builder.create_from_latest_sample())

    def providers(self) -> dict[str, list[dict[str, object]]]:
        return self.provider_registry.summary()

    def model_status(self) -> dict[str, object]:
        return self.provider_registry.model_status()

    def studio_status(self) -> dict[str, object]:
        return self.provider_registry.studio_status()

    def local_pipeline_status(self) -> dict[str, object]:
        if self.local_song_pipeline is None:
            return {
                "ready": False,
                "missing": ["settings"],
                "requirements": [],
                "mode": "local_only",
            }
        status = self.local_song_pipeline.status()
        return {
            "ready": status.ready,
            "missing": status.missing,
            "requirements": status.requirements,
            "mode": "local_only",
            "pro_mode": "disabled",
            "limits": {
                "local_command_timeout_seconds": self.settings.local_models.local_command_timeout_seconds if self.settings else 3600,
                "max_full_song_duration_seconds": self.settings.local_models.max_full_song_duration_seconds if self.settings else 360,
                "allow_cpu_full_song": self.settings.local_models.allow_cpu_full_song if self.settings else False,
            },
        }

    def system_status(self, bootstrap_status: dict[str, object] | None = None) -> dict[str, object]:
        bootstrap_status = bootstrap_status or {"status": "idle"}
        local_pipeline = self.local_pipeline_status()
        llama_cpp = self.provider_registry.llama_cpp_status()
        components: list[dict[str, object]] = [
            {
                "id": "sqlite",
                "label": "SQLite activo",
                "status": "ready" if self.storage.db_path.exists() else "missing",
                "detail": str(self.storage.db_path),
                "restartable": False,
            },
            {
                "id": "ffmpeg",
                "label": "ffmpeg mezcla/export",
                "status": "ready" if shutil.which("ffmpeg") else "missing",
                "detail": shutil.which("ffmpeg") or "No disponible en PATH local.",
                "restartable": False,
            },
            {
                "id": "bootstrap",
                "label": "Bootstrap local",
                "status": str(bootstrap_status.get("status", "idle")),
                "detail": str(bootstrap_status.get("message", "Preparacion de modelos/providers en data/.")),
                "restartable": True,
            },
        ]
        llm_models = dict(llama_cpp.get("models", {}))
        for role, label in (("gemma", "Gemma GGUF"), ("qwen", "Qwen GGUF")):
            metadata = dict(llm_models.get(role, {}))
            exists = bool(metadata.get("exists"))
            components.append(
                {
                    "id": f"llm_{role}",
                    "label": label,
                    "status": "ready" if exists else "missing",
                    "detail": str(metadata.get("path") or llama_cpp.get("reason", "Modelo GGUF pendiente.")),
                    "restartable": True,
                }
            )
        for requirement in list(local_pipeline.get("requirements", [])):
            configured = bool(requirement.get("configured"))
            optional = requirement.get("required_for_real_output") is False
            components.append(
                {
                    "id": str(requirement["role"]),
                    "label": str(requirement["role"]).replace("_", " ").title(),
                    "status": "ready" if configured else "optional" if optional else "missing",
                    "detail": str(requirement.get("detail", requirement.get("engine", ""))),
                    "restartable": True,
                }
            )

        for env_name, label in (
            ("SONG_AI_MODEL_ROOT", "Volumen de modelos"),
            ("SONG_AI_PROVIDER_ROOT", "Volumen de providers"),
            ("SONG_AI_PROVIDER_CACHE", "Cache de providers"),
        ):
            path = Path(os.getenv(env_name, ""))
            components.append(
                {
                    "id": env_name.lower(),
                    "label": label,
                    "status": "ready" if path.exists() else "missing",
                    "detail": str(path),
                    "restartable": True,
                }
            )

        return {
            "mode": "local_only",
            "ready": all(
                component["status"] in {"ready", "optional"}
                for component in components
                if component["id"] != "bootstrap"
            ),
            "components": components,
            "bootstrap": bootstrap_status,
            "local_pipeline": local_pipeline,
        }

    def project_phase_status(self, set_id: str | None = None) -> dict[str, object]:
        project: dict[str, object] | None = None
        if set_id:
            project = self.get_project(set_id)
        else:
            sets = self.list_sets()
            if sets:
                project = self.get_project(str(sets[0]["set_id"]))

        draft_counts = self._workflow_readiness(project)["draft_counts"]
        samples = list(project["samples"]) if project else []
        songs = list(project["songs"]) if project else []
        latest_song_dir = Path(str(songs[-1]["path"])) if songs else None
        phases = [
            self._phase("instrumental", "1. Instrumental", int(draft_counts["instrumental"]) > 0),
            self._phase("melody", "2. Melodia", int(draft_counts["melody"]) > 0),
            self._phase("lyrics", "3. Letra", int(draft_counts["lyrics"]) > 0),
            self._phase("set", "4. Set/proyecto", project is not None),
            self._phase("sample", "5. Sample/checkpoint", len(samples) > 0),
            self._phase("song", "6. Cancion completa", len(songs) > 0),
            self._phase(
                "mix",
                "7. Mezcla preparada",
                bool(latest_song_dir and (latest_song_dir / "mix" / "mix_manifest.json").exists()),
            ),
            self._phase(
                "exports",
                "8. Exports preparados",
                bool(latest_song_dir and (latest_song_dir / "exports" / "manifest.json").exists()),
            ),
            self._phase(
                "local_final",
                "9. Final local MP3",
                bool(
                    latest_song_dir
                    and (latest_song_dir / "exports" / "local_final_manifest.json").exists()
                    and (latest_song_dir / "exports" / "final_mix.mp3").exists()
                ),
            ),
        ]
        return {
            "set_id": str(project["set"]["set_id"]) if project else "",
            "project_name": str(project["project"]["project_name"]) if project else "",
            "ready_for_final": all(phase["ready"] for phase in phases[:6]),
            "complete": all(phase["ready"] for phase in phases),
            "phases": phases,
        }

    def orchestration_status(self) -> dict[str, object]:
        return self.model_orchestrator.status()

    def list_tasks(self) -> list[dict[str, object]]:
        return self.storage.list_tasks()

    def list_model_runs(self) -> list[dict[str, object]]:
        return self.storage.list_model_runs()

    def list_project_events(self, project_id: str | None = None) -> list[dict[str, object]]:
        return self.storage.list_project_events(project_id)

    def run_model_handoff(self, payload: dict[str, object]) -> dict[str, object]:
        return self.model_orchestrator.run_handoff(payload)

    def json_configs(self) -> list[dict[str, str]]:
        return self.storage.list_json_config_paths()

    def export_sets_to_json(self) -> dict[str, object]:
        result = self.storage.export_indexed_sets_to_json()
        return {
            **result,
            "summary": (
                f"{result['exported_count']} set(s) exportados desde SQLite a JSON. "
                "Si el archivo existia, fue sobrescrito con la version persistida en base de datos."
            ),
        }

    def prepare_mix(self) -> dict[str, str]:
        return self.path_response(self.audio_mixer.prepare_latest_song_mix())

    def prepare_exports(self) -> dict[str, str]:
        return self.path_response(self.export_builder.prepare_latest_song_exports())

    def generate_audio_exports(self) -> dict[str, str]:
        return self.path_response(self.export_builder.generate_latest_song_audio_exports())

    def generate_local_final_song(self) -> dict[str, object]:
        if self.local_song_pipeline is None:
            raise ValueError("No hay configuracion local para generar cancion final.")
        latest_song = self.storage.get_latest_song()
        if latest_song is None:
            raise ValueError("No hay cancion completa. Crea set, sample y cancion antes de generar final local.")
        song_dir = Path(str(latest_song["path"]))
        context = self.export_builder.load_render_context(latest_song)
        result = self.local_song_pipeline.generate(context, song_dir)
        self.storage.write_json(
            song_dir / "exports" / "local_final_manifest.json",
            {
                "song_id": latest_song["song_id"],
                "set_id": latest_song.get("set_id", ""),
                **result,
            },
        )
        return {
            "summary": "Cancion final local generada sin modo pro.",
            **result,
        }

    def latest_audio_export_file(self, extension: str = "mp3") -> tuple[Path, str]:
        safe_extension = extension.lower().strip().lstrip(".")
        if safe_extension not in {"mp3", "wav"}:
            raise ValueError("Formato de descarga no soportado. Usa mp3 o wav.")

        professional_file = self._latest_professional_audio_export_file(safe_extension)
        if professional_file is not None:
            path, filename, _media_type = professional_file
            return path, filename

        latest_song = self.storage.get_latest_song()
        if latest_song is None:
            raise ValueError("No hay cancion completa para descargar.")

        song_dir = Path(str(latest_song["path"]))
        export_path = song_dir / "exports" / f"final_mix.{safe_extension}"
        local_final_manifest = song_dir / "exports" / "local_final_manifest.json"
        if not export_path.exists():
            if safe_extension == "mp3":
                pending_path = song_dir / "exports" / "final_mix.mp3.pending.txt"
                if pending_path.exists():
                    raise ValueError("El MP3 aun no esta disponible. Instala ffmpeg y vuelve a generar el export.")
            raise ValueError(f"No existe final_mix.{safe_extension}. Genera WAV/MP3 antes de descargar.")
        if not local_final_manifest.exists():
            raise ValueError(
                "El archivo disponible es una maqueta tecnica, no una cancion final local con voz cantada. "
                "Usa 'Generar cancion local final' y espera a que se cree local_final_manifest.json."
            )

        set_id = str(latest_song.get("set_id", ""))
        song_set = self.storage.get_indexed_set(set_id)
        project_name = str(song_set.get("project_name", latest_song["song_id"])) if song_set else str(latest_song["song_id"])
        filename = f"{self._safe_download_name(project_name)}.{safe_extension}"
        return export_path, filename

    def _latest_professional_audio_export_file(self, extension: str) -> tuple[Path, str, str] | None:
        artifact_type = f"final_song_{extension}"
        for project in self.storage.list_song_projects():
            try:
                return self.professional_songs.artifact_download_file(str(project["id"]), artifact_type)
            except ValueError:
                continue
        return None

    def save_template(self) -> dict[str, str]:
        return self.path_response(self.template_builder.save_latest_set_template())

    def path_response(self, path: Path) -> dict[str, str]:
        return {"path": str(path), "id": path.name}

    def _phase(self, phase_id: str, label: str, ready: bool) -> dict[str, object]:
        return {
            "id": phase_id,
            "label": label,
            "ready": ready,
            "status": "ready" if ready else "missing",
        }

    def _safe_download_name(self, value: str) -> str:
        normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip()).strip("._-")
        return normalized or "song-ai-final-mix"
