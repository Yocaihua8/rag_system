import json
from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_package_declares_playwright_e2e_scripts_and_dependency():
    package_data = json.loads(Path("package.json").read_text(encoding="utf-8"))

    assert package_data["scripts"]["e2e:install"] == "playwright install chromium"
    assert package_data["scripts"]["test:e2e"] == "npm run build && playwright test"
    assert package_data["devDependencies"]["@playwright/test"]


def test_playwright_config_runs_fastapi_web_server_with_base_url():
    config_path = Path("playwright.config.js")
    assert config_path.exists(), "B-25 should add a root Playwright config"

    config = config_path.read_text(encoding="utf-8")

    for marker in [
        "defineConfig",
        'testDir: "./tests/e2e"',
        "KI_E2E_PORT",
        "18765",
        "baseURL",
        "http://127.0.0.1",
        "webServer",
        'globalTeardown: "./tests/e2e/global-teardown.mjs"',
        "node tests/e2e/start-web-server.mjs",
        "/api/health",
        "reuseExistingServer: !process.env.CI",
        'trace: "retain-on-failure"',
        'screenshot: "only-on-failure"',
        'devices["Desktop Chrome"]',
    ]:
        assert marker in config


def test_e2e_server_uses_temporary_database_via_ki_db_path():
    node_server = Path("tests/e2e/start-web-server.mjs")
    python_server = Path("tests/e2e/e2e_server.py")
    global_teardown = Path("tests/e2e/global-teardown.mjs")

    assert node_server.exists(), "B-25 should add a Node wrapper for Playwright webServer"
    assert python_server.exists(), "B-25 should add a Python FastAPI test server entrypoint"
    assert global_teardown.exists(), "B-165 should stop the Windows E2E server after the suite"

    node_source = node_server.read_text(encoding="utf-8")
    python_source = python_server.read_text(encoding="utf-8")
    teardown_source = global_teardown.read_text(encoding="utf-8")

    for marker in [
        "spawn(",
        "tests/e2e/e2e_server.py",
        "KI_DB_PATH",
        "KI_E2E_PORT",
        "os.tmpdir()",
        ".venv",
        "let shutdownRequested = false",
        "if (shutdownRequested)",
        "shutdownTimer = setTimeout",
        "clearTimeout(shutdownTimer)",
    ]:
        assert marker in node_source
    assert "process.kill(process.pid, signal)" not in node_source

    for marker in [
        "os.environ.setdefault",
        "KI_DB_PATH",
        "KI_E2E_PORT",
        "Path(os.environ[\"KI_DB_PATH\"])",
        "from backend.api.server import create_app",
        'test_app.post("/__e2e__/shutdown")',
        "server.should_exit = True",
        'test_app.mount("/", create_app(db_path=db_path))',
        "uvicorn.Server(config)",
    ]:
        assert marker in python_source

    for marker in [
        "globalTeardown",
        'fetch(`${baseURL}/__e2e__/shutdown`',
        'method: "POST"',
        "AbortController",
    ]:
        assert marker in teardown_source


def test_e2e_smoke_test_covers_project_note_answer_flow():
    spec_path = Path("tests/e2e/web-mvp-smoke.spec.js")
    assert spec_path.exists(), "B-25 should add the first browser E2E smoke spec"

    spec = spec_path.read_text(encoding="utf-8")

    for marker in [
        "test(",
        "creates a project, imports a note, and answers from local sources",
        "fs.mkdtemp",
        "page.goto(\"/\")",
        "locator('[data-nav-action=\"library\"]')",
        "getByLabel(\"项目名称\")",
        "getByLabel(\"本地目录\")",
        "getByRole(\"button\", { name: \"创建知识库\" })",
        "getByPlaceholder(\"粘贴一段笔记\")",
        "getByRole(\"button\", { name: \"加入\" })",
        "getByRole(\"button\", { name: \"选择资料\" })",
        "getByLabel(\"输入问题\")",
        "getByRole(\"button\", { name: \"发送\" })",
        "回答已生成",
        "回答依据",
    ]:
        assert marker in spec


def test_backend_config_allows_ki_db_path_override_for_e2e_isolation():
    config = _read("backend/config/web.py")

    assert "import os" in config
    assert 'os.environ.get("KI_DB_PATH")' in config
    assert "Path(override).expanduser()" in config


def test_testing_guide_documents_e2e_ui_commands():
    testing_doc = _read("docs/guides/testing.md")

    for marker in [
        "npm run e2e:install",
        "npm run test:e2e",
        "Playwright",
        "tests/e2e/",
        "KI_DB_PATH",
        "端到端 UI 自动化测试",
    ]:
        assert marker in testing_doc
