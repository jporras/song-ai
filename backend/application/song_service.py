from pathlib import Path
from typing import Any

from audio.mixer import AudioMixer
from application.model_orchestrator import ModelOrchestrator
from builders.export_builder import ExportBuilder
from builders.full_song_builder import FullSongBuilder
from builders.sample_builder import SampleBuilder
from builders.set_builder import SetBuilder
from builders.template_builder import TemplateBuilder
from core import creative_options as options
from core.storage import StorageManager
from explorers.mock_explorers import MockExplorerSuite
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
        self.template_builder = TemplateBuilder(storage)
        self.provider_registry = ProviderRegistry(
            settings.hf_models if settings else None,
            settings.local_models if settings else None,
        )
        self.model_orchestrator = ModelOrchestrator(storage, self.provider_registry)

    def bootstrap(self) -> None:
        self.storage.ensure_project_layout()

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
            "source_of_truth": "sqlite",
            "snapshot_files": {
                "set_json": song_set.get("json_path", ""),
                "instrumental_intent": instrumental.get("intent", {}),
                "melody_intent": melody.get("intent", {}),
                "lyrics_intent": lyrics.get("intent", {}),
            },
        }

    def gemma_assistant(self, payload: dict[str, object] | None = None) -> dict[str, object]:
        payload = payload or {}
        set_id = str(payload.get("set_id", "")).strip()
        project: dict[str, object] | None = None
        if set_id:
            project = self.get_project(set_id)
        else:
            sets = self.list_sets()
            if sets:
                project = self.get_project(str(sets[0]["set_id"]))

        if project is None:
            return {
                "model": "Gemma 4 E4B IT GGUF",
                "mode": "mock_until_llama_cpp_is_connected",
                "status": "needs_project",
                "message": "Crea o carga un proyecto/set para que Gemma pueda asistir transversalmente.",
                "context_used": [],
                "recommendations": [
                    "Completa instrumental, melodia y letra.",
                    "Crea el set/proyecto antes de generar sample o cancion completa.",
                ],
            }

        set_data = dict(project["set"])
        assets = dict(project["assets"])
        question = str(payload.get("question", "Que sigue para terminar esta cancion?")).strip()
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
                    "set": set_data,
                },
            }
        )
        missing: list[str] = []
        if not project["samples"]:
            missing.append("sample/checkpoint")
        if not project["songs"]:
            missing.append("cancion completa")
        return {
            "model": "Gemma 4 E4B IT GGUF",
            "mode": "mock_until_llama_cpp_is_connected",
            "status": "active_project_loaded",
            "question": question,
            "project_name": set_data["project_name"],
            "set_id": set_data["set_id"],
            "message": (
                "Gemma esta actuando como asistente transversal del proyecto activo. "
                "Usa SQLite como fuente activa y lee set, intents, assets, samples, canciones y eventos."
            ),
            "context_used": [
                "project_name",
                "description",
                "instrumental intent",
                "vocal/melody intent",
                "lyrical intent",
                "selected assets",
                "set.json snapshot",
                "manifest.json",
                "intent.json",
            ],
            "recommendations": [
                "Mantener el arreglo suave: piano, caja musical, pads y cuerdas sin romper la intencion de cuna.",
                "Conservar voz cantada suave; no usar TTS hablado como reemplazo de canto.",
                "Revisar la letra editable antes del sample para mejorar metrica, rima y narrativa.",
                "Avanzar en orden: set valido, sample, cancion completa, mezcla, WAV/MP3.",
            ],
            "missing_before_final": missing,
            "handoff": handoff,
        }

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
                    "Para crear un set y avanzar a sample/cancion completa debe existir "
                    "al menos un draft de instrumental, melodia y letra."
                ),
                "summary": (
                    f"Proyecto '{song_set.get('project_name', song_set['set_id'])}' compuesto por instrumental "
                    f"{song_set['instrumental_id']}, melodia {song_set['melody_id']} "
                    f"y letra {song_set['lyrics_id']}."
                ),
                "compatibility_status": compatibility.get("status", "unknown"),
                "next_suggestion": "El set ya tiene instrumental, melodia y letra. Genera un sample como checkpoint y luego produce la cancion completa con soundtrack, voz cantada, mezcla y exports.",
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

    def save_template(self) -> dict[str, str]:
        return self.path_response(self.template_builder.save_latest_set_template())

    def path_response(self, path: Path) -> dict[str, str]:
        return {"path": str(path), "id": path.name}
