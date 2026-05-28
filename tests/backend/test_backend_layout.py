from importlib import import_module
from pathlib import Path

from fastapi import FastAPI


def test_backend_runtime_is_grouped_under_backend_directory():
    assert Path("backend").is_dir()
    assert Path("backend/app.py").is_file()
    assert Path("backend/knowledge_island/server.py").is_file()
    assert not Path("backend/webapp").exists()
    assert not Path("webapp/server.py").exists()
    assert not Path("app.py").exists()


def test_backend_app_import_exposes_fastapi_app():
    launcher = import_module("backend.app")

    assert isinstance(launcher.app, FastAPI)


def test_backend_server_import_exposes_app_factory():
    server = import_module("backend.knowledge_island.server")

    assert callable(server.create_app)


def test_backend_runtime_dir_stays_under_project_root_runtime():
    config = import_module("backend.knowledge_island.config")

    assert config.runtime_dir() == Path.cwd() / "runtime" / "knowledge_island"
    assert not Path("backend/runtime").exists()


def test_current_stage_directory_names_do_not_use_legacy_names():
    assert Path("legacy/desktop").is_dir()
    assert not Path("src").exists()
    assert Path("docs/archive/architecture").is_dir()
    assert not Path("docs/architecture").exists()
    assert Path("docs/archive/release").is_dir()
    assert not Path("docs/release").exists()
    assert Path("tests/backend").is_dir()
    assert Path("tests/frontend").is_dir()
    assert not Path("tests/test_webapp").exists()
