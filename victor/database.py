import sqlite3
from contextlib import contextmanager


class Database:
    """Conexión por operación: ningún cursor SQLite cruza hilos."""
    def __init__(self, path):
        self.path = str(path)
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript('''
                CREATE TABLE IF NOT EXISTS conversations(
                    id INTEGER PRIMARY KEY, title TEXT NOT NULL,
                    created TEXT DEFAULT CURRENT_TIMESTAMP, summary TEXT DEFAULT '', summarized_id INTEGER DEFAULT 0);
                CREATE TABLE IF NOT EXISTS messages(
                    id INTEGER PRIMARY KEY, conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                    role TEXT NOT NULL, content TEXT NOT NULL, created TEXT DEFAULT CURRENT_TIMESTAMP);
                CREATE INDEX IF NOT EXISTS message_conversation ON messages(conversation_id,id);
                CREATE TABLE IF NOT EXISTS memories(
                    id INTEGER PRIMARY KEY, key TEXT UNIQUE NOT NULL, value TEXT NOT NULL,
                    updated TEXT DEFAULT CURRENT_TIMESTAMP);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()
