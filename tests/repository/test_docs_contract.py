from pathlib import Path

from backend.api.server import create_app


ROOT = Path(__file__).resolve().parents[2]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_current_product_architecture_and_operations_documents_exist():
    for relative in (
        "docs/README.md",
        "docs/product/overview.md",
        "docs/product/modules.md",
        "docs/product/use-cases.md",
        "docs/product/glossary.md",
        "docs/architecture/overview.md",
        "docs/architecture/backend/api.md",
        "docs/architecture/backend/data.md",
        "docs/architecture/frontend/pages.md",
        "docs/architecture/contracts/frontend-backend.md",
        "docs/architecture/contracts/permissions.md",
        "docs/integrations/desktop.md",
        "docs/integrations/obsidian.md",
        "docs/operations/setup.md",
        "docs/operations/testing.md",
        "docs/operations/docker.md",
    ):
        assert (ROOT / relative).is_file(), f"missing current document: {relative}"


def test_api_spec_covers_every_current_http_path_without_static_root(tmp_path):
    api_spec = _read("docs/architecture/backend/api.md")
    app = create_app(db_path=tmp_path / "app.db")
    openapi = app.openapi()

    assert "/" not in openapi["paths"]
    assert "/api/health" in openapi["paths"]
    assert "/api/answer/stream" in openapi["paths"]
    assert all(path in api_spec for path in openapi["paths"] if path.startswith("/api/"))


def test_database_and_permission_contracts_keep_v2_boundaries():
    database = _read("docs/architecture/backend/data.md")
    permissions = _read("docs/architecture/contracts/permissions.md")

    for table in (
        "projects",
        "documents",
        "chunks",
        "coach_assessments",
        "learning_plans",
        "obsidian_connections",
        "obsidian_publications",
    ):
        assert table in database
    assert "Agent" in permissions
    assert "只读" in permissions


def test_v2_coach_and_obsidian_facts_are_preserved_in_current_specs():
    coach = _read("docs/product/features/project-knowledge-coach.md")
    obsidian = _read("docs/integrations/obsidian.md")

    assert "runtime/v2" in coach
    assert "学习计划" in coach
    assert "来源" in coach
    assert "desktop-only" in obsidian
    assert "queued" in obsidian
    assert "冲突" in obsidian


def test_runtime_separation_adr_records_ports_cors_and_supersession():
    adr = _read("docs/architecture/decisions/ADR-010-runtime-separation.md")
    adr_006 = _read("docs/architecture/decisions/ADR-006-vue-vite-frontend.md")

    for marker in ("8765", "5173", "4173", "KI_CORS_ORIGINS", "API-only", "Tauri"):
        assert marker in adr
    assert "ADR-006" in adr
    assert "ADR-010" in adr_006


def test_active_docs_do_not_recreate_release_snapshots_or_devlogs():
    assert not (ROOT / "docs/devlog").exists()
    assert not (ROOT / "docs/release").exists()
    assert not (ROOT / "docs/previews").exists()
    assert "v2.0.0" in _read("CHANGELOG.md")
