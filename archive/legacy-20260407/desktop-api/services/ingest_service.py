import shutil
from pathlib import Path
from typing import Dict, List, Optional

from app.config import RAW_PATH


class IngestService:
    def __init__(self, raw_path: Path = RAW_PATH) -> None:
        self.raw_path = raw_path

    def import_paths(self, paths: List[str]) -> Dict:
        self.raw_path.mkdir(parents=True, exist_ok=True)

        imported = []
        skipped = []
        errors = []
        candidates = self._collect_candidates(paths)

        for src in candidates:
            try:
                target = self._copy_markdown(src)
                if target is None:
                    skipped.append({"path": str(src), "reason": "not_markdown"})
                    continue
                imported.append({"src": str(src), "dst": str(target)})
            except Exception as ex:
                errors.append({"path": str(src), "reason": str(ex)})

        return {
            "imported_count": len(imported),
            "skipped_count": len(skipped),
            "error_count": len(errors),
            "imported": imported,
            "skipped": skipped,
            "errors": errors,
        }

    def _collect_candidates(self, paths: List[str]) -> List[Path]:
        candidates: List[Path] = []
        for item in paths:
            path = Path(item)
            if not path.exists():
                continue
            if path.is_dir():
                candidates.extend(sorted(path.rglob("*.md")))
            else:
                candidates.append(path)
        return candidates

    def _copy_markdown(self, source: Path) -> Optional[Path]:
        if source.suffix.lower() != ".md":
            return None
        destination = self._resolve_collision(self.raw_path / source.name)
        shutil.copy2(source, destination)
        return destination

    @staticmethod
    def _resolve_collision(target: Path) -> Path:
        if not target.exists():
            return target
        base = target.stem
        suffix = target.suffix
        i = 1
        while True:
            next_target = target.with_name(f"{base}_{i}{suffix}")
            if not next_target.exists():
                return next_target
            i += 1
