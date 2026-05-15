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
            message="Proyecto creado. Gemma debe conversar con el usuario y Qwen validara la especificacion.",
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
