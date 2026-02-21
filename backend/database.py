"""SQLite database for sci.platformai.org user management."""

import os
import sqlite3
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "sci.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT UNIQUE NOT NULL,
    user_name   TEXT NOT NULL DEFAULT '',
    role        TEXT DEFAULT 'user',
    credit      REAL DEFAULT 0,
    token       INTEGER DEFAULT 0,
    sso_token   TEXT DEFAULT '',
    api_key     TEXT DEFAULT '',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
"""


def get_db() -> sqlite3.Connection:
    """Return a new database connection with row_factory set."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def upsert_user(user_info: dict, sso_token: str = "") -> dict:
    """Insert or update a user record. Returns the user dict."""
    now = datetime.utcnow().isoformat()
    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM users WHERE user_id = ?", (user_info["user_id"],)
    ).fetchone()

    if existing:
        conn.execute(
            """UPDATE users
               SET user_name=?, sso_token=?, api_key=?, credit=?, token=?, updated_at=?
               WHERE user_id=?""",
            (
                user_info.get("user_name", ""),
                sso_token,
                user_info.get("api_key", ""),
                user_info.get("credit", 0),
                user_info.get("token", 0),
                now,
                user_info["user_id"],
            ),
        )
    else:
        conn.execute(
            """INSERT INTO users
               (user_id, user_name, role, credit, token, sso_token, api_key, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_info["user_id"],
                user_info.get("user_name", ""),
                user_info.get("role", "user"),
                user_info.get("credit", 0),
                user_info.get("token", 0),
                sso_token,
                user_info.get("api_key", ""),
                now,
                now,
            ),
        )
    conn.commit()
    conn.close()
    return user_info


def get_user(user_id: str) -> dict | None:
    """Fetch a user by user_id. Returns dict or None."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None
