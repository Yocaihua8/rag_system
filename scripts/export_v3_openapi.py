from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from backend.api.v3.app import create_v3_app


class _SchemaOnlyStore:
    """Sentinel dependency used only while FastAPI builds its OpenAPI schema."""


def build_schema() -> dict[str, Any]:
    app = create_v3_app(
        store=_SchemaOnlyStore(),
        executor=None,
        database_info={"alembic_revision": "schema-export"},
    )
    return app.openapi()


def main() -> int:
    parser = argparse.ArgumentParser(description="Export the deterministic v3 OpenAPI schema")
    parser.add_argument("output", type=Path, help="JSON output path")
    args = parser.parse_args()

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(
        build_schema(),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    output.write_text(f"{serialized}\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
