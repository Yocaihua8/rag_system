import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "check_docs_consistency.py"
SPEC = importlib.util.spec_from_file_location("check_docs_consistency", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
check_docs_consistency = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = check_docs_consistency
SPEC.loader.exec_module(check_docs_consistency)


def test_repository_docs_consistency_contract_passes():
    code, issues = check_docs_consistency.run_checks()

    assert code == 0, "\n".join(
        f"{issue.location}: {issue.message}" for issue in issues
    )


def test_backlog_check_rejects_completed_history(tmp_path, monkeypatch):
    backlog = tmp_path / "BACKLOG.md"
    backlog.write_text(
        "| B-100 | docs | 历史任务 | done | P1 | S | v1 | team | N/A | 已完成 |\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(check_docs_consistency, "BACKLOG", backlog)

    issues = check_docs_consistency._check_backlog_is_active_only()

    assert any("只能保留未完成事项" in issue.message for issue in issues)


def test_active_reference_check_rejects_removed_document_tree(tmp_path, monkeypatch):
    readme = tmp_path / "README.md"
    readme.write_text("旧证据见 docs/release/old.md\n", encoding="utf-8")
    monkeypatch.setattr(check_docs_consistency, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(check_docs_consistency, "DOCS_ROOT", tmp_path / "docs")
    monkeypatch.setattr(check_docs_consistency, "DOCS_README", tmp_path / "missing-docs-readme.md")
    monkeypatch.setattr(check_docs_consistency, "BACKLOG", tmp_path / "missing-backlog.md")

    issues = check_docs_consistency._check_active_references()

    assert any("docs/release/" in issue.message for issue in issues)


def test_structure_check_rejects_nested_canonical_topic_directory(tmp_path, monkeypatch):
    docs_root = tmp_path / "docs"
    for name in check_docs_consistency.CANONICAL_DIRECTORIES:
        directory = docs_root / name
        directory.mkdir(parents=True)
        (directory / "README.md").write_text(f"[{name}]({name}/)\n", encoding="utf-8")
    (docs_root / "design" / "backend").mkdir()
    docs_readme = docs_root / "README.md"
    docs_readme.write_text(
        "\n".join(f"{name}/" for name in check_docs_consistency.CANONICAL_DIRECTORIES),
        encoding="utf-8",
    )
    monkeypatch.setattr(check_docs_consistency, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(check_docs_consistency, "DOCS_ROOT", docs_root)
    monkeypatch.setattr(check_docs_consistency, "DOCS_README", docs_readme)

    issues = check_docs_consistency._check_structure()

    assert any("必须保持扁平" in issue.message for issue in issues)
