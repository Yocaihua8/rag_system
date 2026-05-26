import json
from pathlib import Path

from fastapi.testclient import TestClient

import webapp.server as server


def test_frontend_package_declares_vue_vite_build_scripts():
    package_path = Path("package.json")

    assert package_path.exists(), "root package.json must expose frontend npm scripts"
    package_data = json.loads(package_path.read_text(encoding="utf-8"))

    assert package_data["private"] is True
    assert package_data["scripts"]["dev"] == "vite --host 127.0.0.1 --port 5173"
    assert package_data["scripts"]["build"] == "vite build"
    assert package_data["scripts"]["preview"] == "vite preview --host 127.0.0.1 --port 4173"
    assert package_data["dependencies"]["@vitejs/plugin-vue"]
    assert package_data["dependencies"]["vite"]
    assert package_data["dependencies"]["vue"]


def test_vite_config_builds_into_webapp_static_dist_and_proxies_api():
    vite_config = Path("frontend/vite.config.js")

    assert vite_config.exists(), "frontend/vite.config.js must configure the Vite build"
    config_text = vite_config.read_text(encoding="utf-8")

    assert "defineConfig" in config_text
    assert "vue()" in config_text
    assert "base: \"./\"" in config_text
    assert "outDir: path.resolve(__dirname, \"../webapp/static_dist\")" in config_text
    assert "emptyOutDir: true" in config_text
    assert "\"/api\"" in config_text
    assert "target: \"http://127.0.0.1:8765\"" in config_text


def test_fastapi_serves_vite_build_when_it_exists(tmp_path, monkeypatch):
    dist_dir = tmp_path / "static_dist"
    legacy_dir = tmp_path / "static"
    dist_dir.mkdir()
    legacy_dir.mkdir()
    (dist_dir / "index.html").write_text("<!doctype html><title>vite-build</title>", encoding="utf-8")
    (legacy_dir / "index.html").write_text("<!doctype html><title>legacy-static</title>", encoding="utf-8")

    monkeypatch.setattr(server, "STATIC_DIST_DIR", dist_dir, raising=False)
    monkeypatch.setattr(server, "STATIC_LEGACY_DIR", legacy_dir, raising=False)
    monkeypatch.setattr(server, "STATIC_DIR", legacy_dir, raising=False)
    client = TestClient(server.create_app(db_path=tmp_path / "app.db"))

    response = client.get("/")

    assert response.status_code == 200
    assert "vite-build" in response.text


def test_fastapi_falls_back_to_legacy_static_when_vite_build_is_missing(tmp_path, monkeypatch):
    dist_dir = tmp_path / "missing_dist"
    legacy_dir = tmp_path / "static"
    legacy_dir.mkdir()
    (legacy_dir / "index.html").write_text("<!doctype html><title>legacy-static</title>", encoding="utf-8")

    monkeypatch.setattr(server, "STATIC_DIST_DIR", dist_dir, raising=False)
    monkeypatch.setattr(server, "STATIC_LEGACY_DIR", legacy_dir, raising=False)
    monkeypatch.setattr(server, "STATIC_DIR", legacy_dir, raising=False)
    client = TestClient(server.create_app(db_path=tmp_path / "app.db"))

    response = client.get("/")

    assert response.status_code == 200
    assert "legacy-static" in response.text
