"""Validate the current Knowledge Island documentation against repository facts."""

from __future__ import annotations

import gc
import json
import re
import sqlite3
import sys
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = PROJECT_ROOT / "docs"
DOCS_README = DOCS_ROOT / "README.md"
BACKLOG = DOCS_ROOT / "BACKLOG.md"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

CANONICAL_DIRECTORIES = (
    "requirements",
    "design",
    "features",
    "adr",
    "guides",
    "devlog",
    "plans",
)
OBSOLETE_PATHS = (
    "docs/product",
    "docs/architecture",
    "docs/integrations",
    "docs/operations",
    "docs/governance",
    "tools/docs",
)
FLAT_DOCUMENT_DIRECTORIES = (
    "requirements",
    "design",
    "features",
    "adr",
    "guides",
    "plans",
)
ACTIVE_DOCUMENT_DIRECTORIES = tuple(
    DOCS_ROOT / name for name in ("requirements", "design", "features", "adr", "guides")
)
DEVLOG_ROOT = DOCS_ROOT / "devlog"
STANDARD_METADATA = ("状态", "Owner", "Last Updated", "Scope", "Related")
ADR_METADATA = ("状态", "Date", "Owner", "Related")
DEVLOG_DAILY_METADATA = ("Author", "Iteration", "Related")
DEVLOG_POSTMORTEM_METADATA = ("状态", "Author", "Date", "Related")
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\((?P<target>[^)]+)\)")
SOURCE_DOC_REFERENCE = re.compile(r"(?<![A-Za-z0-9_.-])(docs/[A-Za-z0-9_./-]+\.md)")
DEVLOG_ENTRY_NAME = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})(?P<postmortem>-[a-z0-9][a-z0-9-]*-postmortem)?\.md$"
)
HTTP_METHODS = {"get", "post"}
EXPECTED_API_PATHS = 90
EXPECTED_API_OPERATIONS = 98
EXPECTED_API_GETS = 32
EXPECTED_API_POSTS = 66
EXPECTED_TABLE_COUNT = 43
EXPECTED_DOCUMENT_FIELDS = (
    "id",
    "project_id",
    "source_path",
    "relative_path",
    "content",
    "checksum",
    "updated_at",
)
FORBIDDEN_DOCUMENT_FIELDS = (
    "workspace_id",
    "source_type",
    "raw_content",
    "normalized_markdown",
    "plain_text",
    "rendered_html",
)
DISALLOWED_ACTIVE_REFERENCES = (
    "docs/product/",
    "docs/architecture/",
    "docs/integrations/",
    "docs/operations/",
    "docs/governance/",
    "docs/release/",
    "docs/previews/",
    "docs/superpowers/",
    "tools/docs/",
    ".docs-template/",
    "template-mapping.md",
    "archive/src-desktop-legacy/",
    "backend/static_dist/",
    "python app.py",
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


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _is_template(path: Path) -> bool:
    lower_name = path.name.lower()
    return "-template" in lower_name or path.name == "ADR-000-template.md"


def _linked_local_paths(index_path: Path) -> set[Path]:
    if not index_path.exists():
        return set()
    linked: set[Path] = set()
    for match in MARKDOWN_LINK.finditer(_read(index_path)):
        target = match.group("target").strip().strip("<>").split("#", 1)[0]
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        linked.add((index_path.parent / target).resolve())
    return linked


def _iter_active_documents() -> Iterable[Path]:
    yield DOCS_README
    for directory in ACTIVE_DOCUMENT_DIRECTORIES:
        for path in sorted(directory.glob("*.md")):
            if not _is_template(path):
                yield path


def _check_structure() -> list[Issue]:
    issues: list[Issue] = []
    readme_text = _read(DOCS_README) if DOCS_README.exists() else ""
    for relative in CANONICAL_DIRECTORIES:
        target = DOCS_ROOT / relative
        if not target.is_dir():
            issues.append(Issue(_display(target), "缺少标准文档目录。"))
            continue
        if f"{relative}/" not in readme_text:
            issues.append(Issue(_display(DOCS_README), f"总索引未包含目录：{relative}/"))
        if relative in FLAT_DOCUMENT_DIRECTORIES:
            nested = [path for path in target.iterdir() if path.is_dir()]
            for path in nested:
                issues.append(Issue(_display(path), "标准文档目录必须保持扁平。"))

    for relative in OBSOLETE_PATHS:
        target = PROJECT_ROOT / relative
        if target.exists():
            issues.append(Issue(_display(target), "旧文档或工具路径仍然存在。"))
    return issues


def _check_devlog_structure() -> list[Issue]:
    issues: list[Issue] = []
    if not DEVLOG_ROOT.is_dir():
        return [Issue(_display(DEVLOG_ROOT), "缺少 DevLog 目录。")]

    allowed_root_files = {"README.md", "devlog-template.md", "postmortem-template.md"}
    for child in sorted(DEVLOG_ROOT.iterdir()):
        if child.is_file():
            if child.name not in allowed_root_files:
                issues.append(Issue(_display(child), "DevLog 根目录只能保存 README 和模板。"))
            continue
        if not child.is_dir() or not re.fullmatch(r"\d{4}", child.name):
            issues.append(Issue(_display(child), "DevLog 一级目录必须是四位年份。"))
            continue

        year = child.name
        for month_dir in sorted(child.iterdir()):
            if not month_dir.is_dir() or not re.fullmatch(r"(?:0[1-9]|1[0-2])", month_dir.name):
                issues.append(Issue(_display(month_dir), "DevLog 二级目录必须是 01-12 月份。"))
                continue

            month = month_dir.name
            for entry in sorted(month_dir.iterdir()):
                if not entry.is_file():
                    issues.append(Issue(_display(entry), "DevLog 月份目录不能继续嵌套。"))
                    continue
                match = DEVLOG_ENTRY_NAME.fullmatch(entry.name)
                if match is None:
                    issues.append(Issue(_display(entry), "DevLog 文件名必须是日报或 postmortem 约定格式。"))
                    continue
                try:
                    entry_date = date.fromisoformat(match.group("date"))
                except ValueError:
                    issues.append(Issue(_display(entry), "DevLog 文件名包含无效日期。"))
                    continue
                if str(entry_date.year) != year or f"{entry_date.month:02d}" != month:
                    issues.append(Issue(_display(entry), "DevLog 文件日期与 YYYY/MM 目录不一致。"))

                text = _read(entry)
                head = "\n".join(text.splitlines()[:16])
                required = (
                    DEVLOG_POSTMORTEM_METADATA
                    if match.group("postmortem")
                    else DEVLOG_DAILY_METADATA
                )
                for field in required:
                    if not re.search(rf"^>\s*{re.escape(field)}[：:]", head, flags=re.MULTILINE):
                        issues.append(Issue(_display(entry), f"缺少 DevLog 元数据字段：{field}"))
                if len(text.splitlines()) > 150:
                    issues.append(Issue(_display(entry), "单份 DevLog 不应超过 150 行。"))
    return issues


def _check_nearest_indexes() -> list[Issue]:
    issues: list[Issue] = []
    for directory in (DOCS_ROOT / name for name in CANONICAL_DIRECTORIES):
        index = directory / "README.md"
        if not index.exists():
            issues.append(Issue(_display(index), "缺少最近一级索引。"))
            continue
        linked = _linked_local_paths(index)
        expected = {
            path.resolve()
            for path in directory.glob("*.md")
            if path.name != "README.md" and not _is_template(path)
        }
        for path in sorted(expected - linked):
            issues.append(Issue(_display(path), f"未被最近一级索引 {_display(index)} 引用。"))
    return issues


def _check_metadata() -> list[Issue]:
    issues: list[Issue] = []
    for path in _iter_active_documents():
        if path.name == "README.md" and path.parent == DOCS_ROOT / "adr":
            required = STANDARD_METADATA
        elif path.parent == DOCS_ROOT / "adr" and path.name.startswith("ADR-"):
            required = ADR_METADATA
        else:
            required = STANDARD_METADATA
        head = "\n".join(_read(path).splitlines()[:16])
        for field in required:
            if not re.search(rf"^>\s*{re.escape(field)}[：:]", head, flags=re.MULTILINE):
                issues.append(Issue(_display(path), f"缺少元数据字段：{field}"))
    return issues


def _active_reference_files() -> list[Path]:
    paths = [
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / "AGENTS.md",
        PROJECT_ROOT / "CONTRIBUTING.md",
        BACKLOG,
        *[path for path in DOCS_ROOT.rglob("*.md") if path.parent != DOCS_ROOT / "plans"],
    ]
    return [path for path in paths if path.exists()]


def _check_active_references() -> list[Issue]:
    issues: list[Issue] = []
    for path in _active_reference_files():
        text = _read(path)
        for stale in DISALLOWED_ACTIVE_REFERENCES:
            if stale in text:
                issues.append(Issue(_display(path), f"仍引用已删除路径或命令：{stale}"))

        if path.parent in {
            DOCS_ROOT / "requirements",
            DOCS_ROOT / "design",
            DOCS_ROOT / "features",
            DOCS_ROOT / "guides",
        } and not _is_template(path):
            if re.search(r"\bB-\d{3,}\b", text):
                issues.append(Issue(_display(path), "活动文档混入 B-ID 实施历史；应改写为当前事实。"))
    return issues


def _check_backlog_is_active_only() -> list[Issue]:
    if not BACKLOG.exists():
        return [Issue(_display(BACKLOG), "缺少活动事项清单。")]
    issues: list[Issue] = []
    for line_number, line in enumerate(_read(BACKLOG).splitlines(), start=1):
        if re.match(r"^\|\s*B-\d+\s*\|", line) and re.search(
            r"\|\s*(?:done|wontfix)\s*\|", line, flags=re.IGNORECASE
        ):
            issues.append(Issue(f"{_display(BACKLOG)}:{line_number}", "BACKLOG 只能保留未完成事项。"))
    return issues


def _openapi_snapshot(database_path: Path) -> tuple[set[str], int, int]:
    from backend.api.server import create_app

    app = create_app(db_path=database_path)
    openapi = app.openapi()
    paths = set(openapi["paths"])
    gets = sum("get" in operations for operations in openapi["paths"].values())
    posts = sum("post" in operations for operations in openapi["paths"].values())
    unexpected = {
        method
        for operations in openapi["paths"].values()
        for method in operations
        if method.lower() in {"put", "patch", "delete"}
    }
    if unexpected:
        raise AssertionError(f"unexpected HTTP methods: {sorted(unexpected)}")
    del app
    gc.collect()
    return paths, gets, posts


def _check_api_contract() -> list[Issue]:
    spec_path = DOCS_ROOT / "design" / "api-spec.md"
    if not spec_path.exists():
        return [Issue(_display(spec_path), "缺少 API 契约。")]
    issues: list[Issue] = []
    with tempfile.TemporaryDirectory(prefix="ki-docs-api-") as temp_dir:
        paths, gets, posts = _openapi_snapshot(Path(temp_dir) / "app.db")
    operations = gets + posts
    if (len(paths), operations, gets, posts) != (
        EXPECTED_API_PATHS,
        EXPECTED_API_OPERATIONS,
        EXPECTED_API_GETS,
        EXPECTED_API_POSTS,
    ):
        issues.append(
            Issue(
                "backend/api/openapi_schema.py",
                "当前 OpenAPI 数量偏离已校准基线："
                f"{len(paths)} paths / {operations} operations / {gets} GET / {posts} POST。",
            )
        )

    spec = _read(spec_path)
    for path in sorted(paths):
        if path.startswith("/api/") and path not in spec:
            issues.append(Issue(_display(spec_path), f"缺少当前 API 路径：{path}"))
    for marker in (
        "90 个唯一路径",
        "98 个操作",
        "32 个 GET",
        "66 个 POST",
        "token",
        "done",
        "answer_error",
    ):
        if marker not in spec:
            issues.append(Issue(_display(spec_path), f"缺少 API 基线标记：{marker}"))
    return issues


def _sqlite_snapshot(database_path: Path) -> tuple[set[str], tuple[str, ...]]:
    from backend.api.server import create_app

    app = create_app(db_path=database_path)
    connection = sqlite3.connect(database_path)
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            )
        }
        document_fields = tuple(
            row[1] for row in connection.execute("PRAGMA table_info(documents)")
        )
    finally:
        connection.close()
    del app
    gc.collect()
    return tables, document_fields


