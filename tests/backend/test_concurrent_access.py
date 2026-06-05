import threading
import sqlite3

from backend.knowledge_island.storage import KnowledgeStore


def test_sqlite_connections_enable_wal_and_busy_timeout(tmp_path):
    store = KnowledgeStore(tmp_path / "test.db")

    with store._connect() as conn:
        journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        synchronous = conn.execute("PRAGMA synchronous").fetchone()[0]
        busy_timeout = conn.execute("PRAGMA busy_timeout").fetchone()[0]

    assert journal_mode.lower() == "wal"
    assert synchronous == 1
    assert busy_timeout == 5000


def test_concurrent_read_write(tmp_path):
    store = KnowledgeStore(tmp_path / "test.db")
    errors = []

    def writer():
        try:
            store.create_project("test", tmp_path)
        except Exception as exc:
            errors.append(exc)

    def reader():
        try:
            store.list_projects()
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=writer)] + [
        threading.Thread(target=reader) for _ in range(5)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    locked_errors = [
        exc
        for exc in errors
        if isinstance(exc, sqlite3.OperationalError) and "database is locked" in str(exc)
    ]
    assert not locked_errors
    assert not errors
