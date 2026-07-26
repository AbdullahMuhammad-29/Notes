"""SQLite-backed user accounts - real signup + login, one row per user,
passwords hashed with werkzeug (never stored in plain text).
"""
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""


class UserStore:
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

    def create_user(self, username, password):
        username = (username or "").strip()
        if not username:
            raise ValueError("Username is required.")
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters.")

        conn = self._connect()
        if conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
            conn.close()
            raise ValueError("That username is already taken.")

        password_hash = generate_password_hash(password)
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, password_hash, now),
        )
        conn.commit()
        user_id = cur.lastrowid
        conn.close()
        return user_id

    def verify_login(self, username, password):
        """Returns the user row on success, or None if credentials are wrong."""
        conn = self._connect()
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        if row and check_password_hash(row["password_hash"], password):
            return row
        return None

    def get_user(self, user_id):
        conn = self._connect()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        return row
