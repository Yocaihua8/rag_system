from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts import check_import_paths
from scripts.first_run_check import run_checks


REQUIRED_IMPORTS = [
    "desktop.app.startup_checks",
    "backend.app.modules.workspace.service",
    "backend.app.modules.task.service",
    "backend.app.modules.retrieval.service",
    "backend.infra.storage.db.sqlite",
]


def run_import_checks() -> list[str]:
    errors: list[str] = []
    for module_name in REQUIRED_IMPORTS:
        try:
            importlib.import_module(module_name)
        except Exception as ex:  # pragma: no cover - best effort guard script
            errors.append(f"{module_name}: {ex}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Migration gate checks before removing compatibility layers")
    parser.add_argument(
        "--strict-startup",
        action="store_true",
        help="Treat startup warnings as failures.",
    )
    args = parser.parse_args()

    print("[gate] step 1/3: import-path guard")
    code = check_import_paths.main()
    if code != 0:
        print("[gate] FAIL at step 1/3")
        return code

    print("[gate] step 2/3: startup checks")
    startup = run_checks()
    if startup.ok:
        print("[gate] startup checks OK")
    else:
        print("[gate] startup warnings:")
        for item in startup.warnings:
            print(f"- {item}")
        if args.strict_startup:
            print("[gate] FAIL at step 2/3 (--strict-startup)")
            return 3
        print("[gate] continue (non-strict startup mode)")

    print("[gate] step 3/3: required module imports")
    import_errors = run_import_checks()
    if import_errors:
        print("[gate] FAIL at step 3/3")
        for item in import_errors:
            print(f"- {item}")
        return 4

    print("[gate] PASS: migration gate checks all passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
