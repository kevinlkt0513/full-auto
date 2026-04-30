import secrets
import sqlite3
import time
from pathlib import Path
import bcrypt

from .settings import get_data_dir


_DUMMY_PW_HASH = bcrypt.hashpw(b"dummy-password-for-timing", bcrypt.gensalt(rounds=12))


_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  username TEXT PRIMARY KEY,
  pw_hash BLOB NOT NULL,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  username TEXT NOT NULL,
  created_at REAL NOT NULL,
  expires_at REAL NOT NULL,
  FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
);
"""


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.executescript(_SCHEMA)

    def _conn(self):
        c = sqlite3.connect(self.path, isolation_level=None)
        c.execute("PRAGMA foreign_keys = ON")
        return c

    def user_count(self) -> int:
        with self._conn() as c:
            return c.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    def create_user(self, username: str, password: str) -> None:
        h = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
        with self._conn() as c:
            c.execute(
                "INSERT INTO users(username, pw_hash, created_at) VALUES (?, ?, ?)",
                (username, h, time.time()),
            )

    def verify_user(self, username: str, password: str) -> bool:
        with self._conn() as c:
            row = c.execute("SELECT pw_hash FROM users WHERE username = ?", (username,)).fetchone()
        if not row:
            # Burn equivalent CPU to mask user-existence timing
            bcrypt.checkpw(password.encode(), _DUMMY_PW_HASH)
            return False
        return bcrypt.checkpw(password.encode(), row[0])

    def create_session(self, username: str, ttl_s: int = 7 * 24 * 3600) -> str:
        sid = secrets.token_urlsafe(32)
        now = time.time()
        with self._conn() as c:
            c.execute(
                "INSERT INTO sessions(id, username, created_at, expires_at) VALUES (?, ?, ?, ?)",
                (sid, username, now, now + ttl_s),
            )
        return sid

    def lookup_session(self, sid: str) -> str | None:
        with self._conn() as c:
            row = c.execute(
                "SELECT username, expires_at FROM sessions WHERE id = ?", (sid,)
            ).fetchone()
        if not row:
            return None
        username, expires_at = row
        if time.time() >= expires_at:
            self.delete_session(sid)
            return None
        return username

    def delete_session(self, sid: str) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM sessions WHERE id = ?", (sid,))


def get_db() -> Database:
    """Database instance pointing to the configured webui.db path.
    Reads WEBUI_DATA_DIR at call time (test isolation)."""
    return Database(get_data_dir() / "webui.db")
