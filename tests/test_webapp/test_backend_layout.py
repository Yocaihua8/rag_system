from importlib import import_module
from pathlib import Path

from fastapi import FastAPI


def test_backend_runtime_is_grouped_under_backend_directory():
    assert Path("backend").is_dir()
    assert Path("backend/app.py").is_file()
    assert Path("backend/webapp/server.py").is_file()
    assert not Path("webapp/server.py").exists()
    assert not Path("app.py").exists()


def test_backend_app_import_exposes_fastapi_app():
    launcher = import_module("backend.app")

    assert isinstance(launcher.app, FastAPI)


def test_backend_server_import_exposes_app_factory():
    server = import_module("backend.webapp.server")

    assert callable(server.create_app)
