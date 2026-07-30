from pathlib import Path

from scripts import check_docs_consistency


def test_repository_docs_consistency_contract_passes():
    code, issues = check_docs_consistency.run_checks()

    assert code == 0, "\n".join(
        f"{issue.location}: {issue.message}" for issue in issues
    )


def test_devlog_check_detects_nested_log_missing_from_index(tmp_path, monkeypatch):
    devlog_dir = tmp_path / "docs" / "devlog"
    dated_log = devlog_dir / "2026" / "07" / "2026-07-30.md"
    dated_log.parent.mkdir(parents=True)
    dated_log.write_text("# 日志\n", encoding="utf-8")
    index = devlog_dir / "README.md"
    index.write_text("# DevLog\n", encoding="utf-8")

    monkeypatch.setattr(check_docs_consistency, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(check_docs_consistency, "DEVLOG_DIR", devlog_dir)
    monkeypatch.setattr(check_docs_consistency, "DEVLOG_INDEX", index)

    issues = check_docs_consistency._check_devlog_index()

    assert any("未在 docs/devlog/README.md 中索引" in issue.message for issue in issues)


def test_devlog_check_rejects_flat_dated_log(tmp_path, monkeypatch):
    devlog_dir = tmp_path / "docs" / "devlog"
    devlog_dir.mkdir(parents=True)
    dated_log = devlog_dir / "2026-07-30.md"
    dated_log.write_text("# 日志\n", encoding="utf-8")
    index = devlog_dir / "README.md"
    index.write_text(
        "# DevLog\n\n- [2026-07-30](2026-07-30.md)\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(check_docs_consistency, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(check_docs_consistency, "DEVLOG_DIR", devlog_dir)
    monkeypatch.setattr(check_docs_consistency, "DEVLOG_INDEX", index)

    issues = check_docs_consistency._check_devlog_index()

    assert any("必须归档到" in issue.message for issue in issues)
