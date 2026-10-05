"""Versioned candidate plans in the active SQLite database."""
from contextlib import closing
import json
import sqlite3
from datetime import datetime, timezone
from uuid import uuid4


class AceStepPlanRepository:
    def __init__(self, db_path):
        self.db_path = db_path
        with closing(sqlite3.connect(db_path)) as connection, connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS ace_step_plans (
                plan_id TEXT PRIMARY KEY, song_id TEXT NOT NULL, spec_revision_id TEXT NOT NULL,
                plan_sha256 TEXT NOT NULL, plan_json TEXT NOT NULL, status TEXT NOT NULL,
                created_at TEXT NOT NULL, approved_at TEXT)""")

    def save(self, song_id: str, plan: dict) -> dict:
        item = {"plan_id": "ace_plan_" + uuid4().hex, "song_id": song_id,
                "plan": plan, "status": "candidate", "created_at": datetime.now(timezone.utc).isoformat(),
                "approved_at": None}
        with closing(sqlite3.connect(self.db_path)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            self._require_revision(connection, song_id, plan["spec_revision_id"])
            connection.execute("INSERT INTO ace_step_plans VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                               (item["plan_id"], song_id, plan["spec_revision_id"], plan["plan_sha256"],
                                json.dumps(plan, ensure_ascii=False), item["status"], item["created_at"], None))
        return item

    def get(self, song_id: str, plan_id: str) -> dict | None:
        with closing(sqlite3.connect(self.db_path)) as connection:
            row = connection.execute("SELECT plan_id, song_id, plan_json, status, created_at, approved_at FROM ace_step_plans WHERE song_id=? AND plan_id=?",
                                     (song_id, plan_id)).fetchone()
        return dict(zip(("plan_id", "song_id", "plan", "status", "created_at", "approved_at"),
                        (row[0], row[1], json.loads(row[2]), *row[3:]))) if row else None

    def latest(self, song_id: str) -> dict | None:
        with closing(sqlite3.connect(self.db_path)) as connection:
            row = connection.execute("SELECT plan_id FROM ace_step_plans WHERE song_id=? ORDER BY rowid DESC LIMIT 1", (song_id,)).fetchone()
        return self.get(song_id, row[0]) if row else None

    def approve(self, song_id: str, plan_id: str, revision_id: str, sha256: str) -> dict:
        with closing(sqlite3.connect(self.db_path)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            self._require_revision(connection, song_id, revision_id)
            result = connection.execute("""UPDATE ace_step_plans SET status='approved', approved_at=COALESCE(approved_at, ?)
                WHERE song_id=? AND plan_id=? AND spec_revision_id=? AND plan_sha256=?""",
                (datetime.now(timezone.utc).isoformat(), song_id, plan_id, revision_id, sha256))
            if result.rowcount != 1:
                raise ValueError("El plan cambio o no pertenece al proyecto activo.")
        return self.get(song_id, plan_id)

    @staticmethod
    def _require_revision(connection, song_id, revision_id):
        row = connection.execute("SELECT revision_id, user_confirmation_status FROM song_spec_revisions WHERE song_id=? ORDER BY revision_number DESC LIMIT 1", (song_id,)).fetchone()
        if not row or row != (revision_id, "confirmed"):
            raise ValueError("La ficha cambio o no esta confirmada; prepara un nuevo plan.")
