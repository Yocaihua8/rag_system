from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ACTIVE_DIRS = [
    PROJECT_ROOT / "desktop",
    PROJECT_ROOT / "backend",
    PROJECT_ROOT / "scripts",
]
BLOCKED_IMPORT_PREFIXES = (
    "from core",
    "import core",
    "from infra",
    "import infra",
    "from app.qt",
    "import app.qt",
)


def _iter_python_files() -> list[Path]:
    files: list[Path] = []
    for base in ACTIVE_DIRS:
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            if "__pycache__" in p.parts:
                continue
            files.append(p)
    return files


def main() -> int:
    violations: list[str] = []
    for file_path in _iter_python_files():
        try:
            lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for idx, line in enumerate(lines, start=1):
            text = line.strip()
            if text.startswith("#"):
                continue
            if any(text.startswith(prefix) for prefix in BLOCKED_IMPORT_PREFIXES):
                rel = file_path.relative_to(PROJECT_ROOT)
                violations.append(f"{rel}:{idx} -> {text}")

    if violations:
        print("[FAIL] 检测到主链路使用旧导入路径：")
        for item in violations:
            print(f"- {item}")
        return 2

    print("[OK] 导入路径检查通过：主链路未使用 core/infra/app.qt 旧导入。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
