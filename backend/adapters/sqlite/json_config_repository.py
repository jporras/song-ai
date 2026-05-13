from datetime import datetime, timezone
from pathlib import Path
import sqlite3


class JsonConfigRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.ensure_schema()

    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS json_config_paths (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT NOT NULL UNIQUE,
                    kind TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def save_path(self, path: Path) -> None:
        resolved_path = str(path.resolve())
        created_at = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO json_config_paths (path, kind, created_at)
                VALUES (?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET kind = excluded.kind
                """,
                (resolved_path, path.name, created_at),
            )

    def list_paths(self) -> list[dict[str, str]]:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT id, path, kind, created_at
                FROM json_config_paths
                ORDER BY id DESC
                """
            ).fetchall()
        return [
            {
                "id": str(row["id"]),
                "path": str(row["path"]),
                "kind": str(row["kind"]),
                "created_at": str(row["created_at"]),
            }
            for row in rows
        ]
