from __future__ import annotations

import os
import platform
from collections.abc import Mapping
from pathlib import Path, PureWindowsPath
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.config.settings import AppSettings

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
        appdata = current_env.get("APPDATA")
        if appdata:
            if platform.system() != "Windows":
                return PureWindowsPath(appdata) / app_name
            base = Path(appdata)
        else:
            base = current_home / "AppData" / "Roaming"
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


def kb_raw_dir(settings: "AppSettings") -> Path:
    return settings.kb_root / "raw"


def kb_domain_dir(settings: "AppSettings", domain: str) -> Path:
    return kb_raw_dir(settings) / domain


def ensure_runtime_dirs(settings: "AppSettings") -> None:
    for path in (
        settings.runtime_dir,
        settings.vector_dir,
        settings.logs_dir,
        settings.outputs_dir,
        settings.app_data_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)


def ensure_kb_dirs(settings: "AppSettings") -> None:
    for domain in ("resume", "jds", "notes", "paper", "prompts"):
        kb_domain_dir(settings, domain).mkdir(parents=True, exist_ok=True)


__all__ = [
    "APP_NAME",
    "app_data_dir",
    "app_env_file",
    "ensure_app_data_dir",
    "ensure_kb_dirs",
    "ensure_runtime_dirs",
    "kb_domain_dir",
    "kb_raw_dir",
]
