from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from threading import Lock


class ProjectIndexingCoordinator:
    def __init__(self) -> None:
        self._guard = Lock()
        self._project_locks: dict[str, Lock] = {}

    @contextmanager
    def project_scope(self, project_id: str) -> Iterator[None]:
        project_lock = self._lock_for(project_id)
        project_lock.acquire()
        try:
            yield
        finally:
            project_lock.release()

    def _lock_for(self, project_id: str) -> Lock:
        clean_project_id = str(project_id)
        with self._guard:
            lock = self._project_locks.get(clean_project_id)
            if lock is None:
                lock = Lock()
                self._project_locks[clean_project_id] = lock
            return lock


default_indexing_coordinator = ProjectIndexingCoordinator()
