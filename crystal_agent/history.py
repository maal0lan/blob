import sqlite3
from pathlib import Path
from .config import APP_DIR
DB_PATH = APP_DIR / "history.sqlite3"

def connect():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def initialize():
    with connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, title TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        db.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE, role TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")

def add(session_id: str, role: str, content: str):
    if not content.strip(): return
    with connect() as db:
        db.execute("INSERT OR IGNORE INTO sessions(id,title) VALUES(?,?)", (session_id, content.strip().splitlines()[0][:70]))
        db.execute("INSERT INTO messages(session_id,role,content) VALUES(?,?,?)", (session_id, role, content))

def recent(session_id: str, limit: int = 12):
    with connect() as db:
        rows = db.execute("SELECT role,content FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?", (session_id, limit)).fetchall()
    return [{"role": r, "content": c} for r, c in reversed(rows)]

def clear():
    with connect() as db: db.execute("DELETE FROM sessions")