def _check_database_contract() -> list[Issue]:
    spec_path = DOCS_ROOT / "design" / "database-design.md"
    if not spec_path.exists():
        return [Issue(_display(spec_path), "缺少数据库契约。")]
    issues: list[Issue] = []
    with tempfile.TemporaryDirectory(prefix="ki-docs-db-") as temp_dir:
        tables, fields = _sqlite_snapshot(Path(temp_dir) / "app.db")
    if len(tables) != EXPECTED_TABLE_COUNT:
        issues.append(
            Issue(
                "backend/storage/knowledge_store.py",
                f"当前表数量为 {len(tables)}，偏离 43 表文档基线。",
            )
        )
    if fields != EXPECTED_DOCUMENT_FIELDS:
        issues.append(
            Issue(
                "backend/storage/knowledge_store.py",
                f"documents 字段偏离文档基线：{fields}",
            )
        )

    spec = _read(spec_path)
    for table in sorted(tables):
        if f"`{table}`" not in spec:
            issues.append(Issue(_display(spec_path), f"缺少当前 SQLite 表：{table}"))
    for field in fields:
        if f"`{field}`" not in spec:
            issues.append(Issue(_display(spec_path), f"缺少 documents 字段：{field}"))
    for field in FORBIDDEN_DOCUMENT_FIELDS:
        if re.search(rf"documents[^\n]{{0,400}}`{re.escape(field)}`", spec, flags=re.DOTALL):
            issues.append(Issue(_display(spec_path), f"documents 仍包含错误字段：{field}"))
    if "43 张当前表" not in spec:
        issues.append(Issue(_display(spec_path), "缺少 43 张当前表的基线说明。"))
    return issues


