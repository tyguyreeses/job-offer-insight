"""SQLite bootstrap and migration helpers."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from typing import Iterator

from ..utils.config_types import DatabaseSection


class SQLiteDatabase:
    """Thin SQLite wrapper for connection and migration lifecycle."""

    def __init__(
        self,
        *,
        path: str | Path,
        enable_wal: bool,
        timeout_seconds: float,
        migrations_dir: Path | None = None,
    ) -> None:
        self._path = Path(path)
        self._enable_wal = enable_wal
        self._timeout_seconds = timeout_seconds
        self._migrations_dir = migrations_dir or Path(__file__).resolve().parent / "migrations"
        self._init_lock = Lock()
        self._initialized = False

    @property
    def path(self) -> Path:
        return self._path

    def initialize(self) -> None:
        if self._initialized:
            return
        with self._init_lock:
            if self._initialized:
                return

            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self.connection() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version TEXT PRIMARY KEY,
                        applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                self._apply_migrations(conn)
            self._initialized = True

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(
            self._path,
            timeout=self._timeout_seconds,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        if self._enable_wal:
            conn.execute("PRAGMA journal_mode = WAL;")

        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _apply_migrations(self, conn: sqlite3.Connection) -> None:
        for migration_path in sorted(self._migrations_dir.glob("*.sql")):
            version = migration_path.stem
            already_applied = conn.execute(
                "SELECT 1 FROM schema_migrations WHERE version = ?",
                (version,),
            ).fetchone()
            if already_applied:
                continue
            conn.executescript(migration_path.read_text(encoding="utf-8"))
            conn.execute(
                "INSERT INTO schema_migrations (version) VALUES (?)",
                (version,),
            )


def build_sqlite_database(config: DatabaseSection) -> SQLiteDatabase:
    return SQLiteDatabase(
        path=config.path,
        enable_wal=config.enable_wal,
        timeout_seconds=config.timeout_seconds,
    )
