"""SQLite database setup and access layer."""
import sqlite3
import os
from pathlib import Path

DB_PATH = os.environ.get("PRODUCTIVITY_DB", str(Path.home() / ".productivity.db"))


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS classes (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT DEFAULT '',
                color TEXT DEFAULT 'cyan'
            );

            CREATE TABLE IF NOT EXISTS assignment_types (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                name   TEXT NOT NULL UNIQUE,
                weight REAL DEFAULT 1.0
            );

            CREATE TABLE IF NOT EXISTS assignments (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                title        TEXT NOT NULL,
                class_id     INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
                type_id      INTEGER REFERENCES assignment_types(id) ON DELETE SET NULL,
                due_date     TEXT NOT NULL,
                est_hours    REAL DEFAULT 1.0,
                priority     INTEGER DEFAULT 2,
                completed    INTEGER DEFAULT 0,
                notes        TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS tests (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                class_id    INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
                date        TEXT NOT NULL,
                topics      TEXT DEFAULT '',
                est_hours   REAL DEFAULT 2.0,
                importance  INTEGER DEFAULT 2
            );

            CREATE TABLE IF NOT EXISTS study_plans (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                plan_text  TEXT NOT NULL
            );
        """)
        # Seed default assignment types if none exist
        types = conn.execute("SELECT COUNT(*) FROM assignment_types").fetchone()[0]
        if types == 0:
            conn.executemany(
                "INSERT INTO assignment_types (name, weight) VALUES (?, ?)",
                [
                    ("Homework", 0.5),
                    ("Quiz", 1.0),
                    ("Project", 1.5),
                    ("Midterm", 2.0),
                    ("Final Exam", 3.0),
                    ("Lab", 0.75),
                ],
            )
