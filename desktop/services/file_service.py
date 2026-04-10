from __future__ import annotations

from pathlib import Path


class FileService:
    def ensure_dir(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
