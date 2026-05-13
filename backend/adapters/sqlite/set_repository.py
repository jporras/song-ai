from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3

from models.song_set import SongSet


class SetRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.ensure_schema()

    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as connection:
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

    def save_set(self, song_set: SongSet, json_path: Path) -> None:
        created_at = song_set.created_at or datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as connection:
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
        with sqlite3.connect(self.db_path) as connection:
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
        with sqlite3.connect(self.db_path) as connection:
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
