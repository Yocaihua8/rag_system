import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_frontend_workspace_declares_playwright_e2e_command():
    root_package = json.loads(_read("package.json"))
    frontend_package = json.loads(_read("frontend/package.json"))

    assert root_package["scripts"]["frontend:e2e"] == "npm run e2e --workspace frontend"
    assert "vite build --mode e2e" in frontend_package["scripts"]["e2e"]
    assert "node scripts/run-e2e.mjs" in frontend_package["scripts"]["e2e"]
    assert "@playwright/test" in frontend_package["devDependencies"]


def test_playwright_config_starts_separate_frontend_and_backend_origins():
    config = _read("frontend/playwright.config.js")
    runner = _read("frontend/scripts/run-e2e.mjs")

    for marker in (
        'testDir: "../tests/e2e"',
        'trace: "retain-on-failure"',
        'screenshot: "only-on-failure"',
    ):
        assert marker in config
    for marker in (
        "KI_E2E_BACKEND_PORT",
        "18765",
        "KI_E2E_FRONTEND_PORT",
        "4173",
        "e2e_server.py",
        '"preview"',
        "/api/health",
    ):
        assert marker in runner


def test_e2e_backend_uses_isolated_database_and_explicit_shutdown():
    wrapper = _read("frontend/scripts/run-e2e.mjs")
    server = _read("tests/e2e/e2e_server.py")

    for marker in ("spawn(", "KI_DB_PATH", "18765", "mkdtempSync", ".venv", "SIGKILL"):
        assert marker in wrapper
    assert 'test_app.post("/__e2e__/shutdown")' in server
    assert "create_app(db_path=db_path)" in server
    assert "uvicorn.Server(config)" in server


def test_browser_suite_covers_cross_origin_runtime_flows():
    spec = _read("tests/e2e/web-mvp-smoke.spec.js")

    for marker in (
        "creates a project, imports a note, and answers from local sources",
        "http://127.0.0.1:18765",
        "EventSource",
        "/api/answer/stream",
        "/api/coach/learning-plans",
        "/api/obsidian/",
        "Access-Control-Allow-Origin",
    ):
        assert marker in spec


def test_backend_config_allows_isolated_e2e_database_override():
    source = _read("backend/config/web.py")

    assert 'os.environ.get("KI_DB_PATH")' in source
    assert "Path(override).expanduser().resolve()" in source


def test_testing_guide_documents_new_e2e_command_and_ports():
    testing = _read("docs/guides/testing.md")

    for marker in ("npm run frontend:e2e", "Playwright", "tests/e2e/", "18765", "4173"):
        assert marker in testing
