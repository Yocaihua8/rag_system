from __future__ import annotations

import argparse


def run_qt() -> int:
    from desktop.app.bootstrap import run

    return run()


def run_cli() -> int:
    # Keep backward compatibility for legacy CLI entry.
    print("[WARN] --mode cli uses legacy path (app.main). Preferred mode is --mode qt.")
    from backend.app.main import main as legacy_main

    legacy_main()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="RAG Desktop Launcher")
    parser.add_argument(
        "--mode",
        choices=["qt", "cli"],
        default="qt",
        help="Startup mode: qt (default) or legacy cli",
    )
    args = parser.parse_args()

    if args.mode == "cli":
        return run_cli()
    return run_qt()


if __name__ == "__main__":
    raise SystemExit(main())

