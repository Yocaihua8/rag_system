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
        "tools/docs",
        "tests/backend",
        "tests/integration",
        "tests/repository",
        "tests/e2e",
        "docs/product",
        "docs/architecture/backend",
        "docs/architecture/frontend",
        "docs/architecture/contracts",
        "docs/architecture/decisions",
        "docs/integrations",
        "docs/operations",
        "docs/governance/plans",
        "docs/governance/templates",
    ):
        assert (ROOT / relative).is_dir(), f"missing classified directory: {relative}"


def test_legacy_archive_history_and_mixed_script_roots_are_removed():
    for relative in (
        "archive",
        "legacy",
        "scripts",
        ".docs-template",
        "docs/devlog",
        "docs/release",
        "docs/previews",
        "docs/superpowers",
        "docs/design",
        "docs/features",
        "docs/guides",
        "docs/adr",
        "docs/requirements",
    ):
        assert not (ROOT / relative).exists(), f"obsolete path remains: {relative}"
