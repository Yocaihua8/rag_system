"""
check_docs_consistency.py — Knowledge Island 文档结构一致性检查。

当前检查项：
1. dated DevLog 必须位于 docs/devlog/YYYY/MM/，并由 docs/devlog/README.md 索引；
2. docs/features/README.md 必须索引全部非模板功能文档；
3. docs/adr/README.md 必须索引全部真实 ADR；
4. docs/README.md 的目录说明必须包含并指向核心文档目录；
5. 正式需求、设计、功能和指南文档必须包含项目约定的元数据。

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
DEVLOG_DIR = DOCS_ROOT / "devlog"
DEVLOG_INDEX = DEVLOG_DIR / "README.md"
FEATURES_DIR = DOCS_ROOT / "features"
FEATURES_INDEX = FEATURES_DIR / "README.md"
ADR_DIR = DOCS_ROOT / "adr"
ADR_INDEX = ADR_DIR / "README.md"
DOCS_README = DOCS_ROOT / "README.md"

DAILY_DEVLOG_NAME = re.compile(r"(?P<year>\d{4})-(?P<month>\d{2})-\d{2}\.md")
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\((?P<target>[^)]+)\)")
DEVLOG_LINK = re.compile(r"\[(?P<date>\d{4}-\d{2}-\d{2})\]\((?P<target>[^)#]+)(?:#[^)]*)?\)")

DOCS_README_REQUIRED = (
    "requirements",
    "design",
    "features",
    "guides",
    "adr",
    "devlog",
    "plans",
    "release",
    "architecture",
    "superpowers",
    "previews",
    "glossary.md",
    "BACKLOG.md",
    "style-guide.md",
)

FORMAL_DOC_DIRS = (
    DOCS_ROOT / "requirements",
    DOCS_ROOT / "design",
    DOCS_ROOT / "features",
    DOCS_ROOT / "guides",
)
METADATA_EXCLUDED_NAMES = {
    "ADR-000-template.md",
    "contributor-guide-template.md",
    "feature-template.md",
    "integration-guide-template.md",
    "migration-guide-template.md",
    "rfc-template.md",
}
REQUIRED_METADATA = ("状态", "Owner", "Last Updated", "Scope", "Related")


@dataclass
class Issue:
    """文档一致性问题。"""

    location: str
    message: str


def _display(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def _iter_daily_devlog_files() -> list[Path]:
    if not DEVLOG_DIR.exists():
        return []
    return sorted(
        path
        for path in DEVLOG_DIR.rglob("*.md")
        if path.is_file() and DAILY_DEVLOG_NAME.fullmatch(path.name)
    )


def _normalize_link_target(index_path: Path, raw_target: str) -> Path | None:
    target = raw_target.strip().strip("<>")
    target = target.split("#", 1)[0].strip()
    if not target or target.startswith(("http://", "https://", "mailto:")):
        return None
    return (index_path.parent / target).resolve()


def _linked_local_paths(index_path: Path) -> set[Path]:
    if not index_path.exists():
        return set()
    linked: set[Path] = set()
    for match in MARKDOWN_LINK.finditer(index_path.read_text(encoding="utf-8")):
        target = _normalize_link_target(index_path, match.group("target"))
        if target is not None:
            linked.add(target)
    return linked


def _check_devlog_index() -> list[Issue]:
    issues: list[Issue] = []
    daily_files = _iter_daily_devlog_files()
    if not DEVLOG_INDEX.exists():
        return [Issue(_display(DEVLOG_INDEX), "缺少 DevLog 年月索引。")]

    index_text = DEVLOG_INDEX.read_text(encoding="utf-8")
    linked_files = _linked_local_paths(DEVLOG_INDEX)

    for path in daily_files:
        match = DAILY_DEVLOG_NAME.fullmatch(path.name)
        assert match is not None
        expected = DEVLOG_DIR / match.group("year") / match.group("month") / path.name
        if path.resolve() != expected.resolve():
            issues.append(
                Issue(
                    _display(path),
                    f"日期日志必须归档到 {_display(expected)}。",
                )
            )
        if path.resolve() not in linked_files:
            issues.append(Issue(_display(path), "未在 docs/devlog/README.md 中索引。"))

    indexed_dates: set[str] = set()
    for match in DEVLOG_LINK.finditer(index_text):
        date = match.group("date")
        target = _normalize_link_target(DEVLOG_INDEX, match.group("target"))
        if target is None:
            continue
        if target.name != f"{date}.md":
            issues.append(
                Issue(
                    _display(DEVLOG_INDEX),
                    f"索引标签与目标文件不一致：{date} -> {match.group('target')}",
                )
            )
        if date in indexed_dates:
            issues.append(Issue(_display(DEVLOG_INDEX), f"日期日志重复索引：{date}"))
        indexed_dates.add(date)

    return issues


def _check_complete_index(
    *,
    index_path: Path,
    expected_files: Iterable[Path],
    description: str,
) -> list[Issue]:
    if not index_path.exists():
        return [Issue(_display(index_path), f"缺少{description}索引。")]
    linked = _linked_local_paths(index_path)
    return [
        Issue(_display(path), f"未在 {_display(index_path)} 中索引。")
        for path in sorted(expected_files)
        if path.resolve() not in linked
    ]


def _check_feature_index() -> list[Issue]:
    expected = (
        path
        for path in FEATURES_DIR.glob("*.md")
        if path.name not in {"README.md", "feature-template.md"}
    )
    return _check_complete_index(
        index_path=FEATURES_INDEX,
        expected_files=expected,
        description="功能文档",
    )


def _check_adr_index() -> list[Issue]:
    expected = (
        path
        for path in ADR_DIR.glob("ADR-[0-9][0-9][0-9]-*.md")
        if path.name != "ADR-000-template.md"
    )
    return _check_complete_index(
        index_path=ADR_INDEX,
        expected_files=expected,
        description="ADR",
    )


def _extract_docs_readme_directory_refs(lines: Iterable[str]) -> list[str]:
    in_table = False
    refs: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## 4. 目录说明"):
            in_table = True
            continue
        if in_table and stripped.startswith("## "):
            break
        if not in_table or not stripped.startswith("|"):
            continue
        parts = [item.strip() for item in stripped.split("|")]
        if len(parts) < 3:
            continue
        match = MARKDOWN_LINK.search(parts[1])
        if match:
            refs.append(match.group("target").rstrip("/"))
    return refs


def _check_docs_readme_paths() -> list[Issue]:
    if not DOCS_README.exists():
        return [Issue(_display(DOCS_README), "缺少文档总览。")]

    refs = _extract_docs_readme_directory_refs(
        DOCS_README.read_text(encoding="utf-8").splitlines()
    )
    issues: list[Issue] = []
    for required in DOCS_README_REQUIRED:
        if required not in refs:
            issues.append(
                Issue(
                    _display(DOCS_README),
                    f"目录说明缺少核心路径：{required}",
                )
            )
    for ref in refs:
        target = (DOCS_ROOT / ref).resolve()
        if not target.exists():
            issues.append(
                Issue(
                    _display(DOCS_README),
                    f"目录说明引用了不存在路径：{ref}",
                )
            )
    return issues


def _iter_formal_docs() -> Iterable[Path]:
    yield DOCS_README
    yield DOCS_ROOT / "glossary.md"
    for directory in FORMAL_DOC_DIRS:
        for path in sorted(directory.glob("*.md")):
            if path.name not in METADATA_EXCLUDED_NAMES:
                yield path


def _check_formal_metadata() -> list[Issue]:
    issues: list[Issue] = []
    for path in _iter_formal_docs():
        if not path.exists():
            issues.append(Issue(_display(path), "正式文档缺失。"))
            continue
        head = "\n".join(path.read_text(encoding="utf-8").splitlines()[:12])
        for field in REQUIRED_METADATA:
            if not re.search(rf"^>\s*{re.escape(field)}[：:]", head, flags=re.MULTILINE):
                issues.append(Issue(_display(path), f"缺少元数据字段：{field}"))
    return issues


def run_checks() -> tuple[int, list[Issue]]:
    """执行文档一致性检查，返回 (exit_code, issues)。"""

    all_issues = [
        *_check_devlog_index(),
        *_check_feature_index(),
        *_check_adr_index(),
        *_check_docs_readme_paths(),
        *_check_formal_metadata(),
    ]
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
