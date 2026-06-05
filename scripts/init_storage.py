"""
init_storage.py — 初始化运行时目录和数据库 Schema。

用法：
    py -3 scripts/init_storage.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from legacy.desktop.config.settings import load_settings
from legacy.desktop.config.paths import ensure_runtime_dirs, ensure_kb_dirs
from legacy.desktop.adapters.storage.db import create_connection, init_schema


def main() -> None:
    s = load_settings()

    # 创建运行时目录和知识库目录
    ensure_runtime_dirs(s)
    ensure_kb_dirs(s)
    print(f"[OK] 运行时目录: {s.runtime_dir}")
    print(f"[OK] 知识库根目录: {s.kb_root}")

    # 初始化数据库 Schema
    conn = create_connection(s.db_path)
    init_schema(conn)
    conn.close()
    print(f"[OK] 数据库初始化完成: {s.db_path}")

    print("\n[DONE] 存储层初始化成功。")


if __name__ == "__main__":
    main()
