from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3


class OrchestrationRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.ensure_schema()

    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    task_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    model_role TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    progress INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS model_runs (
                    run_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    model_role TEXT NOT NULL,
                    provider_name TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS project_events (
                    event_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    project_name TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    model_role TEXT NOT NULL,
                    provider_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def create_task(
        self,
        task_id: str,
        task_type: str,
        model_role: str,
        payload: dict[str, object],
        message: str,
    ) -> dict[str, object]:
        created_at = self.now()
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO tasks (
                    task_id,
                    task_type,
                    status,
                    model_role,
                    payload_json,
                    result_json,
                    progress,
                    message,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    task_type,
                    "pending",
                    model_role,
                    json.dumps(payload, ensure_ascii=False),
                    "{}",
                    0,
                    message,
                    created_at,
                    created_at,
                ),
            )
        return self.get_task(task_id) or {}

    def update_task(
        self,
        task_id: str,
        status: str,
        progress: int,
        message: str,
        result: dict[str, object] | None = None,
    ) -> dict[str, object]:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                UPDATE tasks
                SET status = ?,
                    progress = ?,
                    message = ?,
                    result_json = ?,
                    updated_at = ?
                WHERE task_id = ?
                """,
                (
                    status,
                    progress,
                    message,
                    json.dumps(result or {}, ensure_ascii=False),
                    self.now(),
                    task_id,
                ),
            )
        return self.get_task(task_id) or {}

    def list_tasks(self) -> list[dict[str, object]]:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT task_id, task_type, status, model_role, payload_json, result_json, progress, message, created_at, updated_at
                FROM tasks
                ORDER BY updated_at DESC
                """
            ).fetchall()
        return [self.task_row_to_dict(row) for row in rows]

    def get_task(self, task_id: str) -> dict[str, object] | None:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                SELECT task_id, task_type, status, model_role, payload_json, result_json, progress, message, created_at, updated_at
                FROM tasks
                WHERE task_id = ?
                """,
                (task_id,),
            ).fetchone()
        if row is None:
            return None
        return self.task_row_to_dict(row)

    def create_model_run(
        self,
        run_id: str,
        task_id: str,
        model_role: str,
        provider_name: str,
        model_name: str,
        metadata: dict[str, object],
    ) -> dict[str, object]:
        started_at = self.now()
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO model_runs (
                    run_id,
                    task_id,
                    model_role,
                    provider_name,
                    model_name,
                    status,
                    started_at,
                    completed_at,
                    metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    task_id,
                    model_role,
                    provider_name,
                    model_name,
                    "running",
                    started_at,
                    "",
                    json.dumps(metadata, ensure_ascii=False),
                ),
            )
        return self.get_model_run(run_id) or {}

    def complete_model_run(
        self,
        run_id: str,
        status: str,
        metadata: dict[str, object],
    ) -> dict[str, object]:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                UPDATE model_runs
                SET status = ?,
                    completed_at = ?,
                    metadata_json = ?
                WHERE run_id = ?
                """,
                (
                    status,
                    self.now(),
                    json.dumps(metadata, ensure_ascii=False),
                    run_id,
                ),
            )
        return self.get_model_run(run_id) or {}

    def list_model_runs(self) -> list[dict[str, object]]:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT run_id, task_id, model_role, provider_name, model_name, status, started_at, completed_at, metadata_json
                FROM model_runs
                ORDER BY started_at DESC
                """
            ).fetchall()
        return [self.model_run_row_to_dict(row) for row in rows]

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
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO project_events (
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
                    metadata_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
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
                    json.dumps(metadata, ensure_ascii=False),
                    self.now(),
                ),
            )
        return self.get_project_event(event_id) or {}

    def list_project_events(self, project_id: str | None = None) -> list[dict[str, object]]:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            if project_id:
                rows = connection.execute(
                    """
                    SELECT event_id, project_id, project_name, phase, actor, model_role, provider_name, status, message, task_id, run_id, metadata_json, created_at
                    FROM project_events
                    WHERE project_id = ?
                    ORDER BY created_at ASC
                    """,
                    (project_id,),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT event_id, project_id, project_name, phase, actor, model_role, provider_name, status, message, task_id, run_id, metadata_json, created_at
                    FROM project_events
                    ORDER BY created_at DESC
                    """
                ).fetchall()
        return [self.project_event_row_to_dict(row) for row in rows]

    def get_project_event(self, event_id: str) -> dict[str, object] | None:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                SELECT event_id, project_id, project_name, phase, actor, model_role, provider_name, status, message, task_id, run_id, metadata_json, created_at
                FROM project_events
                WHERE event_id = ?
                """,
                (event_id,),
            ).fetchone()
        if row is None:
            return None
        return self.project_event_row_to_dict(row)

    def get_model_run(self, run_id: str) -> dict[str, object] | None:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                SELECT run_id, task_id, model_role, provider_name, model_name, status, started_at, completed_at, metadata_json
                FROM model_runs
                WHERE run_id = ?
                """,
                (run_id,),
            ).fetchone()
        if row is None:
            return None
        return self.model_run_row_to_dict(row)

    def task_row_to_dict(self, row: sqlite3.Row) -> dict[str, object]:
        return {
            "task_id": str(row["task_id"]),
            "task_type": str(row["task_type"]),
            "status": str(row["status"]),
            "model_role": str(row["model_role"]),
            "payload": json.loads(str(row["payload_json"])),
            "result": json.loads(str(row["result_json"])),
            "progress": int(row["progress"]),
            "message": str(row["message"]),
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
        }

    def model_run_row_to_dict(self, row: sqlite3.Row) -> dict[str, object]:
        return {
            "run_id": str(row["run_id"]),
            "task_id": str(row["task_id"]),
            "model_role": str(row["model_role"]),
            "provider_name": str(row["provider_name"]),
            "model_name": str(row["model_name"]),
            "status": str(row["status"]),
            "started_at": str(row["started_at"]),
            "completed_at": str(row["completed_at"]),
            "metadata": json.loads(str(row["metadata_json"])),
        }

    def project_event_row_to_dict(self, row: sqlite3.Row) -> dict[str, object]:
        return {
            "event_id": str(row["event_id"]),
            "project_id": str(row["project_id"]),
            "project_name": str(row["project_name"]),
            "phase": str(row["phase"]),
            "actor": str(row["actor"]),
            "model_role": str(row["model_role"]),
            "provider_name": str(row["provider_name"]),
            "status": str(row["status"]),
            "message": str(row["message"]),
            "task_id": str(row["task_id"]),
            "run_id": str(row["run_id"]),
            "metadata": json.loads(str(row["metadata_json"])),
            "created_at": str(row["created_at"]),
        }

    def now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
