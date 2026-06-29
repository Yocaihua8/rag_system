"""
import_markdown_paths.py — 将 Markdown 文件复制到知识库目录（指定 domain）。

用法：
    py -3 scripts/import_markdown_paths.py --domain resume path/to/file.md [path2/ ...]
    py -3 scripts/import_markdown_paths.py --domain jds --target custom/dir file.md
"""
from __future__ import annotations

import argparse
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.config.paths import kb_domain_dir
from backend.config.settings import load_settings


@dataclass
class ImportResult:
    imported: list[tuple[Path, Path]] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def imported_count(self) -> int:
        return len(self.imported)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped)

    @property
    def error_count(self) -> int:
        return len(self.errors)


def collect_markdown_files(paths: list[str]) -> list[Path]:
    """递归收集所有 .md 文件。"""
    result: list[Path] = []
    for p in paths:
        src = Path(p)
        if src.is_file() and src.suffix.lower() == ".md":
            result.append(src)
        elif src.is_dir():
            result.extend(src.rglob("*.md"))
    return result


def import_markdown_paths(
    paths: list[str],
    target_dir: Path,
) -> ImportResult:
    result = ImportResult()
    target_dir.mkdir(parents=True, exist_ok=True)
    files = collect_markdown_files(paths)

    for src in files:
        dst = target_dir / src.name
        if dst.exists():
            result.skipped.append(src)
            continue
        try:
            shutil.copy2(src, dst)
            result.imported.append((src, dst))
        except Exception as exc:
            result.errors.append(f"{src}: {exc}")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="将 Markdown 文件导入知识库 domain 目录"
    )
    parser.add_argument(
        "--domain",
        default="notes",
        help="目标 domain（resume / jds / notes），默认 notes",
    )
    parser.add_argument(
        "--target",
        default=None,
        help="覆盖目标目录（不指定则使用 kb_root/<domain>）",
    )
    parser.add_argument("paths", nargs="+", help="要导入的文件或目录")
    args = parser.parse_args()

    s = load_settings()
    if args.target:
        target_dir = Path(args.target)
    else:
        target_dir = kb_domain_dir(s, args.domain)

    result = import_markdown_paths(args.paths, target_dir)

    print(f"[import] 完成 → {target_dir}")
    print(f"  imported = {result.imported_count}")
    print(f"  skipped  = {result.skipped_count}")
    print(f"  errors   = {result.error_count}")

    if result.imported:
        print("[imported]")
        for src, dst in result.imported:
            print(f"  {src} -> {dst}")
    if result.skipped:
        print("[skipped]")
        for p in result.skipped[:20]:
            print(f"  {p}")
    if result.errors:
        print("[errors]")
        for e in result.errors[:20]:
            print(f"  {e}")

    return 0 if result.error_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
