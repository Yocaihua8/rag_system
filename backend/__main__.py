"""Run the Knowledge Island API service."""

import os

from backend.api.server import run_server
from backend.config.settings import load_backend_env
from backend.config.web import DEFAULT_HOST, DEFAULT_PORT


def main() -> int:
    values = {**load_backend_env(), **os.environ}
    host = values.get("KI_API_HOST", DEFAULT_HOST).strip() or DEFAULT_HOST
    raw_port = values.get("KI_API_PORT", str(DEFAULT_PORT)).strip()
    try:
        port = int(raw_port)
    except ValueError as exc:
        raise SystemExit("KI_API_PORT must be an integer") from exc
    return run_server(host=host, port=port)


if __name__ == "__main__":
    raise SystemExit(main())
