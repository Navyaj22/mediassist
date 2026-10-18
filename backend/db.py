"""Tiny SQLite layer for chat history (plain SQL, no ORM)."""
import json
import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.getenv("MEDIASSIST_DB", Path(__file__).parent / "chat.db"))


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                sources TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )"""
        )


def save_chat(question, answer, sources):
    with _conn() as c:
        c.execute(
            "INSERT INTO history (question, answer, sources) VALUES (?, ?, ?)",
            (question, answer, json.dumps(sources)),
        )


def get_history(limit=50):
    with _conn() as c:
        rows = c.execute(
            "SELECT id, question, answer, sources, created_at FROM history ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        {**dict(r), "sources": json.loads(r["sources"])} for r in reversed(rows)
    ]


def clear_history():
    with _conn() as c:
        c.execute("DELETE FROM history")
