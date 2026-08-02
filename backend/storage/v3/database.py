"""SQLite engine, generation checks, and Alembic lifecycle for v3."""
from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import Connection, Engine, URL, create_engine, event, select

from backend.config.v3 import V3_DATA_GENERATION
from backend.storage.v3.errors import (
    StoreNotInitializedError,
    V3DataGenerationMismatchError,
    V3SchemaVersionError,
)
from backend.storage.v3.schema import app_metadata


class V3Database:
    def __init__(
        self,
        db_path: Path,
        *,
        expected_generation: str = V3_DATA_GENERATION,
        busy_timeout_ms: int = 30_000,
    ) -> None:
        self.db_path = Path(db_path).expanduser().resolve()
        self.expected_generation = str(expected_generation).strip() or V3_DATA_GENERATION
        self.busy_timeout_ms = int(busy_timeout_ms)
        if self.busy_timeout_ms <= 0:
            raise ValueError("busy_timeout_ms must be positive")
        self._engine: Engine | None = None
        self._initialized = False

    @property
    def engine(self) -> Engine:
        if not self._initialized or self._engine is None:
            raise StoreNotInitializedError("v3 store is not initialized")
        return self._engine

    def initialize(self) -> dict[str, Any]:
        if self._initialized:
            return self.info()

        _validate_existing_generation(self.db_path, self.expected_generation)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        engine = _create_sqlite_engine(self.db_path, self.busy_timeout_ms)
        try:
            _upgrade_to_head(engine, self.db_path)
            self._engine = engine
            self._initialized = True
            info = self.info()
            if info["data_generation"] != self.expected_generation:
                raise V3DataGenerationMismatchError(
                    "v3 migration did not create the expected data generation marker"
                )
            if info["alembic_revision"] != info["alembic_head"]:
                raise V3SchemaVersionError(
                    "v3 database revision does not match the application migration head"
                )
            return info
        except BaseException:
            engine.dispose()
            self._engine = None
            self._initialized = False
            raise

    def close(self) -> dict[str, bool]:
        if self._engine is not None:
            self._engine.dispose()
        self._engine = None
        self._initialized = False
        return {"closed": True}

    def info(self) -> dict[str, Any]:
        engine = self.engine
        with engine.connect() as connection:
            metadata_rows = {
                str(row.key): str(row.value)
                for row in connection.execute(
                    select(app_metadata.c.key, app_metadata.c.value)
                )
            }
            revision = connection.exec_driver_sql(
                "SELECT version_num FROM alembic_version"
            ).scalar_one_or_none()
            journal_mode = str(
                connection.exec_driver_sql("PRAGMA journal_mode").scalar_one()
            ).lower()
            foreign_keys = int(
                connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one()
            )
            busy_timeout = int(
                connection.exec_driver_sql("PRAGMA busy_timeout").scalar_one()
            )
        return {
            "db_path": str(self.db_path),
            "data_generation": metadata_rows.get("data_generation", ""),
            "schema_version": metadata_rows.get("schema_version", ""),
            "alembic_revision": str(revision or ""),
            "alembic_head": _alembic_head(self.db_path),
            "journal_mode": journal_mode,
            "foreign_keys": foreign_keys,
            "busy_timeout_ms": busy_timeout,
        }

    @contextmanager
    def read_connection(self) -> Iterator[Connection]:
        with self.engine.connect() as connection:
            yield connection

    @contextmanager
    def transaction(self, *, immediate: bool = True) -> Iterator[Connection]:
        connection = self.engine.connect()
        try:
            if immediate:
                connection.exec_driver_sql("BEGIN IMMEDIATE")
            else:
                connection.begin()
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()


def _create_sqlite_engine(db_path: Path, busy_timeout_ms: int) -> Engine:
    url = URL.create("sqlite+pysqlite", database=str(db_path))
    engine = create_engine(
        url,
        future=True,
        connect_args={
            "timeout": busy_timeout_ms / 1000,
            "check_same_thread": False,
        },
        pool_pre_ping=True,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute(f"PRAGMA busy_timeout = {busy_timeout_ms}")
            cursor.execute("PRAGMA journal_mode = WAL")
            cursor.fetchone()
            cursor.execute("PRAGMA synchronous = NORMAL")
        finally:
            cursor.close()

    return engine


def _validate_existing_generation(db_path: Path, expected_generation: str) -> None:
    if not db_path.exists() or db_path.stat().st_size == 0:
        return

    try:
        uri = f"{db_path.resolve().as_uri()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as connection:
            tables = {
                str(row[0])
                for row in connection.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                    """
                ).fetchall()
            }
            if not tables:
                return
            if "app_metadata" not in tables:
                raise V3DataGenerationMismatchError(
                    "v3 data root points to an existing unmarked database; refusing to modify it"
                )
            row = connection.execute(
                "SELECT value FROM app_metadata WHERE key = 'data_generation'"
            ).fetchone()
            actual_generation = str(row[0]) if row else ""
            if actual_generation != expected_generation:
                raise V3DataGenerationMismatchError(
                    "v3 data root has data generation "
                    f"{actual_generation or 'unmarked'}; expected {expected_generation}"
                )
            if "alembic_version" not in tables:
                raise V3SchemaVersionError(
                    "marked v3 database is missing Alembic revision state"
                )
    except (V3DataGenerationMismatchError, V3SchemaVersionError):
        raise
    except (OSError, sqlite3.DatabaseError) as exc:
        raise V3DataGenerationMismatchError(
            "v3 data root is not a readable v3 SQLite database"
        ) from exc


def _alembic_config(db_path: Path) -> Config:
    backend_root = Path(__file__).resolve().parents[2]
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option(
        "script_location",
        str(Path(__file__).resolve().parent / "migrations"),
    )
    url = URL.create("sqlite+pysqlite", database=str(db_path))
    config.set_main_option(
        "sqlalchemy.url",
        url.render_as_string(hide_password=False).replace("%", "%%"),
    )
    return config


def _upgrade_to_head(engine: Engine, db_path: Path) -> None:
    config = _alembic_config(db_path)
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")


def _alembic_head(db_path: Path) -> str:
    return str(ScriptDirectory.from_config(_alembic_config(db_path)).get_current_head() or "")


__all__ = ["V3Database"]
