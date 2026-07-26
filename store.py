"""SQLite-backed storage for notes. Every note belongs to a user_id, and
every read/write is scoped to that user - one user can never see or modify
another user's notes.
"""
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    tags TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class NoteStore:
    def __init__(self, db_path=None):
        self.db_path = db_path or str(Path(__file__).parent / "notes.db")
        conn = self._connect()
        conn.execute(SCHEMA)
        conn.commit()
        conn.close()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create(self, user_id, title, body, tags=""):
        now = _now()
        conn = self._connect()
        cur = conn.execute(
            "INSERT INTO notes (user_id, title, body, tags, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, title, body, tags, now, now),
        )
        conn.commit()
        note_id = cur.lastrowid
        conn.close()
        return note_id

    def update(self, note_id, user_id, title, body, tags=""):
        now = _now()
        conn = self._connect()
        cur = conn.execute(
            "UPDATE notes SET title=?, body=?, tags=?, updated_at=? WHERE id=? AND user_id=?",
            (title, body, tags, now, note_id, user_id),
        )
        conn.commit()
        changed = cur.rowcount > 0
        conn.close()
        return changed

    def delete(self, note_id, user_id):
        conn = self._connect()
        cur = conn.execute("DELETE FROM notes WHERE id=? AND user_id=?", (note_id, user_id))
        conn.commit()
        changed = cur.rowcount > 0
        conn.close()
        return changed

    def get(self, note_id, user_id):
        conn = self._connect()
        row = conn.execute("SELECT * FROM notes WHERE id=? AND user_id=?", (note_id, user_id)).fetchone()
        conn.close()
        return row

    def list(self, user_id, query=None):
        conn = self._connect()
        if query:
            like = f"%{query}%"
            rows = conn.execute(
                "SELECT * FROM notes WHERE user_id=? AND (title LIKE ? OR tags LIKE ?) ORDER BY updated_at DESC",
                (user_id, like, like),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM notes WHERE user_id=? ORDER BY updated_at DESC", (user_id,)
            ).fetchall()
        conn.close()
        return rows
