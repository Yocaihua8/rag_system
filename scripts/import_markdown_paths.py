from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from backend.app.modules.knowledge_base.ingestion import PathImportService


def main() -> int:
    parser = argparse.ArgumentParser(description="Import markdown files from paths into a target directory")
    parser.add_argument("--target", required=True, help="Target directory")
    parser.add_argument("paths", nargs="+", help="Files or directories to import")
    args = parser.parse_args()

    service = PathImportService()
    result = service.import_markdown_paths(paths=args.paths, target_dir=args.target)

    print("[import] done")
    print(f"- imported={result.imported_count}")
    print(f"- skipped={result.skipped_count}")
    print(f"- errors={result.error_count}")
    if result.imported:
        print("[imported]")
        for item in result.imported:
            print(f"- {item.src} -> {item.dst}")
    if result.skipped:
        print("[skipped]")
        for item in result.skipped[:20]:
            print(f"- {item}")
    if result.errors:
        print("[errors]")
        for item in result.errors[:20]:
            print(f"- {item}")
    return 0 if result.error_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())


