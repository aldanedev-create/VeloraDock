"""SQLite state. Each operation uses a separate connection."""
import json
import sqlite3
import threading
from pathlib import Path

class Store:
    def __init__(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True)
        self.directory = directory
        self.path = directory / "veloradock.sqlite3"
        self.lock = threading.RLock()
        with self.connect() as connection:
            connection.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS roots(id INTEGER PRIMARY KEY, path TEXT UNIQUE NOT NULL);
                CREATE TABLE IF NOT EXISTS files(id INTEGER PRIMARY KEY, root_id INTEGER NOT NULL,
                    path TEXT UNIQUE NOT NULL, name TEXT NOT NULL, folded TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS files_name ON files(folded);
                CREATE TABLE IF NOT EXISTS apps(id INTEGER PRIMARY KEY, path TEXT UNIQUE NOT NULL, name TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS actions(id INTEGER PRIMARY KEY, name TEXT NOT NULL,
                    keyword TEXT NOT NULL, path TEXT NOT NULL, args TEXT NOT NULL, favorite INTEGER DEFAULT 0);
                CREATE TABLE IF NOT EXISTS clips(id INTEGER PRIMARY KEY, data BLOB NOT NULL,
                    digest TEXT NOT NULL, created REAL NOT NULL, favorite INTEGER DEFAULT 0);
                CREATE TABLE IF NOT EXISTS extensions(id TEXT PRIMARY KEY, manifest TEXT NOT NULL);
            """)

    def connect(self):
        connection = sqlite3.connect(self.path, timeout=15)
        connection.row_factory = sqlite3.Row
        return connection

    def rows(self, sql, values=()):
        with self.connect() as connection:
            return [dict(row) for row in connection.execute(sql, values).fetchall()]

    def execute(self, sql, values=()):
        with self.connect() as connection:
            cursor = connection.execute(sql, values)
            return cursor.lastrowid

    def setting(self, name, default=None):
        rows = self.rows("SELECT value FROM settings WHERE key=?", (name,))
        return json.loads(rows[0]["value"]) if rows else default

    def set_setting(self, name, value):
        self.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (name, json.dumps(value)))
