"""
check_import_paths.py — 检查活动 Web/backend 代码中是否存在 legacy import。

用法：
    py -3 scripts/check_import_paths.py

退出码：
    0  通过
    2  发现违规 import
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 扫描范围：当前活动代码目录
ACTIVE_DIRS = [
    PROJECT_ROOT / "backend",
    PROJECT_ROOT / "scripts",
]

# 禁止出现的 legacy import 前缀
BLOCKED_IMPORT_PREFIXES = (
    "from src.",
    "import src.",
    "from desktop.",
    "import desktop.",
    "from core",
    "import core",
    "from infra",
    "import infra",
    "from app.qt",
    "import app.qt",
    "from desktop.app",
    "from desktop.ui",
    "from desktop.services",
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
                violations.append(f"{rel}:{idx}  {text}")

    if violations:
        print(f"[FAIL] 检测到 {len(violations)} 处旧架构 import：")
        for item in violations:
            print(f"  - {item}")
        return 2

    py_count = len(_iter_python_files())
    print(f"[OK] 导入路径检查通过：已扫描 {py_count} 个文件，无旧架构引用。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
