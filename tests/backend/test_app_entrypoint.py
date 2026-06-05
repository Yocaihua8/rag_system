from importlib import import_module

from fastapi import FastAPI


def test_root_launcher_exposes_asgi_app_for_uvicorn():
    launcher = import_module("backend.app")

    assert isinstance(launcher.app, FastAPI)
    assert launcher.app.title == "知识岛 API"
    assert launcher.app.version == "0.13.0"
