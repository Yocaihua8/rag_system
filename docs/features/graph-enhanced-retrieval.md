# Graph-enhanced 检索

> 状态：Draft
> Owner：RAG 团队
> Last Updated：2026-06-29
> Scope：B-126 知识图谱接入 Web MVP 检索流程
> Related：docs/design/database-design.md, docs/design/api-spec.md, docs/design/architecture-overview.md, docs/plans/B-126-graph-enhanced-retrieval.md

## 1. 功能目标

B-126 目标是在现有 Web MVP 混合检索链路上增加轻量知识图谱候选扩展：当当前数据库存在 B-48 legacy `graph_nodes` / `graph_edges` 表和图谱数据时，检索会基于命中 chunk 的关联图节点补充相邻节点对应的来源片段，提升多跳问题的召回能力。

## 2. 执行边界

- 不新增 HTTP API 请求参数。
- 不替换现有 BM25、向量检索、Qdrant 候选或 reranker。
- 不修改 Web MVP SQLite schema；当前实现只读兼容已有 `graph_nodes` / `graph_edges` 表。
- 当图谱表不存在、无图谱数据或无可映射来源时，检索结果保持现有行为。

## 3. 待回流内容

B-126 完成后，本文件会更新为正式行为说明，并同步 `docs/design/api-spec.md`、`docs/design/database-design.md` 与 `docs/design/architecture-overview.md`。
