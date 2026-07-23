from __future__ import annotations

import ast
import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from pathlib import PurePosixPath
from typing import Any

from backend.domain.models import Document, SearchHit
from backend.storage import KnowledgeStore


ANALYZER_VERSION = "rules-v1"
SKILL_TAXONOMY = {
    "version": "v1",
    "name": "通用开发技能树",
    "status": "active",
}
SKILL_NODES = (
    {"stable_key": "language", "name": "编程语言", "category": "language", "sort_order": 10},
    {"stable_key": "language:python", "parent_key": "language", "name": "Python", "category": "language", "sort_order": 11},
    {"stable_key": "language:javascript", "parent_key": "language", "name": "JavaScript", "category": "language", "sort_order": 12},
    {"stable_key": "language:typescript", "parent_key": "language", "name": "TypeScript", "category": "language", "sort_order": 13},
    {"stable_key": "framework", "name": "框架与 Web", "category": "framework", "sort_order": 20},
    {"stable_key": "framework:fastapi", "parent_key": "framework", "name": "FastAPI", "category": "framework", "sort_order": 21},
    {"stable_key": "framework:flask", "parent_key": "framework", "name": "Flask", "category": "framework", "sort_order": 22},
    {"stable_key": "framework:django", "parent_key": "framework", "name": "Django", "category": "framework", "sort_order": 23},
    {"stable_key": "framework:vue", "parent_key": "framework", "name": "Vue", "category": "framework", "sort_order": 24},
    {"stable_key": "framework:react", "parent_key": "framework", "name": "React", "category": "framework", "sort_order": 25},
    {"stable_key": "framework:next", "parent_key": "framework", "name": "Next.js", "category": "framework", "sort_order": 26},
    {"stable_key": "framework:vite", "parent_key": "framework", "name": "Vite", "category": "framework", "sort_order": 27},
    {"stable_key": "data", "name": "数据", "category": "data", "sort_order": 30},
    {"stable_key": "data:sqlite", "parent_key": "data", "name": "SQLite", "category": "data", "sort_order": 31},
    {"stable_key": "data:sqlalchemy", "parent_key": "data", "name": "SQLAlchemy", "category": "data", "sort_order": 32},
    {"stable_key": "testing", "name": "测试", "category": "testing", "sort_order": 40},
    {"stable_key": "testing:pytest", "parent_key": "testing", "name": "pytest", "category": "testing", "sort_order": 41},
    {"stable_key": "testing:vitest", "parent_key": "testing", "name": "Vitest", "category": "testing", "sort_order": 42},
    {"stable_key": "testing:jest", "parent_key": "testing", "name": "Jest", "category": "testing", "sort_order": 43},
    {"stable_key": "testing:playwright", "parent_key": "testing", "name": "Playwright", "category": "testing", "sort_order": 44},
    {"stable_key": "delivery", "name": "交付", "category": "delivery", "sort_order": 50},
    {"stable_key": "delivery:package-scripts", "parent_key": "delivery", "name": "包管理脚本", "category": "delivery", "sort_order": 51},
    {"stable_key": "delivery:docker", "parent_key": "delivery", "name": "Docker", "category": "delivery", "sort_order": 52},
    {"stable_key": "ai", "name": "AI 工程", "category": "ai", "sort_order": 60},
    {"stable_key": "ai:llm", "parent_key": "ai", "name": "LLM 集成", "category": "ai", "sort_order": 61},
    {"stable_key": "ai:rag", "parent_key": "ai", "name": "RAG", "category": "ai", "sort_order": 62},
)


_FRAMEWORK_RULES = {
    "fastapi": ("framework:fastapi", "FastAPI", "framework"),
    "flask": ("framework:flask", "Flask", "framework"),
    "django": ("framework:django", "Django", "framework"),
    "vue": ("framework:vue", "Vue", "framework"),
    "react": ("framework:react", "React", "framework"),
    "next": ("framework:next", "Next.js", "framework"),
    "next.js": ("framework:next", "Next.js", "framework"),
    "vite": ("framework:vite", "Vite", "framework"),
}
_TEST_RULES = {
    "pytest": ("testing:pytest", "pytest"),
    "vitest": ("testing:vitest", "Vitest"),
    "jest": ("testing:jest", "Jest"),
    "playwright": ("testing:playwright", "Playwright"),
}


