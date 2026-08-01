from pathlib import Path


def _workflow() -> str:
    path = Path(".github/workflows/ci.yml")
    assert path.exists(), "B-149 must add a GitHub Actions CI workflow"
    return path.read_text(encoding="utf-8")


def _docs_workflow() -> str:
    path = Path(".github/workflows/docs-checks.yml")
    assert path.exists()
    return path.read_text(encoding="utf-8")


def test_ci_workflow_triggers_on_main_push_and_pull_request():
    workflow = _workflow()

    assert "name: CI" in workflow
    assert "push:" in workflow
    assert "pull_request:" in workflow
    assert "branches: [main]" in workflow
    assert "python-tests:" in workflow
    assert "frontend-e2e:" in workflow


def test_ci_workflow_runs_backend_docs_build_and_e2e_commands():
    workflow = _workflow()

    for marker in [
        ".venv/bin/python -m pytest tests/backend tests/integration tests/repository -q",
        ".venv/bin/python scripts/check_docs_consistency.py",
        ".venv/bin/pip-audit -r backend/requirements/base.txt",
        "npm audit --audit-level=high",
        "npm ci",
        "npm run frontend:test",
        "npm run frontend:build",
        "npm exec --workspace frontend -- playwright install chromium --with-deps",
        "npm run frontend:e2e",
    ]:
        assert marker in workflow


def test_python_tests_job_builds_frontend_before_pytest_collection():
    workflow = _workflow()
    python_job = workflow.split("  frontend-e2e:", 1)[0].split("  python-tests:", 1)[1]

    assert "uses: actions/setup-node@v4" in python_job
    assert "npm ci" in python_job
    assert "npm run frontend:build" in python_job
    assert python_job.index("npm run frontend:build") < python_job.index(
        ".venv/bin/python -m pytest tests/backend tests/integration tests/repository -q"
    )


def test_ci_workflow_uses_current_actions_and_versioned_cache_keys():
    workflow = _workflow()

    for marker in [
        'PYTHON_VERSION: "3.11"',
        'NODE_VERSION: "20"',
        'PYTHONUTF8: "1"',
        "uses: actions/checkout@v6",
        "uses: actions/setup-python@v5",
        "uses: actions/setup-node@v4",
        "uses: actions/cache@v4",
        "venv-${{ runner.os }}-py${{ env.PYTHON_VERSION }}-${{ hashFiles('backend/requirements/base.txt', 'backend/requirements/dev.txt') }}",
        "npm-${{ runner.os }}-node${{ env.NODE_VERSION }}-${{ hashFiles('package-lock.json') }}",
        "restore-keys:",
    ]:
        assert marker in workflow


def test_ci_workflow_installs_security_audit_tooling_before_python_audit():
    workflow = _workflow()
    python_job = workflow.split("  frontend-e2e:", 1)[0].split("  python-tests:", 1)[1]

    assert ".venv/bin/pip install -r backend/requirements/dev.txt" in python_job
    assert python_job.index(".venv/bin/pip install -r backend/requirements/dev.txt") < python_job.index(
        ".venv/bin/pip-audit -r backend/requirements/base.txt"
    )
    assert python_job.index("npm ci") < python_job.index("npm audit --audit-level=high")


def test_docs_workflow_runs_flat_path_and_source_derived_checks():
    workflow = _docs_workflow()

    for marker in (
        "scripts/check-placeholders.ps1",
        "scripts/check-doc-links.ps1",
        "python3 -m pip install -r backend/requirements/base.txt",
        "python3 scripts/check_docs_consistency.py",
    ):
        assert marker in workflow
