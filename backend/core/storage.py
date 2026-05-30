from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

from adapters.sqlite.json_config_repository import JsonConfigRepository
from adapters.sqlite.orchestration_repository import OrchestrationRepository
from adapters.sqlite.set_repository import SetRepository
from adapters.sqlite.song_workflow_repository import SongWorkflowRepository
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
        "projects",
        "templates",
    )

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.db_path = self.data_dir / "song_ai.sqlite"
        self.json_config_repository = JsonConfigRepository(self.db_path)
        self.set_repository = SetRepository(self.db_path)
        self.orchestration_repository = OrchestrationRepository(self.db_path)
        self.song_workflow_repository = SongWorkflowRepository(self.db_path)

    def ensure_project_layout(self) -> list[Path]:
        created_or_existing: list[Path] = []
        for relative_folder in self.DATA_FOLDERS:
            folder = self.data_dir / relative_folder
            existed = folder.exists()
            folder.mkdir(parents=True, exist_ok=True)
            if not existed:
                created_or_existing.append(folder)
        self.sync_legacy_sets_to_sqlite()
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

    def get_asset_draft_detail(self, asset_id: str) -> dict[str, object]:
        draft = self.find_asset_draft(asset_id)
        if draft is None:
            raise ValueError("Asset no encontrado.")

        draft_dir = Path(draft["path"])
        detail: dict[str, object] = {**draft}
        for name in ("manifest.json", "intent.json", "metadata.json"):
            path = draft_dir / name
            if path.exists():
                detail[name.replace(".json", "")] = self.read_json(path)

        asset_type = str(draft["asset_type"])
        content_file = {
            AssetType.INSTRUMENTAL.value: "instrumental.txt",
            AssetType.MELODY.value: "melody.txt",
            AssetType.LYRICS.value: "lyrics.md",
        }.get(asset_type)
        if content_file:
            path = draft_dir / content_file
            if path.exists():
                detail["content_path"] = str(path)
                detail["content"] = path.read_text(encoding="utf-8")
        return detail

    def list_asset_drafts_by_type(self, asset_type: AssetType) -> list[dict[str, str]]:
        return [draft for draft in self.list_asset_drafts() if draft["asset_type"] == asset_type.value]

    def get_lyrics_markdown(self, asset_id: str) -> dict[str, str]:
        draft = self.find_asset_draft(asset_id)
        if draft is None or draft["asset_type"] != AssetType.LYRICS.value:
            raise ValueError("Letra no encontrada.")

        lyrics_path = Path(draft["path"]) / "lyrics.md"
        if not lyrics_path.exists():
            raise ValueError("El draft de letra no tiene lyrics.md.")

        return {
            "asset_id": asset_id,
            "path": str(lyrics_path),
            "content": lyrics_path.read_text(encoding="utf-8"),
        }

    def update_lyrics_markdown(self, asset_id: str, content: str) -> dict[str, str]:
        draft = self.find_asset_draft(asset_id)
        if draft is None or draft["asset_type"] != AssetType.LYRICS.value:
            raise ValueError("Letra no encontrada.")
        if not content.strip():
            raise ValueError("La letra no puede quedar vacia.")

        lyrics_path = Path(draft["path"]) / "lyrics.md"
        lyrics_path.write_text(content.rstrip() + "\n", encoding="utf-8")
        return {
            "asset_id": asset_id,
            "path": str(lyrics_path),
            "content": lyrics_path.read_text(encoding="utf-8"),
        }

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

    def sync_legacy_sets_to_sqlite(self) -> dict[str, object]:
        synced: list[str] = []
        skipped: list[str] = []
        for song_set in self.list_song_sets():
            set_id = song_set["set_id"]
            if self.set_repository.get_set(set_id) is not None:
                skipped.append(set_id)
                continue

            set_path = Path(song_set["path"]) / "set.json"
            payload = self.read_json(set_path)
            song_set_model = SongSet.from_dict(
                {
                    **payload,
                    "project_name": payload.get("project_name") or set_id,
                    "description": payload.get("description") or "Proyecto migrado desde snapshot set.json.",
                    "created_at": payload.get("created_at") or datetime.fromtimestamp(
                        set_path.stat().st_mtime,
                        timezone.utc,
                    ).isoformat(),
                }
            )
            self.set_repository.save_set(song_set_model, set_path)
            synced.append(set_id)

        return {
            "synced_count": len(synced),
            "skipped_count": len(skipped),
            "synced": synced,
            "skipped": skipped,
        }

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

    def list_samples_for_set(self, set_id: str) -> list[dict[str, object]]:
        samples: list[dict[str, object]] = []
        for sample in self.list_samples():
            payload = self.read_json(Path(sample["path"]) / "sample.json")
            if str(payload.get("set_id", "")) == set_id:
                payload["path"] = sample["path"]
                samples.append(payload)
        return samples

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

    def list_songs_for_set(self, set_id: str) -> list[dict[str, object]]:
        songs: list[dict[str, object]] = []
        for song in self.list_songs():
            payload = self.read_json(Path(song["path"]) / "song.json")
            if str(payload.get("set_id", "")) == set_id:
                payload["path"] = song["path"]
                songs.append(payload)
        return songs

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

    def update_indexed_set_description(self, set_id: str, description: str) -> dict[str, object] | None:
        updated = self.set_repository.update_description(set_id, description)
        if updated is None:
            return None
        export_path = Path(str(updated.get("json_path") or self.data_dir / "sets" / set_id / "set.json"))
        if not export_path.is_absolute():
            export_path = self.data_dir / "sets" / set_id / "set.json"
        self.write_json(export_path, self.serialize_indexed_set(updated))
        return updated

    def save_project_phase_data(
        self,
        set_id: str,
        phase: str,
        data: dict[str, object],
        status: str,
        phase_status: str = "COMPLETED",
        change_source: str = "USER",
        validation_status: str = "valid",
    ) -> dict[str, object] | None:
        saved = self.set_repository.save_phase_data(
            set_id=set_id,
            phase=phase,
            data=data,
            status=status,
            phase_status=phase_status,
            change_source=change_source,
            validation_status=validation_status,
        )
        if saved is None:
            return None
        phase_dir = self.data_dir / "sets" / set_id / "phase_data"
        self.write_json(phase_dir / f"{phase}.json", dict(saved))
        return saved

    def initialize_project_phase_data(self, set_id: str, phase: str, defaults: dict[str, object] | None = None) -> dict[str, object] | None:
        return self.set_repository.initialize_phase_data(set_id, phase, defaults)

    def list_project_phase_data(self, set_id: str) -> dict[str, object]:
        return self.set_repository.list_phase_data(set_id)

    def list_project_phase_events(self, set_id: str) -> list[dict[str, object]]:
        return self.set_repository.list_phase_events(set_id)

    def create_project_phase_event(
        self,
        project_id: str,
        phase_name: str,
        event_type: str,
        source: str,
        before: dict[str, object] | None = None,
        after: dict[str, object] | None = None,
        message: str = "",
        error_code: str = "",
        error_message: str = "",
    ) -> dict[str, object]:
        return self.set_repository.create_phase_event(
            project_id=project_id,
            phase_name=phase_name,
            event_type=event_type,
            source=source,
            before=before,
            after=after,
            message=message,
            error_code=error_code,
            error_message=error_message,
        )

    def save_project_ui_state(self, set_id: str, last_active_phase: str) -> dict[str, object] | None:
        return self.set_repository.save_ui_state(set_id, last_active_phase)

    def get_project_ui_state(self, set_id: str) -> dict[str, object]:
        return self.set_repository.get_ui_state(set_id)

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

    def create_song_project(self, title: str, user_id: str = "local-user") -> dict[str, object]:
        from models.song_workflow import SongProject

        return self.song_workflow_repository.create_project(SongProject.create(title=title, user_id=user_id))

    def list_song_projects(self) -> list[dict[str, object]]:
        return self.song_workflow_repository.list_projects()

    def get_song_project(self, song_id: str) -> dict[str, object] | None:
        return self.song_workflow_repository.get_project(song_id)

    def list_song_project_events(self, song_id: str) -> list[dict[str, object]]:
        return self.song_workflow_repository.list_events(song_id)

    def update_song_project_phase(self, song_id: str, phase: str, status: str) -> dict[str, object]:
        return self.song_workflow_repository.update_project_phase(song_id, phase, status)

    def upsert_song_spec(
        self,
        song_id: str,
        json_spec: dict[str, object],
        approved_by_qwen: bool,
        missing_fields: list[str],
    ) -> dict[str, object]:
        return self.song_workflow_repository.upsert_spec(song_id, json_spec, approved_by_qwen, missing_fields)

    def create_song_event(
        self,
        song_id: str,
        phase: str,
        status: str,
        progress: int,
        message: str,
        active_model: str,
        payload: dict[str, object] | None = None,
        artifact_id: str = "",
    ) -> dict[str, object]:
        return self.song_workflow_repository.create_event(
            song_id=song_id,
            phase=phase,
            status=status,
            progress=progress,
            message=message,
            active_model=active_model,
            payload=payload,
            artifact_id=artifact_id,
        )

    def create_song_artifact(
        self,
        artifact_id: str,
        song_id: str,
        phase: str,
        artifact_type: str,
        file_path: str,
        metadata: dict[str, object],
    ) -> dict[str, object]:
        path = Path(file_path)
        file_size = path.stat().st_size if path.exists() else 0
        checksum = self.file_checksum(path) if path.exists() and path.is_file() else ""
        enriched_metadata = {
            "artifact_status": "GENERATED" if path.exists() else "MISSING",
            "file_size": file_size,
            "checksum": checksum,
            **metadata,
        }
        artifact = self.song_workflow_repository.create_artifact(
            artifact_id=artifact_id,
            song_id=song_id,
            phase=phase,
            artifact_type=artifact_type,
            file_path=file_path,
            metadata=enriched_metadata,
        )
        self.create_song_event(
            song_id=song_id,
            phase=phase,
            status="completed" if path.exists() else "failed",
            progress=100 if path.exists() else 0,
            message=f"Artefacto {artifact_type} {'generado' if path.exists() else 'faltante'}: {file_path}",
            active_model="artifact-registry",
            payload={
                "event_type": "ARTIFACT_GENERATED" if path.exists() else "ARTIFACT_MISSING",
                "artifact_type": artifact_type,
                "file_path": file_path,
                "file_size": file_size,
                "checksum": checksum,
            },
            artifact_id=artifact_id,
        )
        return artifact

    def file_checksum(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def verify_song_artifact(self, song_id: str, artifact_type: str) -> dict[str, object]:
        project = self.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        matches = [dict(item) for item in list(project.get("artifacts", [])) if str(item.get("type")) == artifact_type]
        if not matches:
            return {"artifact_type": artifact_type, "artifact_status": "NOT_GENERATED", "message": "Artefacto no registrado en SQLite."}
        artifact = matches[-1]
        path = Path(str(artifact["file_path"]))
        metadata = dict(artifact.get("metadata", {}))
        if not path.exists():
            status = "MISSING"
            event_type = "ARTIFACT_MISSING"
            message = "El archivo registrado no existe en disco."
        else:
            checksum = self.file_checksum(path)
            expected = str(metadata.get("checksum", ""))
            if expected and checksum != expected:
                status = "CORRUPTED"
                event_type = "ARTIFACT_CORRUPTED"
                message = "El checksum del archivo no coincide con SQLite."
            else:
                status = "GENERATED"
                event_type = "ARTIFACT_GENERATED"
                message = "Artefacto verificado correctamente."
            metadata["file_size"] = path.stat().st_size
            metadata["checksum"] = checksum
        metadata["artifact_status"] = status
        self.song_workflow_repository.update_artifact_metadata(str(artifact["artifact_id"]), metadata)
        if status != "GENERATED":
            self.create_song_event(
                song_id=song_id,
                phase=str(artifact["phase"]),
                status="failed",
                progress=0,
                message=message,
                active_model="artifact-verifier",
                payload={"event_type": event_type, "artifact_type": artifact_type, "artifact_status": status},
                artifact_id=str(artifact["artifact_id"]),
            )
        return {**artifact, "metadata": metadata, "artifact_status": status, "message": message}

    def create_resource_snapshot(self, snapshot: dict[str, object]) -> dict[str, object]:
        return self.song_workflow_repository.create_resource_snapshot(
            snapshot_id=str(snapshot["id"]),
            phase=str(snapshot["phase"]),
            ram_total_mb=float(snapshot["ram_total_mb"]),
            ram_available_mb=float(snapshot["ram_available_mb"]),
            ram_used_percent=float(snapshot["ram_used_percent"]),
            swap_total_mb=float(snapshot.get("swap_total_mb", 0)),
            swap_free_mb=float(snapshot.get("swap_free_mb", 0)),
            swap_used_mb=float(snapshot.get("swap_used_mb", 0)),
            visible_memory_limit_mb=float(
                snapshot.get("visible_memory_limit_mb", snapshot.get("docker_memory_limit_mb", 0))
            ),
            cpu_percent=float(snapshot["cpu_percent"]),
            vram=[dict(item) for item in list(snapshot.get("vram", []))],
            disk_data_free_mb=float(snapshot["disk_data_free_mb"]),
            disk_models_free_mb=float(snapshot["disk_models_free_mb"]),
            disk_cache_free_mb=float(snapshot["disk_cache_free_mb"]),
            heavy_processes=[dict(item) for item in list(snapshot.get("heavy_processes", []))],
            decision=str(snapshot.get("decision", "unknown")),
            message=str(snapshot.get("message", "")),
        )

    def list_resource_snapshots(self, limit: int = 100) -> list[dict[str, object]]:
        return self.song_workflow_repository.list_resource_snapshots(limit)