def analyze_project(
    store: KnowledgeStore,
    project_id: str,
    llm_client: Any | None = None,
) -> dict[str, Any]:
    documents = sorted(store.list_documents(project_id), key=lambda item: item.relative_path.lower())
    if not documents:
        raise ValueError("coach analysis requires imported documents")

    fingerprint = compute_source_fingerprint(documents)
    latest = store.get_current_coach_analysis_run(project_id)
    if latest and latest.status == "completed" and latest.source_fingerprint != fingerprint:
        store.mark_coach_analysis_stale(project_id)

    points, warnings = _build_knowledge_points(documents)
    mappings = _build_skill_mappings(points)
    signals = _signals(points)
    summary: dict[str, Any] = {
        "overview": _rule_overview(documents, signals),
        "signals": signals,
        "source_count": len(documents),
        "knowledge_point_count": len(points),
        "skill_mapping_count": len(mappings),
        "enhancement_mode": "rule",
        "warning": "；".join(warnings),
    }
    _enhance_summary(summary, documents, llm_client)

    run = store.create_coach_analysis_run(project_id, ANALYZER_VERSION, fingerprint)
    completed = store.save_coach_analysis_result(
        run.id,
        summary,
        points,
        SKILL_TAXONOMY,
        SKILL_NODES,
        mappings,
    )
    response = completed.to_dict()
    saved_points = store.list_coach_knowledge_points(project_id, run_id=completed.id)
    sources = _source_index(saved_points)
    response["source_ids"] = sorted(sources)
    response["sources"] = sources
    return response


def build_coach_overview(store: KnowledgeStore, project_id: str) -> dict[str, Any]:
    run = current_coach_analysis(store, project_id)
    points = store.list_coach_knowledge_points(project_id, run_id=run.id)
    mappings = store.list_coach_skill_mappings(project_id, run_id=run.id)
    sources = _source_index(points)
    return {
        "project_id": project_id,
        "analysis": run.to_dict(),
        "status": run.status,
        "stale": run.status == "stale",
        "summary": run.summary.get("overview", ""),
        "signals": run.summary.get("signals", {}),
        "knowledge_point_count": len(points),
        "skill_mapping_count": len(mappings),
        "source_ids": sorted(sources),
        "sources": sources,
        "scope_notice": "仅表示当前项目、当前来源版本下的项目知识分析。",
    }


def build_knowledge_points_view(store: KnowledgeStore, project_id: str) -> dict[str, Any]:
    run = current_coach_analysis(store, project_id)
    points = store.list_coach_knowledge_points(project_id, run_id=run.id)
    sources = _source_index(points)
    items = []
    for point in points:
        body = point.to_dict()
        body.pop("sources", None)
        body["source_ids"] = [source.id for source in point.sources]
        items.append(body)
    return {
        "analysis": run.to_dict(),
        "status": run.status,
        "stale": run.status == "stale",
        "items": items,
        "sources": sources,
        "scope_notice": "知识点来自当前项目资料，不代表职业能力。",
    }


def build_skills_view(store: KnowledgeStore, project_id: str) -> dict[str, Any]:
    run = current_coach_analysis(store, project_id)
    points = store.list_coach_knowledge_points(project_id, run_id=run.id)
    mappings = store.list_coach_skill_mappings(project_id, run_id=run.id)
    sources = _source_index(points)
    mappings_by_skill: dict[str, list[dict[str, Any]]] = {}
    for mapping in mappings:
        payload = mapping.to_dict()
        payload["source_ids"] = [mapping.source_id]
        mappings_by_skill.setdefault(mapping.skill_node_id, []).append(payload)
    items = []
    for node in store.list_coach_skill_nodes(SKILL_TAXONOMY["version"]):
        node_mappings = mappings_by_skill.get(node.id, [])
        payload = node.to_dict()
        payload["mappings"] = node_mappings
        payload["project_evidence"] = "mapped" if node_mappings else "no_project_evidence"
        items.append(payload)
    return {
        "analysis": run.to_dict(),
        "status": run.status,
        "stale": run.status == "stale",
        "taxonomy": dict(SKILL_TAXONOMY),
        "items": items,
        "sources": sources,
        "scope_notice": "技能映射仅辅助解释当前项目知识，不是整体职业能力评价。",
    }


