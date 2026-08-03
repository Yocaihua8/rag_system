"""Run the Knowledge Island API service."""

import os

from backend.api.server import run_server
from backend.config.desktop import load_desktop_settings, load_server_binding
from backend.config.settings import load_backend_env


def main() -> int:
    values = {**load_backend_env(), **os.environ}
    try:
        desktop_settings = load_desktop_settings(values)
        binding = load_server_binding(values, desktop_settings=desktop_settings)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    return run_server(host=binding.host, port=binding.port)


if __name__ == "__main__":
    raise SystemExit(main())
