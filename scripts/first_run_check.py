"""
first_run_check.py — 首次运行检查（目录、数据库、Ollama 可用性）。

用法：
    py -3 scripts/first_run_check.py [--strict]
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.config.paths import ensure_kb_dirs, ensure_runtime_dirs
from backend.config.settings import load_settings
from backend.providers.llm.ollama import OllamaLLM
from backend.storage import KnowledgeStore


@dataclass
class CheckResult:
    ok: bool
    warnings: list[str] = field(default_factory=list)


def run_checks() -> CheckResult:
    warnings: list[str] = []
    s = load_settings()

    # 1. 运行时目录
    try:
        ensure_runtime_dirs(s)
        ensure_kb_dirs(s)
        print(f"[OK] 目录检查通过: runtime_dir={s.runtime_dir}")
    except Exception as exc:
        warnings.append(f"目录创建失败: {exc}")

    # 2. 数据库 Schema
    try:
        KnowledgeStore(s.db_path)
        print(f"[OK] 数据库 Schema 已就绪: {s.db_path}")
    except Exception as exc:
        warnings.append(f"数据库初始化失败: {exc}")

    # 3. Ollama 可用性（非阻断）
    try:
        client = OllamaLLM(host=s.ollama_host, model=s.ollama_model, timeout=5.0)
        client.get_tags()
        print(f"[OK] Ollama 服务可达: {s.ollama_host}")
    except Exception:
        warnings.append(
            f"Ollama 服务不可达（{s.ollama_host}）。"
            "问答和生成功能将不可用，但知识库索引仍可正常使用。"
        )

    # 4. 知识库根目录存在
    if not s.kb_root.exists():
        warnings.append(
            f"知识库根目录不存在: {s.kb_root}。"
            "请运行 seed_demo_files.py 或在设置中指定正确路径。"
        )
    else:
        print(f"[OK] 知识库根目录存在: {s.kb_root}")

    return CheckResult(ok=len(warnings) == 0, warnings=warnings)


def main() -> int:
    parser = argparse.ArgumentParser(description="RAG Desktop 首次运行检查")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="有警告时以非 0 退出码返回。",
    )
    args = parser.parse_args()

    result = run_checks()
    if result.ok:
        print("\n[DONE] 启动检查全部通过。")
        return 0

    print("\n[WARN] 启动检查发现以下提示项：")
    for item in result.warnings:
        print(f"  - {item}")

    if args.strict:
        print("[FAIL] strict 模式已启用，因存在提示项返回非 0。")
        return 2

    print("[OK] 非 strict 模式：允许继续运行。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
