import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.server import create_app


ROOT = Path(__file__).resolve().parents[2]


def _json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_root_package_orchestrates_parallel_frontends_desktop_and_codegen():
    package = _json("package.json")

    assert package["private"] is True
    assert package["workspaces"] == [
        "frontend",
        "frontend-v3",
        "src-tauri",
        "tools/openapi-codegen",
    ]
    assert package["scripts"] == {
        "frontend:dev": "npm run dev --workspace frontend",
        "frontend:build": "npm run build --workspace frontend",
        "frontend:test": "npm run test --workspace frontend",
        "frontend:e2e": "npm run e2e --workspace frontend",
        "frontend-v3:dev": "npm run dev --workspace frontend-v3",
        "frontend-v3:build": "npm run build --workspace frontend-v3",
        "frontend-v3:test": "npm run test --workspace frontend-v3",
        "frontend-v3:typecheck": "npm run typecheck --workspace frontend-v3",
        "frontend-v3:generate:api": "npm run generate:api --workspace frontend-v3",
        "frontend-v3:e2e": "npm run e2e --workspace frontend-v3",
        "desktop:dev": "npm run dev --workspace src-tauri",
        "desktop:build:windows": "npm run build:windows --workspace src-tauri",
    }
    assert "dependencies" not in package
    assert "devDependencies" not in package


def test_frontend_workspace_owns_vue_vite_vitest_and_playwright():
    package = _json("frontend/package.json")

    assert package["scripts"]["dev"] == "vite --host 127.0.0.1 --port 5173"
    assert package["scripts"]["preview"] == "vite preview --host 127.0.0.1 --port 4173"
    assert package["scripts"]["test"] == "vitest run"
    assert "node scripts/run-e2e.mjs" in package["scripts"]["e2e"]
    assert "vue" in package["dependencies"]
    for dependency in ("vite", "vitest", "@vitejs/plugin-vue", "@playwright/test"):
        assert dependency in package["devDependencies"]


def test_vite_build_is_frontend_local_and_has_no_api_proxy():
    source = (ROOT / "frontend/vite.config.js").read_text(encoding="utf-8")

    assert 'outDir: path.resolve(__dirname, "dist")' in source
    assert "emptyOutDir: true" in source
    assert "proxy:" not in source
    assert "backend/static_dist" not in source
    assert not (ROOT / "vite.config.js").exists()


def test_api_base_configuration_is_absolute_and_local_by_default():
    source = (ROOT / "frontend/src/api/config.js").read_text(encoding="utf-8")

    assert "VITE_API_BASE_URL" in source
    assert "http://127.0.0.1:8765" in source
    assert "new URL" in source


def test_fastapi_is_api_only_and_root_is_not_frontend_fallback(tmp_path):
    source = (ROOT / "backend/api/server.py").read_text(encoding="utf-8")
    client = TestClient(create_app(db_path=tmp_path / "app.db"))

    assert "StaticFiles" not in source
    assert "STATIC_DIST_DIR" not in source
    assert client.get("/").status_code == 404
    assert client.get("/api/health").status_code == 200


def test_playwright_runs_real_cross_origin_frontend_and_backend():
    config = (ROOT / "frontend/playwright.config.js").read_text(encoding="utf-8")
    runner = (ROOT / "frontend/scripts/run-e2e.mjs").read_text(encoding="utf-8")
    e2e_env = (ROOT / "frontend/.env.e2e").read_text(encoding="utf-8")

    assert 'testDir: "../tests/e2e"' in config
    assert "18765" in runner
    assert "4173" in runner
    assert "tests\", \"e2e\", \"e2e_server.py" in runner
    assert '"preview"' in runner
    assert '"@playwright", "test", "cli.js"' in runner
    assert "VITE_API_BASE_URL=http://127.0.0.1:18765" in e2e_env
    assert not (ROOT / "playwright.config.js").exists()