def compute_source_fingerprint(documents: Iterable[Document]) -> str:
    digest = hashlib.sha256()
    for document in sorted(documents, key=lambda item: (item.id, item.relative_path.lower())):
        digest.update(document.id.encode("utf-8"))
        digest.update(b"\0")
        digest.update(_normalized_path(document.relative_path).encode("utf-8"))
        digest.update(b"\0")
        digest.update(document.checksum.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def current_coach_analysis(store: KnowledgeStore, project_id: str):
    run = store.get_current_coach_analysis_run(project_id)
    if run is None:
        raise ValueError("coach analysis not found")
    if run.status == "completed":
        current_fingerprint = compute_source_fingerprint(store.list_documents(project_id))
        if current_fingerprint != run.source_fingerprint:
            store.mark_coach_analysis_stale(project_id)
            run = store.get_current_coach_analysis_run(project_id)
    return run


def _build_knowledge_points(
    documents: list[Document],
) -> tuple[list[dict[str, Any]], list[str]]:
    points: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []
    specialized = False

    for document in documents:
        path = _normalized_path(document.relative_path)
        name = PurePosixPath(path).name.lower()
        suffix = PurePosixPath(path).suffix.lower()
        content_lower = document.content.lower()

        if name.startswith("readme"):
            _add_point(
                points,
                "project:overview",
                "项目说明",
                "project",
                "项目包含可用于理解目标与使用方式的说明文档。",
                _source(document, _first_meaningful_excerpt(document.content), {"kind": "text", "line_start": 1}),
                (),
            )

        if suffix == ".py":
            specialized = True
            _add_point(
                points,
                "language:python",
                "Python 代码",
                "language",
                "项目包含 Python 模块。",
                _source(document),
                ("language:python",),
            )
            try:
                tree = ast.parse(document.content)
            except SyntaxError:
                warnings.append(f"{path} Python AST 解析失败，已使用文本规则")
                tree = None
            tokens = _python_tokens(tree, content_lower)
            _add_detected_technology_points(points, document, tokens)
            if _python_entrypoint(tree, content_lower):
                _add_point(
                    points,
                    f"entrypoint:{document.id}",
                    f"Python 入口：{path}",
                    "architecture",
                    "该文件包含可识别的 Python 或 Web 应用入口。",
                    _source(document, locator={"kind": "python", "symbol": "__main__|app"}),
                    ("language:python",),
                )

        if suffix in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue"}:
            specialized = True
            language_key = "language:typescript" if suffix in {".ts", ".tsx"} else "language:javascript"
            language_name = "TypeScript" if language_key.endswith("typescript") else "JavaScript"
            _add_point(
                points,
                language_key,
                f"{language_name} 代码",
                "language",
                f"项目包含 {language_name} 模块。",
                _source(document),
                (language_key,),
            )
            _add_detected_technology_points(
                points,
                document,
                _text_tokens(content_lower, (*_FRAMEWORK_RULES, *_TEST_RULES, "typescript")),
            )

        if name == "package.json":
            specialized = True
            _analyze_package_json(points, document, warnings)
        elif name == "pyproject.toml" or (
            name.startswith("requirements") and suffix == ".txt"
        ):
            specialized = True
            _analyze_python_manifest(points, document, warnings)
        elif name.startswith("tsconfig") and suffix == ".json":
            specialized = True
            _add_point(
                points,
                "language:typescript",
                "TypeScript 配置",
                "language",
                "项目通过 TypeScript 配置声明编译边界。",
                _source(document, locator={"kind": "manifest", "pointer": "/compilerOptions"}),
                ("language:typescript",),
            )

        if name == "dockerfile" or name.startswith("dockerfile.") or name == "compose.yaml" or name == "compose.yml" or "docker-compose" in name:
            specialized = True
            _add_point(
                points,
                "delivery:docker",
                "容器化交付",
                "delivery",
                "项目包含 Docker 或 Compose 交付清单。",
                _source(document),
                ("delivery:docker",),
            )

        if suffix == ".sql" or "sqlite" in content_lower or "sqlalchemy" in content_lower:
            specialized = True
            _add_detected_technology_points(
                points,
                document,
                {token for token in ("sqlite", "sqlalchemy") if token in content_lower},
            )

        if any(token in content_lower for token in ("retrieval augmented", "rag", "embedding", "vector search")):
            specialized = True
            _add_point(
                points,
                "ai:rag",
                "RAG 与检索增强",
                "ai",
                "项目资料包含检索增强、向量或嵌入相关实现。",
                _source(document),
                ("ai:rag",),
            )
        if any(token in content_lower for token in ("openai", "ollama", "llm", "deepseek")):
            specialized = True
            _add_point(
                points,
                "ai:llm",
                "LLM 集成",
                "ai",
                "项目资料包含 LLM provider 或模型调用相关实现。",
                _source(document),
                ("ai:llm",),
            )

    structure_sources = [
        _source(document, excerpt=_first_meaningful_excerpt(document.content))
        for document in documents[:8]
    ]
    _add_point(
        points,
        "project:structure",
        "项目资料结构",
        "project",
        f"当前分析覆盖 {len(documents)} 份已导入项目资料。",
        structure_sources,
        (),
    )

    if not specialized:
        for document in _generic_documents(documents)[:12]:
            _add_point(
                points,
                f"document:{document.id}:overview",
                f"资料理解：{document.relative_path}",
                "documentation",
                "该资料是当前项目理解的可追溯来源。",
                _source(document, _first_meaningful_excerpt(document.content)),
                (),
            )

    return sorted(points.values(), key=lambda item: (str(item["category"]), str(item["stable_key"]))), warnings


def _analyze_package_json(
    points: dict[str, dict[str, Any]],
    document: Document,
    warnings: list[str],
) -> None:
    try:
        manifest = json.loads(document.content)
    except json.JSONDecodeError:
        warnings.append(f"{document.relative_path} JSON 解析失败，已使用文本规则")
        manifest = {}
    if not isinstance(manifest, dict):
        manifest = {}
    dependency_names: set[str] = set()
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        values = manifest.get(key)
        if isinstance(values, dict):
            dependency_names.update(str(name).lower() for name in values)
    text_tokens = dependency_names | _text_tokens(
        document.content.lower(),
        (*_FRAMEWORK_RULES, *_TEST_RULES, "typescript"),
    )
    _add_point(
        points,
        "language:javascript",
        "JavaScript 工程",
        "language",
        "项目通过 package.json 声明 JavaScript 依赖或脚本。",
        _source(document, locator={"kind": "manifest", "pointer": "/"}),
        ("language:javascript",),
    )
    if "typescript" in text_tokens:
        _add_point(
            points,
            "language:typescript",
            "TypeScript 工程",
            "language",
            "项目依赖或配置包含 TypeScript。",
            _source(document, locator={"kind": "manifest", "pointer": "/devDependencies/typescript"}),
            ("language:typescript",),
        )
    _add_detected_technology_points(points, document, text_tokens, locator_kind="manifest")
    scripts = manifest.get("scripts")
    if isinstance(scripts, dict) and scripts:
        _add_point(
            points,
            "workflow:package-scripts",
            "前端工程脚本",
            "delivery",
            "package.json 定义了可执行的开发、测试或构建脚本。",
            _source(document, locator={"kind": "manifest", "pointer": "/scripts"}),
            ("delivery:package-scripts",),
        )


def _analyze_python_manifest(
    points: dict[str, dict[str, Any]],
    document: Document,
    warnings: list[str],
) -> None:
    content_lower = document.content.lower()
    _add_point(
        points,
        "language:python",
        "Python 工程",
        "language",
        "项目通过 Python 清单声明依赖或构建信息。",
        _source(document, locator={"kind": "manifest", "key": "dependencies"}),
        ("language:python",),
    )
    tokens = _text_tokens(content_lower, (*_FRAMEWORK_RULES, *_TEST_RULES, "sqlite", "sqlalchemy"))
    _add_detected_technology_points(points, document, tokens, locator_kind="manifest")
    if document.relative_path.lower().endswith(".toml"):
        try:
            import tomllib

            parsed = tomllib.loads(document.content)
            if not isinstance(parsed, dict):
                warnings.append(f"{document.relative_path} TOML 根节点无效，已使用文本规则")
        except (ImportError, ValueError):
            warnings.append(f"{document.relative_path} TOML 解析失败，已使用文本规则")


def _add_detected_technology_points(
    points: dict[str, dict[str, Any]],
    document: Document,
    tokens: set[str],
    locator_kind: str = "text",
) -> None:
    for token, (stable_key, title, category) in _FRAMEWORK_RULES.items():
        if token in tokens:
            _add_point(
                points,
                stable_key,
                title,
                category,
                f"项目来源明确引用 {title}。",
                _source(document, locator={"kind": locator_kind, "token": token}),
                (stable_key,),
            )
    for token, (stable_key, title) in _TEST_RULES.items():
        if token in tokens:
            _add_point(
                points,
                stable_key,
                title,
                "testing",
                f"项目来源明确引用 {title} 测试工具。",
                _source(document, locator={"kind": locator_kind, "token": token}),
                (stable_key,),
            )
    if "sqlite" in tokens:
        _add_point(
            points,
            "data:sqlite",
            "SQLite 数据存储",
            "data",
            "项目来源明确引用 SQLite。",
            _source(document, locator={"kind": locator_kind, "token": "sqlite"}),
            ("data:sqlite",),
        )
    if "sqlalchemy" in tokens:
        _add_point(
            points,
            "data:sqlalchemy",
            "SQLAlchemy 数据访问",
            "data",
            "项目来源明确引用 SQLAlchemy。",
            _source(document, locator={"kind": locator_kind, "token": "sqlalchemy"}),
            ("data:sqlalchemy",),
        )


def _build_skill_mappings(points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mappings: list[dict[str, Any]] = []
    for point in points:
        sources = point.get("sources") or []
        if not sources:
            continue
        source = sources[0]
        confidence = _source_confidence(source)
        for skill_key in point.pop("_skill_keys", []):
            mappings.append(
                {
                    "knowledge_point_key": point["stable_key"],
                    "skill_key": skill_key,
                    "confidence": confidence,
                    "rationale": f"{point['title']} 与技能节点 {skill_key} 由同一项目来源支撑。",
                    "source_path": source["source_path"],
                    "source_hash": source["source_hash"],
                    "source_locator": source["locator"],
                }
            )
    return mappings


def _add_point(
    points: dict[str, dict[str, Any]],
    stable_key: str,
    title: str,
    category: str,
    summary: str,
    sources: Mapping[str, Any] | Iterable[Mapping[str, Any]],
    skill_keys: Iterable[str],
) -> None:
    source_list = [sources] if isinstance(sources, Mapping) else list(sources)
    existing = points.get(stable_key)
    if existing is None:
        existing = {
            "stable_key": stable_key,
            "title": title,
            "category": category,
            "summary": summary,
            "sources": [],
            "_skill_keys": [],
        }
        points[stable_key] = existing
    known_sources = {
        (item.get("document_id"), json.dumps(item.get("locator", {}), sort_keys=True, ensure_ascii=False))
        for item in existing["sources"]
    }
    for source in source_list:
        signature = (
            source.get("document_id"),
            json.dumps(source.get("locator", {}), sort_keys=True, ensure_ascii=False),
        )
        if signature not in known_sources:
            existing["sources"].append(dict(source))
            known_sources.add(signature)
    for skill_key in skill_keys:
        if skill_key not in existing["_skill_keys"]:
            existing["_skill_keys"].append(skill_key)


def _source(
    document: Document,
    excerpt: str = "",
    locator: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    clean_excerpt = excerpt.strip() or _first_meaningful_excerpt(document.content)
    if not clean_excerpt:
        clean_excerpt = document.relative_path
    return {
        "document_id": document.id,
        "source_path": document.relative_path,
        "source_hash": document.checksum,
        "excerpt": clean_excerpt[:600],
        "locator": dict(locator or _line_locator(document.content, clean_excerpt)),
    }


def _line_locator(content: str, excerpt: str) -> dict[str, Any]:
    first_line = excerpt.splitlines()[0].strip() if excerpt else ""
    line_start = 1
    if first_line:
        for index, line in enumerate(content.splitlines(), start=1):
            if first_line in line:
                line_start = index
                break
    return {"kind": "line", "line_start": line_start, "line_end": line_start}


def _python_tokens(tree: ast.AST | None, content_lower: str) -> set[str]:
    tokens = _text_tokens(content_lower, (*_FRAMEWORK_RULES, *_TEST_RULES, "sqlite", "sqlalchemy"))
    if tree is None:
        return tokens
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            tokens.update(alias.name.split(".")[0].lower() for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            tokens.add(node.module.split(".")[0].lower())
    return tokens


def _python_entrypoint(tree: ast.AST | None, content_lower: str) -> bool:
    if 'if __name__ == "__main__"' in content_lower or "if __name__ == '__main__'" in content_lower:
        return True
    if tree is None:
        return "fastapi(" in content_lower or "flask(" in content_lower
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id in {"app", "application"}
            for target in node.targets
        ):
            return True
    return False


def _text_tokens(content_lower: str, candidates: Iterable[str]) -> set[str]:
    return {
        token
        for token in candidates
        if re.search(rf"(?<![\w-]){re.escape(token.lower())}(?![\w-])", content_lower)
    }


def _first_meaningful_excerpt(content: str) -> str:
    lines = [line.strip(" \t#>*-") for line in content.splitlines()]
    clean = [line for line in lines if line]
    return "\n".join(clean[:3])[:600]


def _generic_documents(documents: list[Document]) -> list[Document]:
    preferred = [
        document
        for document in documents
        if PurePosixPath(document.relative_path).suffix.lower() in {".md", ".txt"}
        or "/docs/" in f"/{_normalized_path(document.relative_path).lower()}/"
    ]
    return preferred or documents


def _signals(points: list[dict[str, Any]]) -> dict[str, list[str]]:
    signals: dict[str, list[str]] = {
        "languages": [],
        "frameworks": [],
        "data": [],
        "testing": [],
        "delivery": [],
        "ai": [],
    }
    key_map = {
        "language": "languages",
        "framework": "frameworks",
        "data": "data",
        "testing": "testing",
        "delivery": "delivery",
        "ai": "ai",
    }
    for point in points:
        target = key_map.get(str(point["category"]))
        if target and str(point["title"]) not in signals[target]:
            signals[target].append(str(point["title"]))
    return signals


def _rule_overview(documents: list[Document], signals: Mapping[str, list[str]]) -> str:
    detected = []
    for label, key in (
        ("语言", "languages"),
        ("框架", "frameworks"),
        ("数据", "data"),
        ("测试", "testing"),
        ("交付", "delivery"),
        ("AI", "ai"),
    ):
        values = signals.get(key) or []
        if values:
            detected.append(f"{label}：{'、'.join(values)}")
    suffix = "；".join(detected) if detected else "未从当前资料识别出专用技术信号"
    return f"已基于 {len(documents)} 份项目资料生成规则分析。{suffix}。"


def _enhance_summary(
    summary: dict[str, Any],
    documents: list[Document],
    llm_client: Any | None,
) -> None:
    if llm_client is None:
        return
    generate = getattr(llm_client, "generate_answer", None)
    if not callable(generate):
        summary["warning"] = _append_warning(summary.get("warning", ""), "LLM 摘要增强不可用，已保留规则结果")
        return
    try:
        hits = [
            SearchHit(document=document, score=1.0, snippet=_first_meaningful_excerpt(document.content))
            for document in documents[:5]
        ]
        enhanced = str(
            generate(
                "请仅基于来源，用一段中文概括该项目的用途、技术结构与学习重点；不要新增来源中没有的事实。",
                hits,
            )
            or ""
        ).strip()
        if enhanced:
            summary["overview"] = enhanced
            summary["enhancement_mode"] = "model"
    except Exception as exc:
        summary["warning"] = _append_warning(
            summary.get("warning", ""),
            f"LLM 摘要增强失败，已使用规则结果：{type(exc).__name__}",
        )


def _append_warning(current: object, warning: str) -> str:
    clean = str(current or "").strip()
    return f"{clean}；{warning}" if clean else warning


def _source_confidence(source: Mapping[str, Any]) -> float:
    kind = str((source.get("locator") or {}).get("kind", ""))
    if kind == "manifest":
        return 1.0
    if kind in {"python", "line"}:
        return 0.9
    return 0.6


def _source_index(points: Iterable[Any]) -> dict[str, dict[str, Any]]:
    sources: dict[str, dict[str, Any]] = {}
    for point in points:
        for source in point.sources:
            payload = source.to_dict()
            payload["path"] = payload.pop("source_path")
            sources[source.id] = payload
    return sources


def _normalized_path(path: str) -> str:
    return PurePosixPath(path.replace("\\", "/")).as_posix().lower()


__all__ = [
    "ANALYZER_VERSION",
    "SKILL_NODES",
    "SKILL_TAXONOMY",
    "analyze_project",
    "build_coach_overview",
    "build_knowledge_points_view",
    "build_skills_view",
    "compute_source_fingerprint",
    "current_coach_analysis",
]
