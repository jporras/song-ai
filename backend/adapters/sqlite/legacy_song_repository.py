from __future__ import annotations

from pathlib import Path
import json
import sqlite3


class LegacySongRepository:
    """Persists the legacy set -> sample -> song workflow in SQLite."""

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
                CREATE TABLE IF NOT EXISTS legacy_samples (
                    sample_id TEXT PRIMARY KEY,
                    set_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    json_path TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(set_id) REFERENCES song_sets(set_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS legacy_songs (
                    song_id TEXT PRIMARY KEY,
                    sample_id TEXT NOT NULL,
                    set_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    json_path TEXT NOT NULL,
                    exports_path TEXT NOT NULL,
                    stems_path TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(sample_id) REFERENCES legacy_samples(sample_id),
                    FOREIGN KEY(set_id) REFERENCES song_sets(set_id)
                )
                """
            )
            connection.execute("CREATE INDEX IF NOT EXISTS idx_legacy_samples_set ON legacy_samples(set_id, created_at)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_legacy_songs_set ON legacy_songs(set_id, created_at)")

    def save_sample(self, payload: dict[str, object], json_path: Path, *, overwrite: bool = True) -> None:
        verb = "INSERT OR REPLACE" if overwrite else "INSERT OR IGNORE"
        with self._connect() as connection:
            connection.execute(
                f"""
                {verb} INTO legacy_samples
                    (sample_id, set_id, status, provider, json_path, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(payload["sample_id"]),
                    str(payload["set_id"]),
                    str(payload.get("status", "")),
                    str(payload.get("provider", "")),
                    str(json_path),
                    json.dumps(payload, ensure_ascii=False),
                    str(payload.get("created_at", "")),
                ),
            )

    def save_song(self, payload: dict[str, object], json_path: Path, *, overwrite: bool = True) -> None:
        verb = "INSERT OR REPLACE" if overwrite else "INSERT OR IGNORE"
        with self._connect() as connection:
            connection.execute(
                f"""
                {verb} INTO legacy_songs
                    (song_id, sample_id, set_id, status, provider, json_path, exports_path,
                     stems_path, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(payload["song_id"]),
                    str(payload["sample_id"]),
                    str(payload["set_id"]),
                    str(payload.get("status", "")),
                    str(payload.get("provider", "")),
                    str(json_path),
                    str(payload.get("exports_dir", "")),
                    str(payload.get("stems_dir", "")),
                    json.dumps(payload, ensure_ascii=False),
                    str(payload.get("created_at", "")),
                ),
            )

    def get_sample(self, sample_id: str) -> dict[str, object] | None:
        return self._get_one("legacy_samples", "sample_id", sample_id)

    def get_song(self, song_id: str) -> dict[str, object] | None:
        return self._get_one("legacy_songs", "song_id", song_id)

    def list_samples(self, set_id: str | None = None) -> list[dict[str, object]]:
        return self._list("legacy_samples", "sample_id", set_id)

    def list_songs(self, set_id: str | None = None) -> list[dict[str, object]]:
        return self._list("legacy_songs", "song_id", set_id)

    def delete_by_set(self, set_id: str) -> dict[str, list[dict[str, object]]]:
        samples = self.list_samples(set_id)
        songs = self.list_songs(set_id)
        with self._connect() as connection:
            connection.execute("DELETE FROM legacy_songs WHERE set_id = ?", (set_id,))
            connection.execute("DELETE FROM legacy_samples WHERE set_id = ?", (set_id,))
        return {"samples": samples, "songs": songs}

    def _get_one(self, table: str, id_column: str, value: str) -> dict[str, object] | None:
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                f"SELECT {id_column}, json_path, payload_json, created_at FROM {table} WHERE {id_column} = ?",
                (value,),
            ).fetchone()
        return self._row_to_dict(row, id_column) if row else None

    def _list(self, table: str, id_column: str, set_id: str | None) -> list[dict[str, object]]:
        query = f"SELECT {id_column}, json_path, payload_json, created_at FROM {table}"
        params: tuple[str, ...] = ()
        if set_id is not None:
            query += " WHERE set_id = ?"
            params = (set_id,)
        query += " ORDER BY created_at DESC, " + id_column + " DESC"
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(query, params).fetchall()
        return [self._row_to_dict(row, id_column) for row in rows]

    def _row_to_dict(self, row: sqlite3.Row, id_column: str) -> dict[str, object]:
        payload = json.loads(str(row["payload_json"]))
        payload[id_column] = str(row[id_column])
        payload["json_path"] = str(row["json_path"])
        payload["created_at"] = str(row["created_at"])
        return payload
