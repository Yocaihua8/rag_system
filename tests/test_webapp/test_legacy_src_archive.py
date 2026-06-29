from __future__ import annotations

import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (PROJECT_ROOT / path).read_text(encoding="utf-8")


def _iter_python_files(*roots: str) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        root_path = PROJECT_ROOT / root
        if not root_path.exists():
            continue
        for path in root_path.rglob("*.py"):
            parts = set(path.relative_to(PROJECT_ROOT).parts)
            if "__pycache__" in parts:
                continue
            files.append(path)
    return files


def test_active_web_code_does_not_import_src_package():
    bad_refs: list[str] = []

    for path in _iter_python_files("webapp", "backend", "scripts", "tests/test_webapp"):
        if path.name == Path(__file__).name:
            continue
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
        for node in ast.walk(tree):
            imported = ""
            if isinstance(node, ast.ImportFrom):
                imported = node.module or ""
            elif isinstance(node, ast.Import):
                imported = ",".join(alias.name for alias in node.names)
            if imported == "src" or imported.startswith("src."):
                rel = path.relative_to(PROJECT_ROOT).as_posix()
                bad_refs.append(f"{rel}: {imported}")

    assert bad_refs == []


def test_root_src_package_is_archived_under_archive_directory():
    assert not (PROJECT_ROOT / "src").exists()
    assert (PROJECT_ROOT / "archive/src-desktop-legacy/src").is_dir()


def test_dockerfile_does_not_copy_src_package():
    dockerfile = _read("Dockerfile")

    assert "COPY src/" not in dockerfile
    assert "COPY src\\" not in dockerfile


def test_core_requirements_do_not_keep_legacy_desktop_dependencies():
    requirements = _read("requirements.txt").splitlines()
    package_names = {
        line.split("#", 1)[0].strip().split("==", 1)[0].split(">=", 1)[0].lower()
        for line in requirements
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert package_names.isdisjoint({"pyside6", "chromadb", "openai", "ollama"})


def test_current_testing_docs_do_not_require_legacy_src_regressions():
    ag_rules = _read("AGENTS.md")
    testing_guide = _read("docs/guides/testing.md")

    assert "tests/test_application tests/test_domain tests/test_adapters" not in ag_rules
    assert "旧业务层回归" not in ag_rules
    assert "tests/test_application/test_markdown_content.py" not in testing_guide
    assert "tests/test_adapters/test_storage.py" not in testing_guide
