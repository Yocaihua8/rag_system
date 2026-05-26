from importlib import import_module

from fastapi import FastAPI


def test_root_launcher_exposes_asgi_app_for_uvicorn():
    launcher = import_module("app")

    assert isinstance(launcher.app, FastAPI)
