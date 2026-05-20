"""
check_docs_consistency.py — 轻量文档一致性检查。

当前检查项：
1. docs/DEVLOG.md 中的 devlog/日期 日志链接是否存在。
2. docs/devlog/*.md 的日期日志文件是否都出现在 DEVLOG 索引中。
3. docs/README.md 存在时，校验其目录说明与实际路径是否一致。

退出码：
    0  - 通过
    2  - 发现不一致
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = PROJECT_ROOT / "docs"
DEVLOG_AGG = DOCS_ROOT / "DEVLOG.md"
DEVLOG_DIR = DOCS_ROOT / "devlog"
DOCS_README = DOCS_ROOT / "README.md"


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
        if p.name != "README.md" and p.is_file()
    )


def _extract_devlog_links(lines: Iterable[str]) -> list[tuple[str, str, int]]:
    pattern = re.compile(r"\[(\d{4}-\d{2}-\d{2})\]\(([^)]+)\)")
    links: list[tuple[str, str, int]] = []
    for idx, line in enumerate(lines, start=1):
        for match in pattern.finditer(line):
            date, rel_path = match.group(1), match.group(2)
            links.append((date, rel_path, idx))
    return links


def _check_devlog_links() -> list[Issue]:
    issues: list[Issue] = []
    if not DEVLOG_AGG.exists():
        return [
            Issue(
                "docs/DEVLOG.md",
                "docs/DEVLOG.md 不存在，无法校验聚合索引。",
            )
        ]

    lines = DEVLOG_AGG.read_text(encoding="utf-8").splitlines()
    links = _extract_devlog_links(lines)
    if not links:
        issues.append(Issue("docs/DEVLOG.md", "未检测到 devlog 日志链接。"))

    linked_files = set[str]()
    for date, rel_path, line_no in links:
        target = (DOCS_ROOT / rel_path).resolve()
        rel_name = f"devlog/{Path(rel_path).name}"
        if not target.exists():
            issues.append(
                Issue(
                    f"docs/DEVLOG.md:{line_no}",
                    f"日期文件缺失：{rel_name}（{target}）",
                )
            )
        else:
            linked_files.add(Path(rel_path).name)
        if date not in rel_path:
            issues.append(
                Issue(
                    f"docs/DEVLOG.md:{line_no}",
                    f"链接名称与日期不一致：{date} -> {rel_path}",
                )
            )

    # 校验 devlog 目录中每个日期文件都有索引条目
    for p in _iter_daily_devlog_files():
        if p.name not in linked_files:
            issues.append(
                Issue(
                    str(p.relative_to(PROJECT_ROOT)),
                    f"未在 DEVLOG 索引中链接：{p.relative_to(PROJECT_ROOT)}",
                )
            )

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
    devlog_issues = _check_devlog_links()
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
