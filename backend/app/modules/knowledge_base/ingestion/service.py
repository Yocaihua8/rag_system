from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class IngestionResult:
    total_files: int
    supported_files: int
    skipped_files: int


class IngestionService:
    SUPPORTED_SUFFIXES = {".md", ".txt", ".pdf", ".docx", ".json", ".yaml", ".yml", ".py", ".ts", ".java"}
    TEXT_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml", ".py", ".ts", ".java"}

    def scan(self, root_path: str) -> IngestionResult:
        root = Path(root_path)
        if not root.exists():
            return IngestionResult(total_files=0, supported_files=0, skipped_files=0)

        files: List[Path] = [p for p in root.rglob("*") if p.is_file()]
        supported = [p for p in files if p.suffix.lower() in self.SUPPORTED_SUFFIXES]
        skipped = len(files) - len(supported)
        return IngestionResult(total_files=len(files), supported_files=len(supported), skipped_files=skipped)

    def collect_supported_files(self, root_path: str) -> List[Path]:
        root = Path(root_path)
        if not root.exists():
            return []
        files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in self.SUPPORTED_SUFFIXES]
        return sorted(files)

    def load_text_corpus(self, root_path: str, limit: int = 400) -> List[str]:
        corpus: List[str] = []
        for path in self.collect_supported_files(root_path):
            if path.suffix.lower() not in self.TEXT_SUFFIXES:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore").strip()
            except OSError:
                continue
            if text:
                corpus.append(text[:6000])
            if len(corpus) >= limit:
                break
        return corpus