def _check_package_and_command_facts() -> list[Issue]:
    issues: list[Issue] = []
    base_requirements = _read(PROJECT_ROOT / "backend" / "requirements" / "base.txt").lower()
    frontend_package = json.loads(_read(PROJECT_ROOT / "frontend" / "package.json"))
    plugin_package = json.loads(
        _read(PROJECT_ROOT / "integrations" / "obsidian-plugin" / "package.json")
    )
    setup = _read(DOCS_ROOT / "guides" / "setup.md")
    testing = _read(DOCS_ROOT / "guides" / "testing.md")
    combined = f"{setup}\n{testing}"

    for dependency in ("qdrant-client", "jieba"):
        if dependency not in base_requirements:
            issues.append(Issue("backend/requirements/base.txt", f"缺少约定依赖：{dependency}"))
        if dependency.lower() not in combined.lower():
            issues.append(Issue("docs/guides/", f"未说明依赖状态：{dependency}"))
    if "pinia" not in frontend_package.get("dependencies", {}):
        issues.append(Issue("frontend/package.json", "Pinia 声明状态发生变化，需同步文档。"))
    for dependency in ("Pinia", "pymupdf", "sentence-transformers"):
        if dependency.lower() not in combined.lower():
            issues.append(Issue("docs/guides/", f"未说明依赖状态：{dependency}"))

    expected_plugin_scripts = {"test", "typecheck", "build"}
    missing_scripts = expected_plugin_scripts - set(plugin_package.get("scripts", {}))
    if missing_scripts:
        issues.append(
            Issue(
                "integrations/obsidian-plugin/package.json",
                f"插件缺少文档要求的脚本：{sorted(missing_scripts)}",
            )
        )
    for command in ("npm test", "npm run typecheck", "npm run build"):
        if command not in testing:
            issues.append(Issue(_display(DOCS_ROOT / "guides" / "testing.md"), f"缺少插件命令：{command}"))
    return issues


