from __future__ import annotations

import os
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLACEHOLDER_SCRIPT = PROJECT_ROOT / "scripts" / "check-placeholders.ps1"
LINK_SCRIPT = PROJECT_ROOT / "scripts" / "check-doc-links.ps1"


def _run_pwsh(script: Path, target: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    return subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            str(script),
            "-Target",
            str(target),
        ],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_placeholder_checker_ignores_generated_trees_and_non_token_braces(tmp_path):
    docs_root = tmp_path / "consumer"
    docs_root.mkdir()
    (docs_root / "workflow.yml").write_text(
        'ref: "${{ github.sha }}"\npayload: \'{"outer":{"inner":1}}\'\n',
        encoding="utf-8",
    )
    ignored = docs_root / "node_modules" / "package"
    ignored.mkdir(parents=True)
    (ignored / "README.md").write_text("{{SHOULD_BE_IGNORED}}\n", encoding="utf-8")

    result = _run_pwsh(PLACEHOLDER_SCRIPT, docs_root)

    assert result.returncode == 0, result.stdout + result.stderr


def test_placeholder_checker_rejects_unresolved_consumer_token(tmp_path):
    bad_file = tmp_path / "consumer.md"
    bad_file.write_text("# {{UNRESOLVED_TOKEN}}\n", encoding="utf-8")

    result = _run_pwsh(PLACEHOLDER_SCRIPT, bad_file)

    assert result.returncode == 1
    assert "unresolved placeholder" in result.stdout


def test_link_checker_ignores_generated_dependency_trees(tmp_path):
    docs_root = tmp_path / "consumer"
    docs_root.mkdir()
    (docs_root / "README.md").write_text("# Valid\n", encoding="utf-8")
    ignored = docs_root / ".venv" / "package"
    ignored.mkdir(parents=True)
    (ignored / "README.md").write_text("[broken](missing.md)\n", encoding="utf-8")

    result = _run_pwsh(LINK_SCRIPT, docs_root)

    assert result.returncode == 0, result.stdout + result.stderr
