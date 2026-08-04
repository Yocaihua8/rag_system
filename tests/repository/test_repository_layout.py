from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ALLOWED_ROOT_FILES = {
    ".dockerignore",
    ".editorconfig",
    ".gitignore",
    ".markdownlint.json",
    "AGENTS.md",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "package-lock.json",
    "package.json",
    "README.md",
    "SECURITY.md",
}


def test_repository_root_contains_only_standard_entry_files():
    actual = {
        path.name
        for path in ROOT.iterdir()
        if path.is_file() and path.name != ".env"
    }

    assert actual == ALLOWED_ROOT_FILES


def test_runtime_source_and_docs_are_classified_by_responsibility():
    for relative in (
        "backend",
        "frontend",
        "src-tauri",
        "integrations",
        "ops/docker",
        "scripts",
        "tests/backend",
        "tests/integration",
        "tests/repository",
        "tests/e2e",
        "docs/requirements",
        "docs/design",
        "docs/features",
        "docs/adr",
        "docs/guides",
        "docs/plans",
        "docs/devlog",
    ):
        assert (ROOT / relative).is_dir(), f"missing classified directory: {relative}"

    for relative in (
        "docs/requirements",
        "docs/design",
        "docs/features",
        "docs/adr",
        "docs/guides",
        "docs/plans",
    ):
        nested = [path for path in (ROOT / relative).iterdir() if path.is_dir()]
        assert not nested, f"canonical docs directory must stay flat: {relative}"


def test_legacy_archive_history_and_mixed_script_roots_are_removed():
    for relative in (
        "archive",
        "legacy",
        ".docs-template",
        "docs/release",
        "docs/previews",
        "docs/superpowers",
        "docs/product",
        "docs/architecture",
        "docs/integrations",
        "docs/operations",
        "docs/governance",
    ):
        assert not (ROOT / relative).exists(), f"obsolete path remains: {relative}"

    tools_entries = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "tools").iterdir()
    }
    assert tools_entries == {"tools/openapi-codegen"}
