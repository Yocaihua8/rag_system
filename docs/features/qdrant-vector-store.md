# Qdrant 向量存储

> 状态：Draft（B-134 执行中）
> Owner：RAG 团队
> Last Updated：2026-06-28
> Related：docs/design/architecture-overview.md, docs/design/database-design.md, docs/design/api-spec.md, docs/adr/ADR-007-qdrant-vector-store.md

## 1. 功能目标

B-134 目标是将 Web MVP 检索链路中的向量相似度全量 SQLite 扫描替换为 Qdrant 本地模式检索，降低大文档库（> 5000 chunks）下的查询成本。

## 2. 当前状态

实现进行中，正式行为以 B-134 完成后的本文档更新为准。

## 3. 待确认 / 待落地

- Qdrant 本地存储路径、collection 命名和可配置项。
- 文档摄入、更新、删除时向量索引同步规则。
- Qdrant 不可用或未安装时的降级行为。
- `/api/search` 与 `/api/search/debug` 的响应字段兼容范围。

## 4. 架构落点

- Provider 层：`backend/providers/vector_store/`
- 过渡期集成点：`webapp/storage.py`、`webapp/search.py`
- 正式设计文档：`docs/design/architecture-overview.md`
- 架构决策记录：`docs/adr/ADR-007-qdrant-vector-store.md`
