from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class AnalysisResult:
    total_files: int
    top_suffixes: List[str]
    detected_stack: List[str]
    key_files: List[str]
    summary: str


class AnalysisService:
    STACK_HINTS: Dict[str, List[str]] = {
        "Python": ["requirements.txt", "pyproject.toml", ".py"],
        "FastAPI": ["fastapi", "uvicorn"],
        "Vue": ["package.json", "vite.config", ".vue"],
        "TypeScript": [".ts", "tsconfig.json"],
        "Java": [".java", "pom.xml", "build.gradle"],
        "SQLite": ["sqlite", ".db"],
    }

    def analyze(self, root_path: str, max_files: int = 1200) -> AnalysisResult:
        root = Path(root_path)
        if not root.exists():
            return AnalysisResult(0, [], [], [], "目录不存在，无法分析。")

        all_files = [p for p in root.rglob("*") if p.is_file()]
        sampled = all_files[:max_files]
        suffix_counter = Counter(p.suffix.lower() or "(no suffix)" for p in sampled)

        key_files = []
        for name in ("README.md", "requirements.txt", "pyproject.toml", "package.json", "vite.config.ts", "pom.xml"):
            candidate = root / name
            if candidate.exists():
                key_files.append(str(candidate))

        detected = set()
        lower_paths = [str(p).lower() for p in sampled]
        for stack, hints in self.STACK_HINTS.items():
            for h in hints:
                if h.startswith("."):
                    if any(path.endswith(h.lower()) for path in lower_paths):
                        detected.add(stack)
                        break
                else:
                    if any(h.lower() in path for path in lower_paths):
                        detected.add(stack)
                        break

        top_suffixes = [f"{k}: {v}" for k, v in suffix_counter.most_common(8)]
        stack_list = sorted(detected)
        summary = (
            f"扫描文件数: {len(sampled)} / {len(all_files)}\n"
            f"技术栈候选: {', '.join(stack_list) if stack_list else '未识别'}\n"
            f"关键文件命中: {len(key_files)}"
        )
        return AnalysisResult(
            total_files=len(sampled),
            top_suffixes=top_suffixes,
            detected_stack=stack_list,
            key_files=key_files,
            summary=summary,
        )
