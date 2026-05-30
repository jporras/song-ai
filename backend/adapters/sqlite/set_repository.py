from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3
from uuid import uuid4

from models.song_set import SongSet


class SetRepository:
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
                CREATE TABLE IF NOT EXISTS song_sets (
                    set_id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL DEFAULT '',
                    description TEXT NOT NULL DEFAULT '',
                    instrumental_id TEXT NOT NULL,
                    melody_id TEXT NOT NULL,
                    lyrics_id TEXT NOT NULL,
                    compatibility_json TEXT NOT NULL,
                    json_path TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            columns = {
                str(row[1])
                for row in connection.execute("PRAGMA table_info(song_sets)").fetchall()
            }
            if "project_name" not in columns:
                connection.execute("ALTER TABLE song_sets ADD COLUMN project_name TEXT NOT NULL DEFAULT ''")
            if "description" not in columns:
                connection.execute("ALTER TABLE song_sets ADD COLUMN description TEXT NOT NULL DEFAULT ''")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS project_phase_data (
                    set_id TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    id TEXT NOT NULL DEFAULT '',
                    project_id TEXT NOT NULL DEFAULT '',
                    phase_name TEXT NOT NULL DEFAULT '',
                    phase_status TEXT NOT NULL DEFAULT 'NOT_CREATED',
                    change_source TEXT NOT NULL DEFAULT 'DEFAULT',
                    validation_status TEXT NOT NULL DEFAULT 'unknown',
                    created_at TEXT NOT NULL DEFAULT '',
                    completed_at TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY (set_id, phase)
                )
                """
            )
            self._ensure_phase_data_columns(connection)
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS project_phase_events (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    phase_name TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    before_json TEXT NOT NULL,
                    after_json TEXT NOT NULL,
                    message TEXT NOT NULL,
                    error_code TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS project_ui_state (
                    set_id TEXT PRIMARY KEY,
                    last_active_phase TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL
                )
                """
            )

    def _ensure_phase_data_columns(self, connection: sqlite3.Connection) -> None:
        columns = {str(row[1]) for row in connection.execute("PRAGMA table_info(project_phase_data)").fetchall()}
        additions = {
            "id": "TEXT NOT NULL DEFAULT ''",
            "project_id": "TEXT NOT NULL DEFAULT ''",
            "phase_name": "TEXT NOT NULL DEFAULT ''",
            "phase_status": "TEXT NOT NULL DEFAULT 'NOT_CREATED'",
            "change_source": "TEXT NOT NULL DEFAULT 'DEFAULT'",
            "validation_status": "TEXT NOT NULL DEFAULT 'unknown'",
            "created_at": "TEXT NOT NULL DEFAULT ''",
            "completed_at": "TEXT NOT NULL DEFAULT ''",
        }
        for name, definition in additions.items():
            if name not in columns:
                connection.execute(f"ALTER TABLE project_phase_data ADD COLUMN {name} {definition}")
        now = datetime.now(timezone.utc).isoformat()
        connection.execute("UPDATE project_phase_data SET id = lower(hex(randomblob(16))) WHERE id = ''")
        connection.execute("UPDATE project_phase_data SET project_id = set_id WHERE project_id = ''")
        connection.execute("UPDATE project_phase_data SET phase_name = phase WHERE phase_name = ''")
        connection.execute("UPDATE project_phase_data SET phase_status = 'COMPLETED' WHERE phase_status IN ('', 'NOT_CREATED') AND status != ''")
        connection.execute("UPDATE project_phase_data SET change_source = 'USER' WHERE change_source = ''")
        connection.execute("UPDATE project_phase_data SET validation_status = 'valid' WHERE validation_status = ''")
        connection.execute("UPDATE project_phase_data SET created_at = updated_at WHERE created_at = '' AND updated_at != ''")
        connection.execute("UPDATE project_phase_data SET created_at = ? WHERE created_at = ''", (now,))

    def save_set(self, song_set: SongSet, json_path: Path) -> None:
        created_at = song_set.created_at or datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO song_sets (
                    set_id,
                    project_name,
                    description,
                    instrumental_id,
                    melody_id,
                    lyrics_id,
                    compatibility_json,
                    json_path,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(set_id) DO UPDATE SET
                    project_name = excluded.project_name,
                    description = excluded.description,
                    instrumental_id = excluded.instrumental_id,
                    melody_id = excluded.melody_id,
                    lyrics_id = excluded.lyrics_id,
                    compatibility_json = excluded.compatibility_json,
                    json_path = excluded.json_path,
                    created_at = excluded.created_at
                """
                ,
                (
                    song_set.set_id,
                    song_set.project_name,
                    song_set.description,
                    song_set.instrumental_id,
                    song_set.melody_id,
                    song_set.lyrics_id,
                    json.dumps(song_set.compatibility_data, ensure_ascii=False),
                    str(json_path.resolve()),
                    created_at,
                ),
            )

    def list_sets(self) -> list[dict[str, object]]:
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT
                    set_id,
                    project_name,
                    description,
                    instrumental_id,
                    melody_id,
                    lyrics_id,
                    compatibility_json,
                    json_path,
                    created_at
                FROM song_sets
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def get_set(self, set_id: str) -> dict[str, object] | None:
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                SELECT
                    set_id,
                    project_name,
                    description,
                    instrumental_id,
                    melody_id,
                    lyrics_id,
                    compatibility_json,
                    json_path,
                    created_at
                FROM song_sets
                WHERE set_id = ?
                """
                ,
                (set_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_dict(row)

    def update_description(self, set_id: str, description: str) -> dict[str, object] | None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE song_sets SET description = ? WHERE set_id = ?",
                (description, set_id),
            )
        return self.get_set(set_id)

    def save_phase_data(
        self,
        set_id: str,
        phase: str,
        data: dict[str, object],
        status: str,
        phase_status: str = "COMPLETED",
        change_source: str = "USER",
        validation_status: str = "valid",
    ) -> dict[str, object] | None:
        if self.get_set(set_id) is None:
            return None
        updated_at = datetime.now(timezone.utc).isoformat()
        existing = self.get_phase_data(set_id, phase)
        row_id = str(existing.get("id", "")) if existing else f"phase_{uuid4().hex[:12]}"
        created_at = str(existing.get("created_at", "")) if existing else updated_at
        completed_at = updated_at if phase_status == "COMPLETED" else str(existing.get("completed_at", "")) if existing else ""
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO project_phase_data (
                    set_id, phase, data_json, status, updated_at, id, project_id, phase_name,
                    phase_status, change_source, validation_status, created_at, completed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(set_id, phase) DO UPDATE SET
                    data_json = excluded.data_json,
                    status = excluded.status,
                    updated_at = excluded.updated_at,
                    phase_status = excluded.phase_status,
                    change_source = excluded.change_source,
                    validation_status = excluded.validation_status,
                    completed_at = excluded.completed_at
                """,
                (
                    set_id,
                    phase,
                    json.dumps(data, ensure_ascii=False),
                    status,
                    updated_at,
                    row_id,
                    set_id,
                    phase,
                    phase_status,
                    change_source,
                    validation_status,
                    created_at,
                    completed_at,
                ),
            )
        event_type = "PHASE_SAVED"
        if phase_status == "INITIALIZED":
            event_type = "PHASE_INITIALIZED"
        elif phase_status == "DRAFT" and change_source == "AI":
            event_type = "AI_SUGGESTED"
        elif phase_status == "DRAFT":
            event_type = "USER_MODIFIED"
        self.create_phase_event(
            project_id=set_id,
            phase_name=phase,
            event_type=event_type,
            source=change_source,
            before=dict(existing or {}),
            after=self.get_phase_data(set_id, phase) or {},
            message=f"Fase {phase} guardada con estado {phase_status}.",
        )
        return self.get_phase_data(set_id, phase)

    def initialize_phase_data(self, set_id: str, phase: str, defaults: dict[str, object] | None = None) -> dict[str, object] | None:
        return self.save_phase_data(
            set_id=set_id,
            phase=phase,
            data=defaults or {},
            status="initialized",
            phase_status="INITIALIZED",
            change_source="DEFAULT",
            validation_status="pending",
        )

    def get_phase_data(self, set_id: str, phase: str) -> dict[str, object] | None:
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                SELECT set_id, phase, data_json, status, updated_at, id, project_id, phase_name,
                       phase_status, change_source, validation_status, created_at, completed_at
                FROM project_phase_data
                WHERE set_id = ? AND phase = ?
                """,
                (set_id, phase),
            ).fetchone()
        if row is None:
            return None
        return self._phase_row_to_dict(row)

    def list_phase_data(self, set_id: str) -> dict[str, object]:
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT set_id, phase, data_json, status, updated_at, id, project_id, phase_name,
                       phase_status, change_source, validation_status, created_at, completed_at
                FROM project_phase_data
                WHERE set_id = ?
                ORDER BY updated_at ASC
                """,
                (set_id,),
            ).fetchall()
        return {str(row["phase"]): self._phase_row_to_dict(row) for row in rows}

    def create_phase_event(
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
        event_id = f"phase_event_{uuid4().hex[:12]}"
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO project_phase_events (
                    id, project_id, phase_name, event_type, source, before_json, after_json,
                    message, error_code, error_message, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    project_id,
                    phase_name,
                    event_type,
                    source,
                    json.dumps(before or {}, ensure_ascii=False),
                    json.dumps(after or {}, ensure_ascii=False),
                    message,
                    error_code,
                    error_message,
                    created_at,
                ),
            )
        return {
            "id": event_id,
            "project_id": project_id,
            "phase_name": phase_name,
            "event_type": event_type,
            "source": source,
            "before": before or {},
            "after": after or {},
            "message": message,
            "error_code": error_code,
            "error_message": error_message,
            "created_at": created_at,
        }

    def list_phase_events(self, project_id: str) -> list[dict[str, object]]:
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT id, project_id, phase_name, event_type, source, before_json, after_json,
                       message, error_code, error_message, created_at
                FROM project_phase_events
                WHERE project_id = ?
                ORDER BY created_at ASC
                """,
                (project_id,),
            ).fetchall()
        return [
            {
                "id": str(row["id"]),
                "project_id": str(row["project_id"]),
                "phase_name": str(row["phase_name"]),
                "event_type": str(row["event_type"]),
                "source": str(row["source"]),
                "before": json.loads(str(row["before_json"])),
                "after": json.loads(str(row["after_json"])),
                "message": str(row["message"]),
                "error_code": str(row["error_code"]),
                "error_message": str(row["error_message"]),
                "created_at": str(row["created_at"]),
            }
            for row in rows
        ]

    def save_ui_state(self, set_id: str, last_active_phase: str) -> dict[str, object] | None:
        if self.get_set(set_id) is None:
            return None
        updated_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO project_ui_state (set_id, last_active_phase, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(set_id) DO UPDATE SET
                    last_active_phase = excluded.last_active_phase,
                    updated_at = excluded.updated_at
                """,
                (set_id, last_active_phase, updated_at),
            )
        return self.get_ui_state(set_id)

    def get_ui_state(self, set_id: str) -> dict[str, object]:
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                SELECT set_id, last_active_phase, updated_at
                FROM project_ui_state
                WHERE set_id = ?
                """,
                (set_id,),
            ).fetchone()
        if row is None:
            return {"set_id": set_id, "last_active_phase": "", "updated_at": ""}
        return {
            "set_id": str(row["set_id"]),
            "last_active_phase": str(row["last_active_phase"]),
            "updated_at": str(row["updated_at"]),
        }

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, object]:
        return {
            "set_id": str(row["set_id"]),
            "project_name": str(row["project_name"] or row["set_id"]),
            "description": str(row["description"] or ""),
            "instrumental_id": str(row["instrumental_id"]),
            "melody_id": str(row["melody_id"]),
            "lyrics_id": str(row["lyrics_id"]),
            "compatibility_data": json.loads(str(row["compatibility_json"])),
            "json_path": str(row["json_path"]),
            "created_at": str(row["created_at"]),
        }

    def _phase_row_to_dict(self, row: sqlite3.Row) -> dict[str, object]:
        return {
            "id": str(row["id"]),
            "project_id": str(row["project_id"] or row["set_id"]),
            "phase_name": str(row["phase_name"] or row["phase"]),
            "set_id": str(row["set_id"]),
            "phase": str(row["phase"]),
            "data": json.loads(str(row["data_json"])),
            "status": str(row["status"]),
            "phase_status": str(row["phase_status"]),
            "change_source": str(row["change_source"]),
            "validation_status": str(row["validation_status"]),
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
            "completed_at": str(row["completed_at"]),
        }
