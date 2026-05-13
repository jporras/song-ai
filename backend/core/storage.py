from pathlib import Path
import json

from adapters.sqlite.json_config_repository import JsonConfigRepository
from adapters.sqlite.orchestration_repository import OrchestrationRepository
from adapters.sqlite.set_repository import SetRepository
from models.assets import AssetDraft, AssetType
from models.song_set import SongSet


class StorageManager:
    DATA_FOLDERS = (
        "drafts/instrumentals",
        "drafts/melodies",
        "drafts/lyrics",
        "sets",
        "samples",
        "songs",
        "templates",
    )

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.db_path = self.data_dir / "song_ai.sqlite"
        self.json_config_repository = JsonConfigRepository(self.db_path)
        self.set_repository = SetRepository(self.db_path)
        self.orchestration_repository = OrchestrationRepository(self.db_path)

    def ensure_project_layout(self) -> list[Path]:
        created_or_existing: list[Path] = []
        for relative_folder in self.DATA_FOLDERS:
            folder = self.data_dir / relative_folder
            existed = folder.exists()
            folder.mkdir(parents=True, exist_ok=True)
            if not existed:
                created_or_existing.append(folder)
        return created_or_existing

    def list_data_folders(self) -> list[Path]:
        return [self.data_dir / relative_folder for relative_folder in self.DATA_FOLDERS]

    def save_asset_draft(self, draft: AssetDraft) -> Path:
        draft_dir = self.get_asset_draft_dir(draft.asset_type, draft.asset_id)
        draft_dir.mkdir(parents=True, exist_ok=True)

        self.write_json(draft_dir / "manifest.json", draft.manifest.to_dict())
        self.write_json(draft_dir / "intent.json", draft.intent.to_dict())
        self.write_json(
            draft_dir / "metadata.json",
            {
                "asset_id": draft.asset_id,
                "asset_type": draft.asset_type.value,
                "files": [str(file_path) for file_path in draft.files],
                "metadata": draft.metadata,
            },
        )
        return draft_dir

    def list_asset_drafts(self) -> list[dict[str, str]]:
        drafts: list[dict[str, str]] = []
        for asset_type in AssetType:
            parent = self.get_asset_parent_dir(asset_type)
            if not parent.exists():
                continue
            for draft_dir in sorted(path for path in parent.iterdir() if path.is_dir()):
                metadata_path = draft_dir / "metadata.json"
                if not metadata_path.exists():
                    continue
                metadata = self.read_json(metadata_path)
                drafts.append(
                    {
                        "asset_id": str(metadata.get("asset_id", draft_dir.name)),
                        "asset_type": str(metadata.get("asset_type", asset_type.value)),
                        "path": str(draft_dir),
                    }
                )
        return drafts

    def find_asset_draft(self, asset_id: str) -> dict[str, str] | None:
        for draft in self.list_asset_drafts():
            if draft["asset_id"] == asset_id:
                return draft
        return None

    def list_asset_drafts_by_type(self, asset_type: AssetType) -> list[dict[str, str]]:
        return [draft for draft in self.list_asset_drafts() if draft["asset_type"] == asset_type.value]

    def favorite_asset(self, asset_id: str) -> dict[str, str] | None:
        draft = self.find_asset_draft(asset_id)
        if draft is None:
            return None

        favorites = self.list_favorites()
        if not any(favorite["asset_id"] == asset_id for favorite in favorites):
            favorites.append({"asset_id": draft["asset_id"], "asset_type": draft["asset_type"]})
            self.write_json(self.data_dir / "favorites.json", {"favorites": favorites})
        return draft

    def list_favorites(self) -> list[dict[str, str]]:
        path = self.data_dir / "favorites.json"
        if not path.exists():
            return []
        payload = self.read_json(path)
        return [
            {"asset_id": str(item["asset_id"]), "asset_type": str(item["asset_type"])}
            for item in list(payload.get("favorites", []))
        ]

    def save_song_set(self, song_set: SongSet) -> Path:
        set_dir = self.data_dir / "sets" / song_set.set_id
        set_dir.mkdir(parents=True, exist_ok=True)
        set_path = set_dir / "set.json"
        self.write_json(set_path, song_set.to_dict())
        self.set_repository.save_set(song_set, set_path)
        return set_dir

    def list_song_sets(self) -> list[dict[str, str]]:
        sets_dir = self.data_dir / "sets"
        if not sets_dir.exists():
            return []
        song_sets: list[dict[str, str]] = []
        for set_dir in sorted(path for path in sets_dir.iterdir() if path.is_dir()):
            set_path = set_dir / "set.json"
            if not set_path.exists():
                continue
            payload = self.read_json(set_path)
            song_sets.append({"set_id": str(payload["set_id"]), "path": str(set_dir)})
        return song_sets

    def get_latest_song_set(self) -> dict[str, object] | None:
        song_sets = self.list_song_sets()
        if not song_sets:
            return None
        latest = song_sets[-1]
        payload = self.read_json(Path(latest["path"]) / "set.json")
        payload["path"] = latest["path"]
        return payload

    def list_samples(self) -> list[dict[str, str]]:
        samples_dir = self.data_dir / "samples"
        if not samples_dir.exists():
            return []
        samples: list[dict[str, str]] = []
        for sample_dir in sorted(path for path in samples_dir.iterdir() if path.is_dir()):
            sample_path = sample_dir / "sample.json"
            if not sample_path.exists():
                continue
            payload = self.read_json(sample_path)
            samples.append({"sample_id": str(payload["sample_id"]), "path": str(sample_dir)})
        return samples

    def get_latest_sample(self) -> dict[str, object] | None:
        samples = self.list_samples()
        if not samples:
            return None
        latest = samples[-1]
        payload = self.read_json(Path(latest["path"]) / "sample.json")
        payload["path"] = latest["path"]
        return payload

    def list_songs(self) -> list[dict[str, str]]:
        songs_dir = self.data_dir / "songs"
        if not songs_dir.exists():
            return []
        songs: list[dict[str, str]] = []
        for song_dir in sorted(path for path in songs_dir.iterdir() if path.is_dir()):
            song_path = song_dir / "song.json"
            if not song_path.exists():
                continue
            payload = self.read_json(song_path)
            songs.append({"song_id": str(payload["song_id"]), "path": str(song_dir)})
        return songs

    def get_latest_song(self) -> dict[str, object] | None:
        songs = self.list_songs()
        if not songs:
            return None
        latest = songs[-1]
        payload = self.read_json(Path(latest["path"]) / "song.json")
        payload["path"] = latest["path"]
        return payload

    def get_asset_draft_dir(self, asset_type: AssetType, asset_id: str) -> Path:
        return self.get_asset_parent_dir(asset_type) / asset_id

    def get_asset_parent_dir(self, asset_type: AssetType) -> Path:
        folder_name = {
            AssetType.INSTRUMENTAL: "instrumentals",
            AssetType.MELODY: "melodies",
            AssetType.LYRICS: "lyrics",
        }[asset_type]
        return self.data_dir / "drafts" / folder_name

    def write_json(self, path: Path, payload: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        self.json_config_repository.save_path(path)

    def read_json(self, path: Path) -> dict[str, object]:
        return json.loads(path.read_text(encoding="utf-8"))

    def list_json_config_paths(self) -> list[dict[str, str]]:
        return self.json_config_repository.list_paths()

    def list_indexed_sets(self) -> list[dict[str, object]]:
        return self.set_repository.list_sets()

    def get_indexed_set(self, set_id: str) -> dict[str, object] | None:
        return self.set_repository.get_set(set_id)

    def export_indexed_sets_to_json(self) -> dict[str, object]:
        exported_paths: list[str] = []
        for song_set in self.list_indexed_sets():
            set_id = str(song_set["set_id"])
            export_path = Path(str(song_set.get("json_path") or self.data_dir / "sets" / set_id / "set.json"))
            if not export_path.is_absolute():
                export_path = self.data_dir / "sets" / set_id / "set.json"
            self.write_json(export_path, self.serialize_indexed_set(song_set))
            exported_paths.append(str(export_path))
        return {
            "exported_count": len(exported_paths),
            "paths": exported_paths,
        }

    def serialize_indexed_set(self, song_set: dict[str, object]) -> dict[str, object]:
        return {
            "set_id": str(song_set["set_id"]),
            "project_name": str(song_set.get("project_name", song_set["set_id"])),
            "description": str(song_set.get("description", "")),
            "created_at": str(song_set.get("created_at", "")),
            "instrumental_id": str(song_set["instrumental_id"]),
            "melody_id": str(song_set["melody_id"]),
            "lyrics_id": str(song_set["lyrics_id"]),
            "compatibility_data": dict(song_set.get("compatibility_data", {})),
        }

    def create_task(
        self,
        task_id: str,
        task_type: str,
        model_role: str,
        payload: dict[str, object],
        message: str,
    ) -> dict[str, object]:
        return self.orchestration_repository.create_task(task_id, task_type, model_role, payload, message)

    def update_task(
        self,
        task_id: str,
        status: str,
        progress: int,
        message: str,
        result: dict[str, object] | None = None,
    ) -> dict[str, object]:
        return self.orchestration_repository.update_task(task_id, status, progress, message, result)

    def list_tasks(self) -> list[dict[str, object]]:
        return self.orchestration_repository.list_tasks()

    def create_model_run(
        self,
        run_id: str,
        task_id: str,
        model_role: str,
        provider_name: str,
        model_name: str,
        metadata: dict[str, object],
    ) -> dict[str, object]:
        return self.orchestration_repository.create_model_run(
            run_id,
            task_id,
            model_role,
            provider_name,
            model_name,
            metadata,
        )

    def complete_model_run(
        self,
        run_id: str,
        status: str,
        metadata: dict[str, object],
    ) -> dict[str, object]:
        return self.orchestration_repository.complete_model_run(run_id, status, metadata)

    def list_model_runs(self) -> list[dict[str, object]]:
        return self.orchestration_repository.list_model_runs()

    def create_project_event(
        self,
        event_id: str,
        project_id: str,
        project_name: str,
        phase: str,
        actor: str,
        model_role: str,
        provider_name: str,
        status: str,
        message: str,
        task_id: str,
        run_id: str,
        metadata: dict[str, object],
    ) -> dict[str, object]:
        return self.orchestration_repository.create_project_event(
            event_id,
            project_id,
            project_name,
            phase,
            actor,
            model_role,
            provider_name,
            status,
            message,
            task_id,
            run_id,
            metadata,
        )

    def list_project_events(self, project_id: str | None = None) -> list[dict[str, object]]:
        return self.orchestration_repository.list_project_events(project_id)

