from importlib import import_module
from pathlib import Path


def test_backend_module_exposes_main_without_root_compatibility_launcher():
    launcher = import_module("backend.__main__")

    assert callable(launcher.main)
    assert not Path("app.py").exists()
