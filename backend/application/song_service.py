from pathlib import Path
import re
import os
import shutil
from typing import Any
from uuid import NAMESPACE_URL, uuid5
from threading import Lock

from audio.mixer import AudioMixer
from audio.local_song_pipeline import LocalSongPipeline
from audio.resource_monitor import ResourceMonitor
from application.model_orchestrator import ModelOrchestrator
from application.model_manager_service import ModelManagerService
from application.audio_download_service import AudioDownloadService
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
from models.music_validation import validate_bpm
from providers.registry import ProviderRegistry
from config.settings import Settings
from adapters.ace_step_steering import AceStepSteering
from application.ace_step_plan_compiler import PreviewAceStepPlan
from adapters.ace_step_source_audio import AceStepSourceAudio
from application.ace_step_configuration import EditAceStepConfiguration
from application.ace_step_plan_review import ReviewAceStepPlan
from adapters.sqlite.ace_step_plan_repository import AceStepPlanRepository
from adapters.ace_step_candidate_runner import AceStepCandidateRunner
from adapters.sample_audio_evidence import inspect_sample_wav
from application.ace_step_candidate_service import AceStepCandidateService
from application.ace_step_candidate_jobs import AceStepCandidateJobs
from adapters.background_dispatcher import BackgroundDispatcher
from adapters.ace_step_preflight import AceStepPreflight


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
        self._set_creation_lock = Lock()
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
            steering=AceStepSteering(Path(__file__).resolve().parents[2]),
        )
        self.model_orchestrator = ModelOrchestrator(storage, self.provider_registry)
        self.provider_registry.inference_guard = self.model_orchestrator.require_planning_available
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
            model_orchestrator=self.model_orchestrator,
        )
        self.audio_downloads = AudioDownloadService(storage, self.professional_songs)
        self.ace_candidate_jobs = AceStepCandidateJobs(storage, self.generate_ace_step_candidate,
                                                       self._ace_plan_review(), BackgroundDispatcher(),
                                                       AceStepPreflight(Path(__file__).resolve().parents[2]).inspect_plan,
                                                       orchestrator=self.model_orchestrator)

    def bootstrap(self) -> None:
        self.storage.ensure_project_layout()
        self._mark_interrupted_professional_runs()
        self.ace_candidate_jobs.recover_interrupted()

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

    def get_professional_specification(self, song_id: str) -> dict[str, object]:
        result = self.professional_songs.get_song_specification(song_id)
        project = self.storage.get_song_project(song_id)
        result["source_artifacts"] = [dict(item) for item in project.get("artifacts", [])
                                      if str(item.get("file_path", "")).lower().endswith(".wav")]
        return result

    def confirm_professional_specification(self, song_id: str, payload: dict[str, object]) -> dict[str, object]:
        return self.professional_songs.confirm_song_specification(song_id, payload)

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

    def master_professional_song(self, song_id: str, generation_profile: str | None = None) -> dict[str, object]:
        return self.professional_songs.master_song(song_id, generation_profile=generation_profile)

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
            bpm=validate_bpm(payload.get("bpm", 96)),
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
            bpm=validate_bpm(payload.get("bpm", 96)),
            key=str(payload.get("key", "C major")),
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
        content = str(payload.get("content", "")).strip()
        if content:
            self.storage.update_lyrics_markdown(path.name, content)
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
        with self._set_creation_lock:
            return self._create_set_locked(payload)

    def _create_set_locked(self, payload: dict[str, object] | None = None) -> dict[str, str]:
        payload = payload or {}
        project_name = str(payload.get("project_name", "")).strip() or "Proyecto automatico"
        description = str(payload.get("description", "")).strip()
        if not description:
            description = "Cancion completa creada con los primeros drafts disponibles."
        asset_ids = (payload.get("instrumental_id"), payload.get("melody_id"), payload.get("lyrics_id"))
        if any(asset_ids):
            if not all(isinstance(asset_id, str) and asset_id.strip() for asset_id in asset_ids):
                raise ValueError("Selecciona instrumental, melodia y letra para crear el set.")
            request_id = str(payload.get("request_id", "")).strip()
            if len(request_id) > 128:
                raise ValueError("Identificador de solicitud demasiado largo.")
            stable_set_id = f"set-{uuid5(NAMESPACE_URL, 'song-ai:set:' + request_id).hex}" if request_id else None
            if stable_set_id:
                existing = self.storage.get_indexed_set(stable_set_id)
                if existing:
                    if (existing.get("instrumental_id"), existing.get("melody_id"), existing.get("lyrics_id"),
                        existing.get("project_name"), existing.get("description")) != (*asset_ids, project_name, description):
                        raise ValueError("Esta solicitud ya se uso con otro proyecto o seleccion de assets.")
                    return self.path_response(self.storage.data_dir / "sets" / stable_set_id)
            return self.path_response(self.set_builder.create_from_asset_ids(
                instrumental_id=asset_ids[0], melody_id=asset_ids[1], lyrics_id=asset_ids[2],
                project_name=project_name, description=description, set_id=stable_set_id,
            ))
        return self.path_response(
            self.set_builder.create_first_valid_set(
                project_name=project_name,
                description=description,
            )
        )

    def create_default_lullaby_mp3(self, *, approved_mock_fixture: bool = False) -> dict[str, Any]:
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
        set_id = set_path.name
        if not approved_mock_fixture:
            return {
                "summary": "Preset preparado. Revisa y aprueba el sample antes de crear el MP3.",
                "status": "waiting_sample_approval",
                "set_id": set_id,
                "sample_id": sample_path.name,
                "sample_path": str(sample_path),
                "project": self.get_project(set_id),
                "instrumental": instrumental_path,
                "melody": melody_path,
                "lyrics": lyrics_path,
            }
        self.storage.approve_sample(set_id, sample_path.name)
        song_path = self.full_song_builder.create_from_latest_sample()
        mix_path = self.audio_mixer.prepare_latest_song_mix()
        exports_path = self.export_builder.generate_latest_song_audio_exports()
        manifest_path = exports_path / "audio_export_manifest.json"
        manifest = self.storage.read_json(manifest_path) if manifest_path.exists() else {}
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

    def delete_project(self, set_id: str) -> dict[str, object]:
        result = self.storage.delete_indexed_project(set_id)
        return {
            **result,
            "remaining_projects": len(self.list_sets()),
        }

    def get_project(self, set_id: str) -> dict[str, object]:
        song_set = self.get_set(set_id)
        instrumental = self.storage.get_asset_draft_detail(str(song_set["instrumental_id"]))
        melody = self.storage.get_asset_draft_detail(str(song_set["melody_id"]))
        lyrics = self.storage.get_asset_draft_detail(str(song_set["lyrics_id"]))
        phase_data = self.storage.list_project_phase_data(set_id)
        if "music_plan" in phase_data and "music-plan" not in phase_data:
            phase_data["music-plan"] = dict(phase_data["music_plan"], phase="music-plan")
        phase_data = self._repair_text_encoding(phase_data)
        phases = self._hydrate_project_phases(phase_data)
        current_fingerprint = self.storage.set_generation_fingerprint(set_id)
        samples = self.storage.list_samples_for_set(set_id)
        for sample in samples:
            is_current = sample.get("set_fingerprint") == current_fingerprint
            is_approved = sample.get("approval_status") == "approved"
            sample["freshness_status"] = "current" if is_current else "stale"
            sample["ready_for_full_song"] = bool(
                is_current
                and is_approved
                and sample.get("approved_set_fingerprint") == current_fingerprint
            )
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
            "samples": samples,
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
        phase_data = self._validated_editor_data(phase, payload.get("data", {}))
        saved = self.storage.save_project_phase_data(
            set_id,
            phase,
            phase_data,
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
        defaults = self._validated_editor_data(phase, payload.get("data", {}))
        saved = self.storage.initialize_project_phase_data(set_id, phase, defaults)
        if saved is None:
            raise ValueError("Set no encontrado.")
        return {"saved": saved, "project": self.get_project(set_id)}

    def _validated_editor_data(self, phase: str, data: object) -> dict[str, object]:
        phase_data = self._repair_text_encoding(dict(data or {}))
        if phase in {"intent", "music-plan"}:
            field = "intent" if phase == "intent" else "musicPlan"
            section = phase_data.get(field)
            if isinstance(section, dict) and "bpm" in section:
                section["bpm"] = validate_bpm(section["bpm"])
        return phase_data

    def _repair_text_encoding(self, value: object) -> object:
        if isinstance(value, dict):
            return {key: self._repair_text_encoding(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._repair_text_encoding(item) for item in value]
        if not isinstance(value, str):
            return value
        if not re.search(r"Ã.|Â.|â[€™“”€¦€]", value):
            return value
        try:
            repaired = value.encode("latin1").decode("utf-8")
        except UnicodeError:
            replacements = {
                "Ã¡": "á",
                "Ã©": "é",
                "Ã­": "í",
                "Ã³": "ó",
                "Ãº": "ú",
                "Ã±": "ñ",
                "Ã": "Á",
                "Ã‰": "É",
                "Ã": "Í",
                "Ã“": "Ó",
                "Ãš": "Ú",
                "Ã‘": "Ñ",
                "Â¿": "¿",
                "Â¡": "¡",
                "Â«": "«",
                "Â»": "»",
                "Âº": "º",
                "â€™": "'",
                "â€œ": '"',
                "â€": '"',
                "â€¦": "...",
            }
            repaired = value
            for broken, fixed in replacements.items():
                repaired = repaired.replace(broken, fixed)
        return repaired if repaired != value else value

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
        audio_task = self.model_orchestrator.active_audio_task()
        if audio_task is not None:
            return {"model": "Gemma", "mode": "sqlite_guidance", "status": "suspended_for_audio",
                    "message": "Hay un borrador de audio en curso. Puedes consultar su estado o cancelarlo; retomaremos la asistencia al terminar.",
                    "context_used": ["tasks SQLite"], "recommendations": ["Revisar el trabajo de audio activo"],
                    "readiness": {"missing": [], "recommendations": ["Esperar o cancelar el borrador"]}}
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
            else self._run_gemma_or_fallback(prompt, readiness, set_id=str(set_data["set_id"]))
        )
        phase_patch = self._phase_form_patch_from_question(question, str(payload.get("active_phase", "")), project)
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
                "phase_patch": phase_patch,
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
                "task_type": "gemma_to_technical_director_phase_patch" if phase_patch.get("available") else "gemma_to_technical_director_pipeline_review",
                "phase": "technical_review",
                "project_id": str(set_data["set_id"]),
                "project_name": str(set_data["project_name"]),
                "description": f"Gemma traduce la solicitud del usuario para revision tecnica interna: {question}",
                "question": question,
                "context": {
                    "active_phase": str(payload.get("active_phase", "")),
                    "phase_patch": phase_patch,
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
            "phase_patch": phase_patch,
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

    def transform_lyrics_section(self, payload: dict[str, object] | None = None) -> dict[str, object]:
        payload = payload or {}
        mode = str(payload.get("mode", "mejorar")).strip().lower()
        section_type = str(payload.get("section_type", "VERSO")).strip().upper()
        text = str(payload.get("text", "")).strip()
        if not text:
            raise ValueError("La seccion de letra no puede estar vacia.")
        if mode not in {"mejorar", "recrear", "expandir", "acortar", "variantes"}:
            raise ValueError("Modo de transformacion de letra no soportado.")

        project_context = {
            "project_name": str(payload.get("project_name", "")),
            "description": str(payload.get("description", "")),
            "lyrics": dict(payload.get("lyrics", {})) if isinstance(payload.get("lyrics"), dict) else {},
            "intent": dict(payload.get("intent", {})) if isinstance(payload.get("intent"), dict) else {},
        }
        prompt = self._build_lyrics_transform_prompt(mode, section_type, text, project_context)
        try:
            result = self.provider_registry.interpret_with_active_provider(prompt, "lyrics_section_transform")
            transformed = self._clean_lyrics_transform(str(result.get("summary", "")))
            mode_used = str(result.get("mode", "llama_cpp"))
            model = str(result.get("model", self.settings.local_models.interpreter_model if self.settings else "Gemma"))
            if not transformed:
                raise ValueError("Gemma respondio sin texto transformado.")
        except Exception as error:
            transformed = self._fallback_lyrics_transform(mode, text)
            mode_used = "local_fallback"
            model = "local-lyrics-transform"
            result = {"error": str(error)}

        handoff = self.model_orchestrator.run_handoff(
            {
                "model_role": "technical",
                "task_type": "lyrics_section_transform_review",
                "phase": "lyrics",
                "project_id": str(payload.get("set_id", "lyrics")),
                "project_name": str(project_context.get("project_name", "")) or "Lyrics",
                "description": f"Revision tecnica de transformacion lyrics: {mode}",
                "context": {
                    "mode": mode,
                    "section_type": section_type,
                    "original_words": len(text.split()),
                    "transformed_words": len(transformed.split()),
                    "provider_mode": mode_used,
                },
            }
        )
        return {
            "mode": mode_used,
            "model": model,
            "section_type": section_type,
            "transform": mode,
            "text": transformed,
            "original_text": text,
            "technical_handoff": handoff,
            "provider_result": result,
            "requires_user_save": True,
        }

    def _build_lyrics_transform_prompt(
        self,
        mode: str,
        section_type: str,
        text: str,
        project_context: dict[str, object],
    ) -> str:
        instructions = {
            "mejorar": "mejora claridad, musicalidad, imagenes y cantabilidad sin cambiar el sentido central",
            "recrear": "reescribe la seccion desde cero conservando la misma emocion e intencion",
            "expandir": "agrega 1 o 2 lineas cantables con imagen sensorial y continuidad emocional",
            "acortar": "reduce la seccion, conserva solo las lineas mas fuertes y cantables",
            "variantes": "crea dos variantes breves separadas por 'Variante B:'",
        }
        return (
            "Transforma una seccion de letra para Song AI.\n"
            f"Proyecto: {project_context.get('project_name', '')}\n"
            f"Descripcion: {project_context.get('description', '')}\n"
            f"Contexto lyrics: {project_context.get('lyrics', {})}\n"
            f"Contexto intent: {project_context.get('intent', {})}\n"
            f"Tipo de seccion: {section_type}\n"
            f"Accion: {instructions[mode]}.\n"
            "Reglas: responde solo con la nueva letra, sin markdown, sin explicaciones, sin comillas. "
            "Preserva idioma, intencion lirica y tono del proyecto activo.\n"
            "Texto actual:\n"
            f"{text}"
        )

    def _clean_lyrics_transform(self, text: str) -> str:
        cleaned = re.sub(r"```(?:text|markdown)?", "", text, flags=re.IGNORECASE).replace("```", "")
        cleaned = re.sub(r"^(respuesta|letra|texto transformado)\s*:\s*", "", cleaned.strip(), flags=re.IGNORECASE)
        lines = [line.rstrip() for line in cleaned.splitlines()]
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        return "\n".join(lines).strip()

    def _fallback_lyrics_transform(self, mode: str, text: str) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if mode == "acortar":
            return "\n".join(lines[: max(1, min(2, len(lines)))])
        if mode == "expandir":
            return f"{text.strip()}\nNueva mirada con la misma emocion central."
        if mode == "recrear":
            return "Duerme suave bajo el cielo,\nmi voz te cuida al respirar."
        if mode == "variantes":
            return f"Variante A:\n{text.strip()}\n\nVariante B:\nDuerme cerca de mi canto,\nla noche aprende a sonreir."
        return f"{text.strip()}\nMas claro, mas cantable, conservando la esencia."

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
                "Ayuda desde la idea del usuario y el contexto persistido. Si aun no existe un set, "
                "indica que se estan preparando las tres piezas obligatorias: instrumental, melodia vocal y letra. "
                "Antes de la cancion completa exige un set valido y un sample vigente de ese set, "
                "escuchado y aprobado por el usuario. Un sample mock no acredita produccion real. "
                "Indica la pieza o aprobacion pendiente y una accion concreta para continuar."
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
            "Antes de la cancion completa exige las tres piezas, un set valido y un sample vigente de ese set, "
            "escuchado y aprobado por el usuario. Un sample mock no acredita produccion real. "
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

    def _phase_form_patch_from_question(
        self,
        question: str,
        active_phase: str,
        project: dict[str, object] | None,
    ) -> dict[str, object]:
        phase = active_phase.strip()
        if phase not in {"intent", "lyrics", "music-plan", "midi", "instrumental", "voice"}:
            return {"available": False, "reason": "La fase activa no acepta parches conversacionales."}

        normalized = question.lower()
        wants_change = any(
            token in normalized
            for token in (
                "ajusta",
                "ajuste",
                "cambia",
                "cambio",
                "modifica",
                "modificar",
                "pon",
                "haz",
                "sube",
                "baja",
                "aumenta",
                "reduce",
                "mas ",
                "más ",
                "menos ",
            )
        )
        if not wants_change:
            return {"available": False, "reason": "La pregunta no solicita cambios directos al formulario."}

        changes: dict[str, object] = {}
        bpm_match = re.search(r"\b(4[8-9]|[5-9][0-9]|1[0-9]{2}|2[0-3][0-9]|240)\s*bpm\b", normalized)
        requested_bpm = int(bpm_match.group(1)) if bpm_match else None

        if phase == "intent":
            if requested_bpm:
                changes["bpm"] = requested_bpm
            if any(token in normalized for token in ("mas energia", "más energia", "mas energ", "más energ", "sube la energia")):
                changes["energy"] = 58
            if any(token in normalized for token in ("menos energia", "baja la energia", "suave", "calma", "tranquila")):
                changes["energy"] = 22
                changes["warmth"] = 86
            if "cinematic" in normalized or "cinematograf" in normalized:
                changes["cinematic"] = 72
            if "intima" in normalized or "íntima" in normalized or "cercana" in normalized:
                changes["warmth"] = 90
                changes["energy"] = min(int(changes.get("energy", 32)), 32)
            if "femenina" in normalized:
                changes["vocalType"] = "femenina"
            if "masculina" in normalized:
                changes["vocalType"] = "masculina"

        if phase == "lyrics":
            if "tierna" in normalized or "tierno" in normalized:
                changes["tone"] = "tender"
            if "poet" in normalized:
                changes["tone"] = "poetic"
            if "intima" in normalized or "íntima" in normalized or "cercana" in normalized:
                changes["tone"] = "intimate"
            if "cuna" in normalized or "infantil" in normalized:
                changes["theme"] = "cancion de cuna protectora"
            if "coro" in normalized or "estructura" in normalized:
                changes["structure"] = "intro, verse 1, chorus, verse 2, bridge, final chorus, outro"

        if phase == "music-plan":
            if requested_bpm:
                changes["bpm"] = requested_bpm
            if "cinematic" in normalized or "cinematograf" in normalized:
                changes["dynamicArc"] = "crece suavemente hacia un coro final cinematografico"
                changes["transition"] = "crescendo"
            if "suave" in normalized or "calma" in normalized or "tranquila" in normalized:
                changes["dynamicArc"] = "mantiene una energia baja con crecimiento muy gradual"
                changes["transition"] = "ambient bridge"
            if "piano" in normalized:
                changes["instrumentationNotes"] = "Piano calido al frente, acompanado por pads suaves y detalles ligeros."

        if phase == "midi":
            if "humana" in normalized or "natural" in normalized:
                changes["humanization"] = 34
                changes["velocity"] = 58
            if "suave" in normalized or "menos fuerte" in normalized or "baja" in normalized:
                changes["velocity"] = 48
            if "swing" in normalized:
                changes["swing"] = 14

        if phase == "instrumental":
            if "intima" in normalized or "íntima" in normalized or "cercana" in normalized:
                changes["texture"] = "intima, respirada y cercana"
                changes["depth"] = 52
                changes["brightness"] = 32
            if "cinematic" in normalized or "cinematograf" in normalized:
                changes["ambience"] = "cinematografico intimo"
                changes["depth"] = 72
                changes["stereoWidth"] = 66
            if "suave" in normalized or "calma" in normalized:
                changes["texture"] = "suave y envolvente"
                changes["movement"] = 34

        if phase == "voice":
            if "intima" in normalized or "íntima" in normalized or "cercana" in normalized:
                changes["emotion"] = "intima"
                changes["performance"] = "suave, cercana y contenida"
                changes["humanization"] = 58
                changes["vibrato"] = 12
            if "tierna" in normalized or "tierno" in normalized:
                changes["emotion"] = "tierna"
                changes["performance"] = "cantada con ternura y respiracion suave"
            if "humana" in normalized or "natural" in normalized:
                changes["humanization"] = 66
                changes["breaths"] = 34
            if "menos energia" in normalized or "baja la energia" in normalized or "suave" in normalized:
                changes["performance"] = str(changes.get("performance", "suave y contenida"))
                changes["vibrato"] = min(int(changes.get("vibrato", 14)), 14)
            if "armonia" in normalized or "armonias" in normalized or "armonía" in normalized:
                changes["harmonies"] = True
            if "femenina" in normalized:
                changes["mainVoice"] = "femenina suave"
            if "masculina" in normalized:
                changes["mainVoice"] = "masculina suave"

        allowed_fields = {
            "intent": {"warmth", "energy", "nostalgia", "cinematic", "bpm", "key", "vocalType", "songType", "language", "recipient"},
            "lyrics": {"language", "tone", "theme", "structure", "placeholders"},
            "music-plan": {"bpm", "key", "timeSignature", "progression", "dynamicArc", "transition", "instrumentationNotes"},
            "midi": {"humanization", "velocity", "melodyDensity", "chordRhythm", "timingOffset", "swing"},
            "instrumental": {"texture", "ambience", "depth", "brightness", "movement", "stereoWidth"},
            "voice": {"mainVoice", "emotion", "performance", "pronunciation", "breaths", "humanization", "vibrato", "layerBlend", "harmonies", "conversion", "callResponse"},
        }
        changes = {key: value for key, value in changes.items() if key in allowed_fields[phase]}
        if not changes:
            return {"available": False, "reason": "No se detectaron campos seguros para ajustar en la fase activa."}

        project_name = ""
        if project:
            project_name = str(dict(project.get("project", {})).get("project_name", ""))
        return {
            "available": True,
            "phase": phase,
            "changes": changes,
            "reason": f"Ajuste conversacional validado para {phase}" + (f" en {project_name}" if project_name else ""),
            "requires_user_save": True,
            "source": "gemma_to_technical_director_phase_patch",
            "allowed_fields": sorted(allowed_fields[phase]),
        }

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

    def _run_gemma_or_fallback(self, prompt: str, readiness: dict[str, object], set_id: str = "") -> str:
        try:
            result = self.provider_registry.interpret_with_active_provider(prompt, "active_song_project")
            if result.get("engine_steering"):
                readiness["engine_steering"] = result["engine_steering"]
                if set_id:
                    self.storage.create_project_phase_event(
                        project_id=set_id, phase_name="ASSISTANT", event_type="ENGINE_STEERING_SUPPLIED",
                        source="SYSTEM", after={"engine_steering": result["engine_steering"], "provider_mode": result.get("mode")},
                        message="Contexto de capacidades ACE-Step suministrado al assistant; no acredita obediencia ni audio.",
                    )
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

    def create_sample(self, payload: dict[str, object] | None = None) -> dict[str, str]:
        set_id = str((payload or {}).get("set_id", "")).strip()
        path = self.sample_builder.create_for_set(set_id) if set_id else self.sample_builder.create_from_latest_set()
        return self.path_response(path)

    def approve_sample(self, set_id: str, sample_id: str, payload: dict[str, object] | None = None) -> dict[str, object]:
        values = payload or {}
        return self.storage.approve_sample(set_id, sample_id, listened=values.get("listened") is True,
                                           audio_sha256=str(values.get("audio_sha256", "")))

    def sample_audio_file(self, set_id: str, sample_id: str, audio_sha256: str) -> Path:
        sample = self.storage.legacy_song_repository.get_sample(sample_id)
        if sample is None or sample.get("set_id") != set_id:
            raise ValueError("El sample no pertenece al set activo.")
        evidence = self.storage.verify_sample_audio(sample)
        if audio_sha256 != evidence["sha256"]:
            raise ValueError("El audio solicitado cambio; recarga el proyecto antes de escucharlo.")
        return Path(str(sample["json_path"])).parent / str(evidence["relative_path"])

    def preview_ace_step_plan(self, song_id: str, payload: dict[str, object]) -> dict[str, object]:
        return PreviewAceStepPlan(self.storage, AceStepSourceAudio(self.storage.data_dir)).execute(song_id, payload.get("lyrics", ""))

    def edit_ace_step_configuration(self, song_id: str, payload: dict) -> dict:
        record = EditAceStepConfiguration(self.storage, AceStepSourceAudio(self.storage.data_dir)).execute(song_id, payload)
        self.professional_songs._write_song_spec_snapshot(song_id, record["json_spec"],
                                                        record["approved_by_qwen"], record["missing_fields"])
        self.storage.create_song_event(song_id=song_id, phase="SONG_SPEC_COLLECTION", status="pending", progress=0,
                                       message="Entradas ACE-Step guardadas; revisa y confirma la nueva ficha.",
                                       active_model="user", payload={"revision_id": record["revision"]["revision_id"]})
        return self.get_professional_specification(song_id)

    def _ace_plan_review(self):
        preview = PreviewAceStepPlan(self.storage, AceStepSourceAudio(self.storage.data_dir))
        return ReviewAceStepPlan(preview, AceStepPlanRepository(self.storage.db_path))

    def prepare_ace_step_plan(self, song_id: str, payload: dict) -> dict:
        item = self._ace_plan_review().prepare(song_id, payload.get("lyrics", ""))
        self._record_ace_plan(song_id, item, "Plan ACE-Step preparado para revision; no se ejecuto audio.")
        return item

    def latest_ace_step_plan(self, song_id: str) -> dict:
        if self.storage.get_song_project(song_id) is None:
            raise ValueError("Proyecto no encontrado.")
        return {"plan": self._ace_plan_review().latest(song_id)}

    def generate_ace_step_candidate(self, song_id: str, payload: dict, cancellation_check=None) -> dict:
        runner = AceStepCandidateRunner(self.professional_songs.full_song_service)
        return AceStepCandidateService(self.storage, self._ace_plan_review(), runner, inspect_sample_wav).execute(song_id, payload, cancellation_check=cancellation_check)

    def ace_candidate_audio_file(self, song_id: str, task_id: str, checksum: str) -> Path:
        task = self.ace_candidate_jobs.get(song_id, task_id)
        if task["status"] != "completed":
            raise ValueError("El borrador todavia no tiene audio disponible.")
        artifact = task.get("result", {}).get("artifact", {})
        if artifact.get("song_id") != song_id or artifact.get("type") != "ace_step_candidate_wav":
            raise ValueError("El audio no pertenece al borrador del proyecto activo.")
        path = Path(artifact["file_path"])
        expected = self.storage.data_dir / "projects" / song_id / "candidates" / artifact["artifact_id"]
        evidence = inspect_sample_wav(path, expected)
        recorded = artifact.get("metadata", {}).get("audio_evidence", {})
        if not checksum or checksum != recorded.get("sha256") or evidence != recorded:
            raise ValueError("El audio del borrador cambio; revisa o genera un nuevo candidato.")
        return path

    def approve_ace_step_plan(self, song_id: str, plan_id: str, payload: dict) -> dict:
        item = self._ace_plan_review().approve(song_id, plan_id, payload)
        self._record_ace_plan(song_id, item, "Plan y letra aprobados; generacion real y sample siguen pendientes.")
        return item

    def _record_ace_plan(self, song_id: str, item: dict, message: str):
        self.storage.write_json(self.storage.data_dir / "projects" / song_id / "ace_plan.json", item)
        self.storage.create_song_event(song_id=song_id, phase="SONG_SPEC_COLLECTION", status="pending", progress=0,
                                       message=message, active_model="user", payload={"plan_id": item["plan_id"],
                                       "plan_sha256": item["plan"]["plan_sha256"], "plan_status": item["status"]})

    def create_song(self, payload: dict[str, object] | None = None) -> dict[str, str]:
        values = payload or {}
        set_id = str(values.get("set_id", "")).strip()
        sample_id = str(values.get("sample_id", "")).strip() or None
        path = self.full_song_builder.create_for_set(set_id, sample_id) if set_id else self.full_song_builder.create_from_latest_sample()
        return self.path_response(path)

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
            server_available = bool(llama_cpp.get("available")) if role == "gemma" else bool(exists and not llama_cpp.get("missing_models"))
            status = "ready" if exists and server_available else "optional" if exists else "missing"
            detail = str(metadata.get("path") or llama_cpp.get("reason", "Modelo GGUF pendiente."))
            if exists and role == "gemma" and not bool(llama_cpp.get("available")):
                detail = f"{detail} | Servidor no disponible: {llama_cpp.get('error') or llama_cpp.get('reason', '')}"
            components.append(
                {
                    "id": f"llm_{role}",
                    "label": label,
                    "status": status,
                    "detail": detail,
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

    def generate_local_final_song(self, set_id: str | None = None) -> dict[str, object]:
        if self.local_song_pipeline is None:
            raise ValueError("No hay configuracion local para generar cancion final.")
        songs = self.storage.list_songs_for_set(set_id) if set_id else []
        latest_song = songs[0] if songs else self.storage.get_latest_song() if not set_id else None
        if latest_song is None:
            raise ValueError("No hay cancion completa para el set activo. Crea y aprueba su sample antes de continuar.")
        active_set_id = str(latest_song.get("set_id", ""))
        sample = self.storage.legacy_song_repository.get_sample(str(latest_song.get("sample_id", "")))
        current_fingerprint = self.storage.set_generation_fingerprint(active_set_id)
        if (
            sample is None
            or sample.get("approval_status") != "approved"
            or sample.get("approved_set_fingerprint") != current_fingerprint
        ):
            raise ValueError("El sample de la cancion esta ausente o desactualizado. Regeneralo y apruebalo.")
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
        return self.audio_downloads.latest_file(extension)

    def project_audio_export_file(self, set_id: str, extension: str = "mp3") -> tuple[Path, str]:
        return self.audio_downloads.project_file(set_id, extension)

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
