from __future__ import annotations

from pathlib import Path
import json
import sqlite3
from uuid import uuid4

from models.song_workflow import PHASE_SEQUENCE, SongPhase, SongPhaseStatus, SongProject, utc_now


class SongWorkflowRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.ensure_schema()

    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS song_projects (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    current_phase TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS song_specs (
                    song_id TEXT PRIMARY KEY,
                    json_spec TEXT NOT NULL,
                    approved_by_qwen INTEGER NOT NULL,
                    missing_fields_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(song_id) REFERENCES song_projects(id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS song_artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    song_id TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(song_id) REFERENCES song_projects(id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS song_events (
                    event_id TEXT PRIMARY KEY,
                    song_id TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    active_model TEXT NOT NULL,
                    artifact_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(song_id) REFERENCES song_projects(id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS model_executions (
                    execution_id TEXT PRIMARY KEY,
                    song_id TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL,
                    memory_strategy TEXT NOT NULL,
                    status TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    FOREIGN KEY(song_id) REFERENCES song_projects(id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS resource_snapshots (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    ram_total_mb REAL NOT NULL,
                    ram_available_mb REAL NOT NULL,
                    ram_used_percent REAL NOT NULL,
                    swap_total_mb REAL NOT NULL DEFAULT 0,
                    swap_free_mb REAL NOT NULL DEFAULT 0,
                    docker_memory_limit_mb REAL NOT NULL DEFAULT 0,
                    cpu_percent REAL NOT NULL,
                    disk_data_free_mb REAL NOT NULL,
                    disk_models_free_mb REAL NOT NULL,
                    disk_cache_free_mb REAL NOT NULL,
                    heavy_processes_json TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    message TEXT NOT NULL
                )
                """
            )
            self._ensure_resource_snapshot_columns(connection)

    def _ensure_resource_snapshot_columns(self, connection: sqlite3.Connection) -> None:
        columns = {
            str(row[1])
            for row in connection.execute("PRAGMA table_info(resource_snapshots)").fetchall()
        }
        additions = {
            "swap_total_mb": "REAL NOT NULL DEFAULT 0",
            "swap_free_mb": "REAL NOT NULL DEFAULT 0",
            "docker_memory_limit_mb": "REAL NOT NULL DEFAULT 0",
        }
        for name, definition in additions.items():
            if name not in columns:
                connection.execute(f"ALTER TABLE resource_snapshots ADD COLUMN {name} {definition}")

    def create_project(self, project: SongProject) -> dict[str, object]:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO song_projects (id, title, user_id, status, current_phase, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project.id,
                    project.title,
                    project.user_id,
                    project.status,
                    project.current_phase,
                    project.created_at,
                    project.updated_at,
                ),
            )
        self.create_event(
            song_id=project.id,
            phase=SongPhase.SONG_SPEC_COLLECTION.value,
            status=SongPhaseStatus.WAITING_USER_INPUT.value,
            progress=0,
            message="Proyecto creado. Gemma debe conversar con el usuario y el director tecnico validara la especificacion.",
            active_model="gemma",
            payload={"title": project.title, "phase_count": len(PHASE_SEQUENCE)},
        )
        return self.get_project(project.id) or {}

    def list_projects(self) -> list[dict[str, object]]:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT id, title, user_id, status, current_phase, created_at, updated_at
                FROM song_projects
                ORDER BY updated_at DESC
                """
            ).fetchall()
        return [self.project_row_to_dict(row) for row in rows]

    def get_project(self, song_id: str) -> dict[str, object] | None:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                SELECT id, title, user_id, status, current_phase, created_at, updated_at
                FROM song_projects
                WHERE id = ?
                """,
                (song_id,),
            ).fetchone()
        if row is None:
            return None
        project = self.project_row_to_dict(row)
        project["spec"] = self.get_spec(song_id)
        project["artifacts"] = self.list_artifacts(song_id)
        project["events"] = self.list_events(song_id)
        return project

    def update_project_phase(self, song_id: str, phase: str, status: str) -> dict[str, object]:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                UPDATE song_projects
                SET current_phase = ?, status = ?, updated_at = ?
                WHERE id = ?
                """,
                (phase, status, utc_now(), song_id),
            )
        return self.get_project(song_id) or {}

    def create_artifact(
        self,
        artifact_id: str,
        song_id: str,
        phase: str,
        artifact_type: str,
        file_path: str,
        metadata: dict[str, object],
    ) -> dict[str, object]:
        created_at = utc_now()
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO song_artifacts (
                    artifact_id, song_id, phase, type, file_path, metadata_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(artifact_id) DO UPDATE SET
                    file_path = excluded.file_path,
                    metadata_json = excluded.metadata_json
                """,
                (
                    artifact_id,
                    song_id,
                    phase,
                    artifact_type,
                    file_path,
                    json.dumps(metadata, ensure_ascii=False),
                    created_at,
                ),
            )
        return {
            "artifact_id": artifact_id,
            "song_id": song_id,
            "phase": phase,
            "type": artifact_type,
            "file_path": file_path,
            "metadata": metadata,
            "created_at": created_at,
        }

    def upsert_spec(
        self,
        song_id: str,
        json_spec: dict[str, object],
        approved_by_qwen: bool,
        missing_fields: list[str],
    ) -> dict[str, object]:
        now = utc_now()
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO song_specs (song_id, json_spec, approved_by_qwen, missing_fields_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(song_id) DO UPDATE SET
                    json_spec = excluded.json_spec,
                    approved_by_qwen = excluded.approved_by_qwen,
                    missing_fields_json = excluded.missing_fields_json,
                    updated_at = excluded.updated_at
                """,
                (
                    song_id,
                    json.dumps(json_spec, ensure_ascii=False),
                    1 if approved_by_qwen else 0,
                    json.dumps(missing_fields, ensure_ascii=False),
                    now,
                    now,
                ),
            )
        return self.get_spec(song_id) or {}

    def get_spec(self, song_id: str) -> dict[str, object] | None:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                SELECT song_id, json_spec, approved_by_qwen, missing_fields_json, created_at, updated_at
                FROM song_specs
                WHERE song_id = ?
                """,
                (song_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "song_id": str(row["song_id"]),
            "json_spec": json.loads(str(row["json_spec"])),
            "approved_by_qwen": bool(row["approved_by_qwen"]),
            "missing_fields": json.loads(str(row["missing_fields_json"])),
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
        }

    def create_event(
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
        event_id = f"event_{uuid4().hex[:12]}"
        created_at = utc_now()
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO song_events (
                    event_id, song_id, phase, status, progress, message,
                    active_model, artifact_id, payload_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    song_id,
                    phase,
                    status,
                    progress,
                    message,
                    active_model,
                    artifact_id,
                    json.dumps(payload or {}, ensure_ascii=False),
                    created_at,
                ),
            )
        return {
            "event_id": event_id,
            "song_id": song_id,
            "phase": phase,
            "status": status,
            "progress": progress,
            "message": message,
            "active_model": active_model,
            "artifact_id": artifact_id,
            "payload": payload or {},
            "created_at": created_at,
        }

    def list_events(self, song_id: str) -> list[dict[str, object]]:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT event_id, song_id, phase, status, progress, message, active_model, artifact_id, payload_json, created_at
                FROM song_events
                WHERE song_id = ?
                ORDER BY created_at ASC
                """,
                (song_id,),
            ).fetchall()
        return [self.event_row_to_dict(row) for row in rows]

    def list_artifacts(self, song_id: str) -> list[dict[str, object]]:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT artifact_id, song_id, phase, type, file_path, metadata_json, created_at
                FROM song_artifacts
                WHERE song_id = ?
                ORDER BY created_at ASC
                """,
                (song_id,),
            ).fetchall()
        return [self.artifact_row_to_dict(row) for row in rows]

    def create_resource_snapshot(
        self,
        snapshot_id: str,
        phase: str,
        ram_total_mb: float,
        ram_available_mb: float,
        ram_used_percent: float,
        swap_total_mb: float,
        swap_free_mb: float,
        docker_memory_limit_mb: float,
        cpu_percent: float,
        disk_data_free_mb: float,
        disk_models_free_mb: float,
        disk_cache_free_mb: float,
        heavy_processes: list[dict[str, object]],
        decision: str,
        message: str,
    ) -> dict[str, object]:
        created_at = utc_now()
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO resource_snapshots (
                    id, created_at, phase, ram_total_mb, ram_available_mb,
                    ram_used_percent, swap_total_mb, swap_free_mb,
                    docker_memory_limit_mb, cpu_percent, disk_data_free_mb,
                    disk_models_free_mb, disk_cache_free_mb, heavy_processes_json,
                    decision, message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    created_at,
                    phase,
                    ram_total_mb,
                    ram_available_mb,
                    ram_used_percent,
                    swap_total_mb,
                    swap_free_mb,
                    docker_memory_limit_mb,
                    cpu_percent,
                    disk_data_free_mb,
                    disk_models_free_mb,
                    disk_cache_free_mb,
                    json.dumps(heavy_processes, ensure_ascii=False),
                    decision,
                    message,
                ),
            )
        return {
            "id": snapshot_id,
            "created_at": created_at,
            "phase": phase,
            "ram_total_mb": ram_total_mb,
            "ram_available_mb": ram_available_mb,
            "ram_used_percent": ram_used_percent,
            "swap_total_mb": swap_total_mb,
            "swap_free_mb": swap_free_mb,
            "docker_memory_limit_mb": docker_memory_limit_mb,
            "cpu_percent": cpu_percent,
            "disk_data_free_mb": disk_data_free_mb,
            "disk_models_free_mb": disk_models_free_mb,
            "disk_cache_free_mb": disk_cache_free_mb,
            "heavy_processes": heavy_processes,
            "decision": decision,
            "message": message,
        }

    def list_resource_snapshots(self, limit: int = 100) -> list[dict[str, object]]:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT id, created_at, phase, ram_total_mb, ram_available_mb,
                       ram_used_percent, swap_total_mb, swap_free_mb,
                       docker_memory_limit_mb, cpu_percent, disk_data_free_mb,
                       disk_models_free_mb, disk_cache_free_mb, heavy_processes_json,
                       decision, message
                FROM resource_snapshots
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self.resource_snapshot_row_to_dict(row) for row in rows]

    def project_row_to_dict(self, row: sqlite3.Row) -> dict[str, object]:
        return {
            "id": str(row["id"]),
            "title": str(row["title"]),
            "user_id": str(row["user_id"]),
            "status": str(row["status"]),
            "current_phase": str(row["current_phase"]),
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
        }

    def event_row_to_dict(self, row: sqlite3.Row) -> dict[str, object]:
        return {
            "event_id": str(row["event_id"]),
            "song_id": str(row["song_id"]),
            "phase": str(row["phase"]),
            "status": str(row["status"]),
            "progress": int(row["progress"]),
            "message": str(row["message"]),
            "active_model": str(row["active_model"]),
            "artifact_id": str(row["artifact_id"]),
            "payload": json.loads(str(row["payload_json"])),
            "created_at": str(row["created_at"]),
        }

    def artifact_row_to_dict(self, row: sqlite3.Row) -> dict[str, object]:
        return {
            "artifact_id": str(row["artifact_id"]),
            "song_id": str(row["song_id"]),
            "phase": str(row["phase"]),
            "type": str(row["type"]),
            "file_path": str(row["file_path"]),
            "metadata": json.loads(str(row["metadata_json"])),
            "created_at": str(row["created_at"]),
        }

    def resource_snapshot_row_to_dict(self, row: sqlite3.Row) -> dict[str, object]:
        return {
            "id": str(row["id"]),
            "created_at": str(row["created_at"]),
            "phase": str(row["phase"]),
            "ram_total_mb": float(row["ram_total_mb"]),
            "ram_available_mb": float(row["ram_available_mb"]),
            "ram_used_percent": float(row["ram_used_percent"]),
            "swap_total_mb": float(row["swap_total_mb"]),
            "swap_free_mb": float(row["swap_free_mb"]),
            "docker_memory_limit_mb": float(row["docker_memory_limit_mb"]),
            "cpu_percent": float(row["cpu_percent"]),
            "disk_data_free_mb": float(row["disk_data_free_mb"]),
            "disk_models_free_mb": float(row["disk_models_free_mb"]),
            "disk_cache_free_mb": float(row["disk_cache_free_mb"]),
            "heavy_processes": json.loads(str(row["heavy_processes_json"])),
            "decision": str(row["decision"]),
            "message": str(row["message"]),
        }
