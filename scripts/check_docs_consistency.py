"""
check_docs_consistency.py — 轻量文档一致性检查。

当前检查项：
1. docs/devlog/ 目录是否存在，且日期日志文件命名符合 YYYY-MM-DD.md。
2. docs/README.md 存在时，校验其目录说明与实际路径是否一致。

退出码：
    0  - 通过
    2  - 发现不一致
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = PROJECT_ROOT / "docs"
DEVLOG_DIR = DOCS_ROOT / "devlog"
DOCS_README = DOCS_ROOT / "README.md"
DAILY_DEVLOG_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}\.md")


@dataclass
class Issue:
    """文档一致性问题。"""

    location: str
    message: str


def _iter_daily_devlog_files() -> list[Path]:
    if not DEVLOG_DIR.exists():
        return []
    return sorted(
        p
        for p in DEVLOG_DIR.glob("*.md")
        if DAILY_DEVLOG_PATTERN.fullmatch(p.name) and p.is_file()
    )


def _check_devlog_directory() -> list[Issue]:
    issues: list[Issue] = []
    if not DEVLOG_DIR.exists():
        return [
            Issue(
                "docs/devlog/",
                "docs/devlog/ 不存在，无法校验开发过程日志目录。",
            )
        ]

    if not _iter_daily_devlog_files():
        issues.append(Issue("docs/devlog/", "未检测到 YYYY-MM-DD.md 日期日志文件。"))

    return issues


def _extract_docs_readme_refs(lines: Iterable[str]) -> list[str]:
    in_table = False
    paths: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## 2. 目录说明"):
            in_table = True
            continue
        if in_table:
            if stripped.startswith("|"):
                parts = [item.strip() for item in stripped.split("|")]
                if len(parts) < 3:
                    continue
                raw_path = parts[1].strip()
                if raw_path in {"路径", "--", ""}:
                    continue
                if raw_path.startswith("`") and raw_path.endswith("`"):
                    raw_path = raw_path.strip("`")
                if raw_path == "../README.md":
                    paths.append("README.md")
                    continue
                paths.append(raw_path)
            elif stripped == "":
                in_table = False
    return paths


def _check_docs_readme_paths() -> list[Issue]:
    if not DOCS_README.exists():
        return []

    lines = DOCS_README.read_text(encoding="utf-8").splitlines()
    issues: list[Issue] = []
    for rel in _extract_docs_readme_refs(lines):
        target = (DOCS_ROOT / rel).resolve()
        if not target.exists():
            issues.append(Issue("docs/README.md", f"目录说明引用了不存在路径：{rel}"))
    return issues


def run_checks() -> tuple[int, list[Issue]]:
    """执行文档一致性检查，返回 (exit_code, issues)。"""
    devlog_issues = _check_devlog_directory()
    docs_readme_issues = _check_docs_readme_paths()
    all_issues = [*devlog_issues, *docs_readme_issues]
    return (2 if all_issues else 0), all_issues


def main() -> int:
    code, issues = run_checks()
    if not issues:
        print("[PASS] docs consistency checks passed.")
        return 0

    print(f"[FAIL] docs consistency checks failed: {len(issues)} issue(s).")
    for issue in issues:
        print(f"  - {issue.location}: {issue.message}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
