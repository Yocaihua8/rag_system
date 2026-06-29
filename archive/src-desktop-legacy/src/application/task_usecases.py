from __future__ import annotations

from typing import List

from src.domain.errors import NotFoundError
from src.domain.models.task import Task
from src.ports.task_store import ITaskStore


class TaskUseCases:

    def __init__(self, store: ITaskStore) -> None:
        self._store = store

    def get(self, task_id: str) -> Task:
        task = self._store.get(task_id)
        if task is None:
            raise NotFoundError("Task", task_id)
        return task

    def list_recent(self, limit: int = 20) -> List[Task]:
        return self._store.list_recent(limit)
