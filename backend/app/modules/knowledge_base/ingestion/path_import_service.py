from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class ImportItem:
    src: str
    dst: str


@dataclass
class PathImportResult:
    imported: List[ImportItem]
    skipped: List[str]
    errors: List[str]

    @property
    def imported_count(self) -> int:
        return len(self.imported)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped)

    @property
    def error_count(self) -> int:
        return len(self.errors)


class PathImportService:
    """Import markdown files from given files/directories into a target directory."""

    def import_markdown_paths(self, paths: List[str], target_dir: str) -> PathImportResult:
        target = Path(target_dir)
        target.mkdir(parents=True, exist_ok=True)

        imported: List[ImportItem] = []
        skipped: List[str] = []
        errors: List[str] = []

        for src in self._collect_candidates(paths):
            if src.suffix.lower() != ".md":
                skipped.append(f"{src} | not_markdown")
                continue
            try:
                dst = self._copy_with_collision(src, target)
                imported.append(ImportItem(src=str(src), dst=str(dst)))
            except Exception as ex:  # pragma: no cover - best effort import
                errors.append(f"{src} | {ex}")

        return PathImportResult(imported=imported, skipped=skipped, errors=errors)

    def _collect_candidates(self, paths: List[str]) -> List[Path]:
        result: List[Path] = []
        for item in paths:
            p = Path(item)
            if not p.exists():
                continue
            if p.is_dir():
                result.extend(sorted(p.rglob("*.md")))
            else:
                result.append(p)
        return result

    def _copy_with_collision(self, src: Path, target_dir: Path) -> Path:
        dst = target_dir / src.name
        if not dst.exists():
            shutil.copy2(src, dst)
            return dst
        stem = dst.stem
        suffix = dst.suffix
        i = 1
        while True:
            candidate = dst.with_name(f"{stem}_{i}{suffix}")
            if not candidate.exists():
                shutil.copy2(src, candidate)
                return candidate
            i += 1

