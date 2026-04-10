from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from backend.app.services.settings import SettingsService
from backend.app.modules.workspace import WorkspaceService
from backend.infra.storage.db.sqlite import init_runtime_db
from desktop.app.startup_checks import run_startup_checks


@dataclass
class CheckResult:
    ok: bool
    warnings: list[str]


def run_checks() -> CheckResult:
    init_runtime_db()
    checks = run_startup_checks(SettingsService(), WorkspaceService())
    return CheckResult(ok=not checks.has_warning, warnings=list(checks.warnings))


def main() -> int:
    parser = argparse.ArgumentParser(description="RAG Desktop first-run checks")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero code when warnings exist.",
    )
    args = parser.parse_args()

    result = run_checks()
    if result.ok:
        print("[OK] 启动检查通过：未发现阻断项。")
        return 0

    print("[WARN] 启动检查发现提示项：")
    for item in result.warnings:
        print(f"- {item}")

    if args.strict:
        print("[FAIL] strict 模式已启用，因存在提示项返回非 0。")
        return 2
    print("[OK] 非 strict 模式：允许继续运行。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

