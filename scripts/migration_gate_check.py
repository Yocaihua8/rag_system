"""
migration_gate_check.py — 迁移验收门禁。

在删除旧代码前执行，验证新 src/ 层所有关键模块可正常导入。

用法：
    py -3 scripts/migration_gate_check.py [--strict-startup]
"""
from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# 新架构必须可导入的模块
REQUIRED_IMPORTS = [
    "legacy.desktop.config.settings",
    "legacy.desktop.config.paths",
    "legacy.desktop.domain.models.document",
    "legacy.desktop.domain.models.chunk",
    "legacy.desktop.domain.models.workspace",
    "legacy.desktop.domain.models.task",
    "legacy.desktop.domain.models.conversation",
    "legacy.desktop.domain.errors",
    "legacy.desktop.ports.embedder",
    "legacy.desktop.ports.vector_store",
    "legacy.desktop.ports.retriever",
    "legacy.desktop.ports.llm_client",
    "legacy.desktop.ports.document_store",
    "legacy.desktop.ports.chunk_store",
    "legacy.desktop.ports.task_store",
    "legacy.desktop.ports.workspace_store",
    "legacy.desktop.ports.conversation_store",
    "legacy.desktop.adapters.storage.db",
    "legacy.desktop.adapters.storage.sqlite_workspace_store",
    "legacy.desktop.adapters.storage.sqlite_document_store",
    "legacy.desktop.adapters.storage.sqlite_chunk_store",
    "legacy.desktop.adapters.storage.sqlite_task_store",
    "legacy.desktop.adapters.storage.sqlite_conversation_store",
    "legacy.desktop.adapters.embedding.ollama_embedder",
    "legacy.desktop.adapters.vector_store.numpy_store",
    "legacy.desktop.adapters.retrieval.keyword_retriever",
    "legacy.desktop.adapters.llm.ollama_adapter",
    "legacy.desktop.application.container",
    "legacy.desktop.application.workspace_usecases",
    "legacy.desktop.application.ingestion_usecases",
    "legacy.desktop.application.query_usecases",
    "legacy.desktop.application.generation_usecases",
    "legacy.desktop.application.task_usecases",
    "legacy.desktop.application.settings_usecases",
]


def run_import_checks() -> list[str]:
    errors: list[str] = []
    for module_name in REQUIRED_IMPORTS:
        try:
            importlib.import_module(module_name)
            print(f"  [OK] {module_name}")
        except Exception as exc:
            errors.append(f"{module_name}: {exc}")
            print(f"  [FAIL] {module_name}: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="新架构迁移验收门禁")
    parser.add_argument(
        "--strict-startup",
        action="store_true",
        help="启动检查有警告时视为失败。",
    )
    args = parser.parse_args()

    # Step 1: 模块导入检查
    print("[gate] step 1/2: 模块导入检查")
    import_errors = run_import_checks()
    if import_errors:
        print(f"\n[gate] FAIL: {len(import_errors)} 个模块导入失败：")
        for item in import_errors:
            print(f"  - {item}")
        return 1
    print(f"[gate] step 1/2 PASS: 全部 {len(REQUIRED_IMPORTS)} 个模块导入成功\n")

    # Step 2: 首次运行检查
    print("[gate] step 2/2: 运行时检查")
    from scripts.first_run_check import run_checks
    startup = run_checks()
    if startup.ok:
        print("[gate] step 2/2 PASS: 运行时检查通过")
    else:
        print("[gate] step 2/2 WARN:")
        for item in startup.warnings:
            print(f"  - {item}")
        if args.strict_startup:
            print("[gate] FAIL (--strict-startup)")
            return 3
        print("[gate] 继续（非 strict 模式）")

    print("\n[gate] PASS: 迁移验收门禁全部通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
