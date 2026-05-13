from pathlib import Path

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
        self.provider_registry = ProviderRegistry(settings.hf_models if settings else None)
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
            description = "Proyecto creado con los primeros drafts disponibles."
        return self.path_response(
            self.set_builder.create_first_valid_set(
                project_name=project_name,
                description=description,
            )
        )

    def list_sets(self) -> list[dict[str, object]]:
        return [self.describe_set(song_set) for song_set in self.storage.list_indexed_sets()]

    def get_set(self, set_id: str) -> dict[str, object]:
        song_set = self.storage.get_indexed_set(set_id)
        if song_set is None:
            raise ValueError("Set no encontrado.")
        return self.describe_set(song_set)

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
                "next_suggestion": "El set ya tiene los puntos 1, 2 y 3 completos. Generar sample si aun no existe; si existe, pasar a cancion completa.",
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

    def save_template(self) -> dict[str, str]:
        return self.path_response(self.template_builder.save_latest_set_template())

    def path_response(self, path: Path) -> dict[str, str]:
        return {"path": str(path), "id": path.name}
