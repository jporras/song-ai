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

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=30)
        connection.execute("PRAGMA busy_timeout = 30000")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def ensure_schema(self) -> None:
        with self._connect() as connection:
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
                CREATE TABLE IF NOT EXISTS song_spec_revisions (
                    revision_id TEXT PRIMARY KEY,
                    song_id TEXT NOT NULL,
                    revision_number INTEGER NOT NULL,
                    schema_version TEXT NOT NULL,
                    json_spec TEXT NOT NULL,
                    compilation_status TEXT NOT NULL,
                    deterministic_valid INTEGER NOT NULL,
                    technical_review_mode TEXT NOT NULL,
                    user_confirmation_status TEXT NOT NULL,
                    missing_fields_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(song_id, revision_number),
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
                CREATE TABLE IF NOT EXISTS project_artifacts (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    phase_name TEXT NOT NULL,
                    artifact_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER NOT NULL DEFAULT 0,
                    checksum TEXT NOT NULL DEFAULT '',
                    generation_params_json TEXT NOT NULL DEFAULT '{}',
                    source_phase_snapshot_json TEXT NOT NULL DEFAULT '{}',
                    provider_name TEXT NOT NULL DEFAULT '',
                    provider_version TEXT NOT NULL DEFAULT '',
                    seed TEXT NOT NULL DEFAULT '',
                    error_code TEXT NOT NULL DEFAULT '',
                    error_message TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_verified_at TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY(project_id) REFERENCES song_projects(id)
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
                    swap_used_mb REAL NOT NULL DEFAULT 0,
                    visible_memory_limit_mb REAL NOT NULL DEFAULT 0,
                    cpu_percent REAL NOT NULL,
                    vram_json TEXT NOT NULL DEFAULT '[]',
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
            "swap_used_mb": "REAL NOT NULL DEFAULT 0",
            "visible_memory_limit_mb": "REAL NOT NULL DEFAULT 0",
            "vram_json": "TEXT NOT NULL DEFAULT '[]'",
        }
        for name, definition in additions.items():
            if name not in columns:
                connection.execute(f"ALTER TABLE resource_snapshots ADD COLUMN {name} {definition}")
        if "visible_memory_limit_mb" in additions and "docker_memory_limit_mb" in columns:
            connection.execute(
                """
                UPDATE resource_snapshots
                SET visible_memory_limit_mb = docker_memory_limit_mb
                WHERE visible_memory_limit_mb = 0 AND docker_memory_limit_mb > 0
                """
            )

    def create_project(self, project: SongProject) -> dict[str, object]:
        with self._connect() as connection:
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
        with self._connect() as connection:
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
        with self._connect() as connection:
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

    def list_projects_by_user_id(self, user_id: str) -> list[dict[str, object]]:
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT id, title, user_id, status, current_phase, created_at, updated_at
                FROM song_projects
                WHERE user_id = ?
                ORDER BY updated_at DESC
                """,
                (user_id,),
            ).fetchall()
        return [self.project_row_to_dict(row) for row in rows]

    def delete_project(self, song_id: str) -> bool:
        with self._connect() as connection:
            existing = connection.execute("SELECT id FROM song_projects WHERE id = ?", (song_id,)).fetchone()
            if existing is None:
                return False
            connection.execute("DELETE FROM model_executions WHERE song_id = ?", (song_id,))
            connection.execute("DELETE FROM song_events WHERE song_id = ?", (song_id,))
            connection.execute("DELETE FROM project_artifacts WHERE project_id = ?", (song_id,))
            connection.execute("DELETE FROM song_artifacts WHERE song_id = ?", (song_id,))
            connection.execute("DELETE FROM song_specs WHERE song_id = ?", (song_id,))
            connection.execute("DELETE FROM song_spec_revisions WHERE song_id = ?", (song_id,))
            if connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='ace_step_plans'").fetchone():
                connection.execute("DELETE FROM ace_step_plans WHERE song_id = ?", (song_id,))
            connection.execute("DELETE FROM song_projects WHERE id = ?", (song_id,))
        return True

    def update_project_phase(self, song_id: str, phase: str, status: str) -> dict[str, object]:
        with self._connect() as connection:
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
        artifact_status = str(metadata.get("artifact_status", "GENERATED"))
        file_size = int(metadata.get("file_size", 0) or 0)
        checksum = str(metadata.get("checksum", ""))
        with self._connect() as connection:
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
            connection.execute(
                """
                INSERT INTO project_artifacts (
                    id, project_id, phase_name, artifact_type, status, file_path, file_size,
                    checksum, generation_params_json, source_phase_snapshot_json, provider_name,
                    provider_version, seed, error_code, error_message, created_at, updated_at,
                    last_verified_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status = excluded.status,
                    file_path = excluded.file_path,
                    file_size = excluded.file_size,
                    checksum = excluded.checksum,
                    generation_params_json = excluded.generation_params_json,
                    source_phase_snapshot_json = excluded.source_phase_snapshot_json,
                    provider_name = excluded.provider_name,
                    provider_version = excluded.provider_version,
                    seed = excluded.seed,
                    error_code = excluded.error_code,
                    error_message = excluded.error_message,
                    updated_at = excluded.updated_at,
                    last_verified_at = excluded.last_verified_at
                """,
                (
                    artifact_id,
                    song_id,
                    phase,
                    artifact_type,
                    artifact_status,
                    file_path,
                    file_size,
                    checksum,
                    json.dumps(metadata.get("generation_params", {}), ensure_ascii=False),
                    json.dumps(metadata.get("source_phase_snapshot", {}), ensure_ascii=False),
                    str(metadata.get("provider_name", metadata.get("source", ""))),
                    str(metadata.get("provider_version", "")),
                    str(metadata.get("seed", "")),
                    str(metadata.get("error_code", "")),
                    str(metadata.get("error_message", "")),
                    created_at,
                    created_at,
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

    def update_artifact_metadata(self, artifact_id: str, metadata: dict[str, object]) -> None:
        updated_at = utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE song_artifacts
                SET metadata_json = ?
                WHERE artifact_id = ?
                """,
                (json.dumps(metadata, ensure_ascii=False), artifact_id),
            )
            connection.execute(
                """
                UPDATE project_artifacts
                SET status = ?, file_size = ?, checksum = ?, error_code = ?, error_message = ?,
                    updated_at = ?, last_verified_at = ?
                WHERE id = ?
                """,
                (
                    str(metadata.get("artifact_status", "GENERATED")),
                    int(metadata.get("file_size", 0) or 0),
                    str(metadata.get("checksum", "")),
                    str(metadata.get("error_code", "")),
                    str(metadata.get("error_message", "")),
                    updated_at,
                    updated_at,
                    artifact_id,
                ),
            )

    def upsert_spec(
        self,
        song_id: str,
        json_spec: dict[str, object],
        approved_by_qwen: bool,
        missing_fields: list[str],
        schema_version: str = "1.0",
        technical_review_mode: str = "rule_validation",
        user_confirmation_status: str = "not_requested",
        expected_revision_id: str | None = None,
    ) -> dict[str, object]:
        now = utc_now()
        compilation_status = "needs_information" if missing_fields else "complete_for_stage"
        with self._connect() as connection:
            if expected_revision_id is not None:
                connection.execute("BEGIN IMMEDIATE")
                active = connection.execute(
                    "SELECT revision_id FROM song_spec_revisions WHERE song_id = ? ORDER BY revision_number DESC LIMIT 1",
                    (song_id,),
                ).fetchone()
                if not active or active[0] != expected_revision_id:
                    raise ValueError("La revision cambio. Recarga la ficha antes de guardar.")
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
            latest = connection.execute(
                """
                SELECT revision_number, json_spec, compilation_status, technical_review_mode,
                       user_confirmation_status, missing_fields_json
                FROM song_spec_revisions
                WHERE song_id = ?
                ORDER BY revision_number DESC
                LIMIT 1
                """,
                (song_id,),
            ).fetchone()
            json_payload = json.dumps(json_spec, ensure_ascii=False, sort_keys=True)
            missing_payload = json.dumps(missing_fields, ensure_ascii=False)
            unchanged = bool(
                latest
                and str(latest[1]) == json_payload
                and str(latest[2]) == compilation_status
                and str(latest[3]) == technical_review_mode
                and str(latest[4]) == user_confirmation_status
                and str(latest[5]) == missing_payload
            )
            if not unchanged:
                revision_number = int(latest[0]) + 1 if latest else 1
                connection.execute(
                    """
                    INSERT INTO song_spec_revisions (
                        revision_id, song_id, revision_number, schema_version, json_spec,
                        compilation_status, deterministic_valid, technical_review_mode,
                        user_confirmation_status, missing_fields_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"spec_rev_{uuid4().hex[:12]}", song_id, revision_number, schema_version,
                        json_payload, compilation_status, 1 if approved_by_qwen else 0,
                        technical_review_mode, user_confirmation_status, missing_payload, now,
                    ),
                )
        return self.get_spec(song_id) or {}

    def get_spec(self, song_id: str) -> dict[str, object] | None:
        with self._connect() as connection:
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
        result = {
            "song_id": str(row["song_id"]),
            "json_spec": json.loads(str(row["json_spec"])),
            "approved_by_qwen": bool(row["approved_by_qwen"]),
            "missing_fields": json.loads(str(row["missing_fields_json"])),
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
        }
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            revision = connection.execute(
                """
                SELECT revision_id, revision_number, schema_version, compilation_status,
                       deterministic_valid, technical_review_mode, user_confirmation_status, created_at
                FROM song_spec_revisions WHERE song_id = ?
                ORDER BY revision_number DESC LIMIT 1
                """,
                (song_id,),
            ).fetchone()
        if revision is not None:
            result["revision"] = {
                "revision_id": str(revision["revision_id"]),
                "revision_number": int(revision["revision_number"]),
                "schema_version": str(revision["schema_version"]),
                "compilation_status": str(revision["compilation_status"]),
                "deterministic_valid": bool(revision["deterministic_valid"]),
                "technical_review_mode": str(revision["technical_review_mode"]),
                "user_confirmation_status": str(revision["user_confirmation_status"]),
                "created_at": str(revision["created_at"]),
            }
        return result

    def list_spec_revisions(self, song_id: str) -> list[dict[str, object]]:
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT revision_id, revision_number, schema_version, json_spec,
                       compilation_status, deterministic_valid, technical_review_mode,
                       user_confirmation_status, missing_fields_json, created_at
                FROM song_spec_revisions WHERE song_id = ?
                ORDER BY revision_number DESC
                """,
                (song_id,),
            ).fetchall()
        return [
            {
                "revision_id": str(row["revision_id"]),
                "revision_number": int(row["revision_number"]),
                "schema_version": str(row["schema_version"]),
                "json_spec": json.loads(str(row["json_spec"])),
                "compilation_status": str(row["compilation_status"]),
                "deterministic_valid": bool(row["deterministic_valid"]),
                "technical_review_mode": str(row["technical_review_mode"]),
                "user_confirmation_status": str(row["user_confirmation_status"]),
                "missing_fields": json.loads(str(row["missing_fields_json"])),
                "created_at": str(row["created_at"]),
            }
            for row in rows
        ]

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
        with self._connect() as connection:
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
        with self._connect() as connection:
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
        with self._connect() as connection:
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
        swap_used_mb: float,
        visible_memory_limit_mb: float,
        cpu_percent: float,
        vram: list[dict[str, object]],
        disk_data_free_mb: float,
        disk_models_free_mb: float,
        disk_cache_free_mb: float,
        heavy_processes: list[dict[str, object]],
        decision: str,
        message: str,
    ) -> dict[str, object]:
        created_at = utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO resource_snapshots (
                    id, created_at, phase, ram_total_mb, ram_available_mb,
                    ram_used_percent, swap_total_mb, swap_free_mb,
                    swap_used_mb, visible_memory_limit_mb, cpu_percent, vram_json, disk_data_free_mb,
                    disk_models_free_mb, disk_cache_free_mb, heavy_processes_json,
                    decision, message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    swap_used_mb,
                    visible_memory_limit_mb,
                    cpu_percent,
                    json.dumps(vram, ensure_ascii=False),
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
            "swap_used_mb": swap_used_mb,
            "visible_memory_limit_mb": visible_memory_limit_mb,
            "cpu_percent": cpu_percent,
            "vram": vram,
            "disk_data_free_mb": disk_data_free_mb,
            "disk_models_free_mb": disk_models_free_mb,
            "disk_cache_free_mb": disk_cache_free_mb,
            "heavy_processes": heavy_processes,
            "decision": decision,
            "message": message,
        }

    def list_resource_snapshots(self, limit: int = 100) -> list[dict[str, object]]:
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT id, created_at, phase, ram_total_mb, ram_available_mb,
                       ram_used_percent, swap_total_mb, swap_free_mb,
                       swap_used_mb, visible_memory_limit_mb, cpu_percent, vram_json, disk_data_free_mb,
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
            "swap_used_mb": float(row["swap_used_mb"]),
            "visible_memory_limit_mb": float(row["visible_memory_limit_mb"]),
            "cpu_percent": float(row["cpu_percent"]),
            "vram": json.loads(str(row["vram_json"])),
            "disk_data_free_mb": float(row["disk_data_free_mb"]),
            "disk_models_free_mb": float(row["disk_models_free_mb"]),
            "disk_cache_free_mb": float(row["disk_cache_free_mb"]),
            "heavy_processes": json.loads(str(row["heavy_processes_json"])),
            "decision": str(row["decision"]),
            "message": str(row["message"]),
        }