def _check_source_doc_references() -> list[Issue]:
    issues: list[Issue] = []
    source_roots = (
        PROJECT_ROOT / "backend",
        PROJECT_ROOT / "frontend",
        PROJECT_ROOT / "src-tauri",
        PROJECT_ROOT / "integrations",
        PROJECT_ROOT / "ops",
    )
    allowed_suffixes = {".py", ".js", ".mjs", ".ts", ".vue", ".rs", ".toml", ".json", ".yml", ".yaml", ".ps1", ".sh"}
    excluded_parts = {"node_modules", "dist", "build", "target", "__pycache__"}
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in allowed_suffixes:
                continue
            if excluded_parts.intersection(path.parts):
                continue
            try:
                text = _read(path)
            except UnicodeDecodeError:
                continue
            for reference in SOURCE_DOC_REFERENCE.findall(text):
                if not (PROJECT_ROOT / reference).is_file():
                    issues.append(Issue(_display(path), f"源码引用的文档不存在：{reference}"))
    return issues


def run_checks() -> tuple[int, list[Issue]]:
    checks = (
        _check_structure,
        _check_devlog_structure,
        _check_nearest_indexes,
        _check_metadata,
        _check_active_references,
        _check_backlog_is_active_only,
        _check_api_contract,
        _check_database_contract,
        _check_package_and_command_facts,
        _check_source_doc_references,
    )
    issues: list[Issue] = []
    for check in checks:
        try:
            issues.extend(check())
        except Exception as exc:  # pragma: no cover - keeps CLI diagnostics actionable
            issues.append(Issue(check.__name__, f"检查执行失败：{exc}"))
    return (2 if issues else 0), issues


def main() -> int:
    code, issues = run_checks()
    if not issues:
        print("[PASS] docs consistency and source-derived contract checks passed.")
        return 0
    print(f"[FAIL] docs checks failed: {len(issues)} issue(s).")
    for issue in issues:
        print(f"  - {issue.location}: {issue.message}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
