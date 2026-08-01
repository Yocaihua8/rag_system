import sqlite3
from pathlib import Path

from backend.api.server import create_app


ROOT = Path(__file__).resolve().parents[2]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_canonical_flat_document_entry_points_exist():
    for relative in (
        "docs/README.md",
        "docs/BACKLOG.md",
        "docs/style-guide.md",
        "docs/glossary.md",
        "docs/requirements/README.md",
        "docs/requirements/project-background-and-scope.md",
        "docs/requirements/functional-modules.md",
        "docs/requirements/use-cases.md",
        "docs/requirements/version-scope.md",
        "docs/design/README.md",
        "docs/design/system-design-overview.md",
        "docs/design/architecture-overview.md",
        "docs/design/api-spec.md",
        "docs/design/api-changes.md",
        "docs/design/database-design.md",
        "docs/design/permission-matrix.md",
        "docs/design/state-flow-and-acceptance.md",
        "docs/design/frontend-backend-contract-check.md",
        "docs/design/ui-wireframes.md",
        "docs/design/page-module-contract.md",
        "docs/design/component-api-contract.md",
        "docs/design/risk-register.md",
        "docs/features/README.md",
        "docs/adr/README.md",
        "docs/guides/README.md",
        "docs/plans/README.md",
    ):
        assert (ROOT / relative).is_file(), f"missing current document: {relative}"


def test_api_spec_matches_every_current_http_path_and_operation_count(tmp_path):
    api_spec = _read("docs/design/api-spec.md")
    openapi = create_app(db_path=tmp_path / "api.db").openapi()
    paths = openapi["paths"]
    get_count = sum("get" in operations for operations in paths.values())
    post_count = sum("post" in operations for operations in paths.values())

    assert "/" not in paths
    assert len(paths) == 90
    assert get_count == 32
    assert post_count == 66
    assert get_count + post_count == 98
    assert all(path in api_spec for path in paths if path.startswith("/api/"))
    for event_name in ("token", "done", "answer_error"):
        assert event_name in api_spec


def test_database_spec_matches_current_tables_and_documents_fields(tmp_path):
    database_path = tmp_path / "schema.db"
    create_app(db_path=database_path)
    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            )
        }
        document_fields = tuple(
            row[1] for row in connection.execute("PRAGMA table_info(documents)")
        )

    database = _read("docs/design/database-design.md")
    assert len(tables) == 43
    assert document_fields == (
        "id",
        "project_id",
        "source_path",
        "relative_path",
        "content",
        "checksum",
        "updated_at",
    )
    assert all(f"`{table}`" in database for table in tables)
    assert all(f"`{field}`" in database for field in document_fields)


def test_permission_contract_records_current_auth_cors_key_and_agent_boundaries():
    permissions = _read("docs/design/permission-matrix.md")

    for marker in (
        "API Key",
        "JWT",
        "Vue",
        "EventSource",
        "KI_CORS_ORIGINS",
        "env:*",
        "saved:*",
        ".env",
        "project_overview",
        "search_sources",
        "agent_tool_runs",
    ):
        assert marker in permissions


def test_coach_and_obsidian_specs_preserve_current_user_boundaries():
    coach = _read("docs/features/project-knowledge-coach.md")
    obsidian = _read("docs/features/obsidian-integration.md")

    for marker in ("runtime/v2", "学习计划", "来源"):
        assert marker in coach
    for marker in ("desktop-only", "queued", "冲突", "data.json"):
        assert marker in obsidian


def test_runtime_separation_adr_records_ports_cors_and_supersession():
    adr = _read("docs/adr/ADR-010-runtime-separation.md")
    adr_006 = _read("docs/adr/ADR-006-vue-vite-frontend.md")

    for marker in ("8765", "5173", "4173", "KI_CORS_ORIGINS", "API-only", "Tauri"):
        assert marker in adr
    assert "ADR-006" in adr
    assert "ADR-010" in adr_006
    assert "取代" in adr_006


def test_active_docs_do_not_recreate_history_or_template_state():
    for relative in (
        ".docs-template",
        "docs/devlog",
        "docs/release",
        "docs/previews",
        "docs/superpowers",
    ):
        assert not (ROOT / relative).exists()
    assert "v2.0.0" in _read("CHANGELOG.md")
