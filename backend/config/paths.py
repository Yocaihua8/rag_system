from __future__ import annotations

import os
import platform
from collections.abc import Mapping
from pathlib import Path

APP_NAME = "KnowledgeIsland"


def app_data_dir(
    app_name: str = APP_NAME,
    *,
    system: str | None = None,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    current_system = system or platform.system()
    current_env = environ if environ is not None else os.environ
    current_home = home if home is not None else Path.home()

    if current_system == "Windows":
        base = Path(current_env.get("APPDATA") or current_home / "AppData" / "Roaming")
    elif current_system == "Darwin":
        base = current_home / "Library" / "Application Support"
    else:
        base = Path(current_env.get("XDG_CONFIG_HOME") or current_home / ".config")
    return base / app_name


def ensure_app_data_dir(app_name: str = APP_NAME) -> Path:
    path = app_data_dir(app_name)
    path.mkdir(parents=True, exist_ok=True)
    return path


def app_env_file(app_name: str = APP_NAME) -> Path:
    return app_data_dir(app_name) / ".env"


__all__ = ["APP_NAME", "app_data_dir", "app_env_file", "ensure_app_data_dir"]
