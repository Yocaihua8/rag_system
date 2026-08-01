"""Knowledge Island current-document consistency checks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = PROJECT_ROOT / "docs"
DOCS_README = DOCS_ROOT / "README.md"
BACKLOG = DOCS_ROOT / "BACKLOG.md"
ADR_DIR = DOCS_ROOT / "architecture" / "decisions"
ADR_INDEX = ADR_DIR / "README.md"

REQUIRED_DIRECTORIES = (
    "product",
    "architecture/backend",
    "architecture/frontend",
    "architecture/contracts",
    "architecture/decisions",
    "integrations",
    "operations",
    "governance/plans",
    "governance/templates",
)
FORMAL_DOC_DIRECTORIES = (
    DOCS_ROOT / "product",
    DOCS_ROOT / "architecture" / "backend",
    DOCS_ROOT / "architecture" / "frontend",
    DOCS_ROOT / "architecture" / "contracts",
    DOCS_ROOT / "integrations",
    DOCS_ROOT / "operations",
)
REQUIRED_METADATA = ("状态", "Owner", "Last Updated", "Scope", "Related")
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\((?P<target>[^)]+)\)")
DISALLOWED_ACTIVE_REFERENCES = (
    "docs/devlog/",
    "docs/release/",
    "docs/previews/",
    "docs/superpowers/",
    "docs/design/",
    "docs/features/",
    "docs/guides/",
    "docs/adr/",
    "docs/requirements/",
    "archive/src-desktop-legacy/",
    "backend/static_dist/",
    "python app.py",
    "requirements.txt",
)


@dataclass(frozen=True)
class Issue:
    location: str
    message: str


def _display(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def _linked_local_paths(index_path: Path) -> set[Path]:
    if not index_path.exists():
        return set()
    linked: set[Path] = set()
    for match in MARKDOWN_LINK.finditer(index_path.read_text(encoding="utf-8")):
        target = match.group("target").strip().strip("<>").split("#", 1)[0]
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        linked.add((index_path.parent / target).resolve())
    return linked


def _check_required_directories() -> list[Issue]:
    issues: list[Issue] = []
    readme_text = DOCS_README.read_text(encoding="utf-8") if DOCS_README.exists() else ""
    for relative in REQUIRED_DIRECTORIES:
        target = DOCS_ROOT / relative
        if not target.is_dir():
            issues.append(Issue(_display(target), "缺少文档分类目录。"))
        if relative not in readme_text:
            issues.append(Issue(_display(DOCS_README), f"索引未包含目录：{relative}"))
    return issues


def _check_adr_index() -> list[Issue]:
    expected = {
        path.resolve()
        for path in ADR_DIR.glob("ADR-[0-9][0-9][0-9]-*.md")
        if path.name != "ADR-000-template.md"
    }
    if not ADR_INDEX.exists():
        return [Issue(_display(ADR_INDEX), "缺少 ADR 索引。")]
    linked = _linked_local_paths(ADR_INDEX)
    return [
        Issue(_display(path), f"未在 {_display(ADR_INDEX)} 中索引。")
        for path in sorted(expected - linked)
    ]


def _iter_formal_docs() -> Iterable[Path]:
    yield DOCS_README
    for directory in FORMAL_DOC_DIRECTORIES:
        yield from sorted(directory.glob("*.md"))


def _check_formal_metadata() -> list[Issue]:
    issues: list[Issue] = []
    for path in _iter_formal_docs():
        if not path.exists() or path.name == "README.md" or "template" in path.name.lower():
            continue
        head = "\n".join(path.read_text(encoding="utf-8").splitlines()[:14])
        for field in REQUIRED_METADATA:
            if not re.search(rf"^>\s*{re.escape(field)}[：:]", head, flags=re.MULTILINE):
                issues.append(Issue(_display(path), f"缺少元数据字段：{field}"))
    return issues


def _check_active_references() -> list[Issue]:
    issues: list[Issue] = []
    active_files = [
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / "AGENTS.md",
        PROJECT_ROOT / "CONTRIBUTING.md",
        DOCS_README,
        BACKLOG,
        *[
            path
            for path in DOCS_ROOT.rglob("*.md")
            if "governance/plans" not in path.as_posix()
        ],
    ]
    for path in active_files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for stale in DISALLOWED_ACTIVE_REFERENCES:
            if stale in text:
                issues.append(Issue(_display(path), f"仍引用已删除路径或命令：{stale}"))
    return issues


def _check_backlog_is_active_only() -> list[Issue]:
    if not BACKLOG.exists():
        return [Issue(_display(BACKLOG), "缺少活动事项清单。")]
    issues: list[Issue] = []
    for line_number, line in enumerate(BACKLOG.read_text(encoding="utf-8").splitlines(), start=1):
        if re.match(r"^\|\s*B-\d+\s*\|", line) and re.search(
            r"\|\s*(?:done|wontfix)\s*\|", line, flags=re.IGNORECASE
        ):
            issues.append(Issue(f"{_display(BACKLOG)}:{line_number}", "BACKLOG 只能保留未完成事项。"))
    return issues


def run_checks() -> tuple[int, list[Issue]]:
    issues = [
        *_check_required_directories(),
        *_check_adr_index(),
        *_check_formal_metadata(),
        *_check_active_references(),
        *_check_backlog_is_active_only(),
    ]
    return (2 if issues else 0), issues


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
