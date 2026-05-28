from pathlib import Path

from scripts import check_docs_consistency


def test_docs_consistency_uses_devlog_directory_without_removed_aggregate():
    code, issues = check_docs_consistency.run_checks()

    issue_text = "\n".join(f"{issue.location}: {issue.message}" for issue in issues)
    assert code == 0, issue_text
    assert "docs/DEVLOG.md" not in issue_text


def test_root_readme_documents_current_devlog_directory():
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "`docs/devlog/`" in readme
    assert "`docs/DEVLOG.md`" not in readme
