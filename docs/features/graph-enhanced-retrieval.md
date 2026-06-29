# Graph-enhanced 检索

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-06-29
> Scope：B-126 知识图谱接入 Web MVP 检索流程
> Related：docs/design/database-design.md, docs/design/api-spec.md, docs/design/architecture-overview.md

## 1. 功能目标

B-126 在现有 Web MVP 混合检索链路上增加轻量知识图谱候选扩展：当当前 SQLite 数据库已经存在 B-48 legacy `graph_nodes` / `graph_edges` 表和图谱数据时，检索会基于基础命中 chunk 映射到图谱节点，再补充一跳相邻节点对应的来源 chunk，提升多跳问题的召回能力。

## 2. 启用条件

- 图谱表必须已存在于当前数据库中；Web MVP 不在本任务中创建或迁移 `graph_nodes` / `graph_edges`。
- `graph_nodes.workspace_id` 需与当前 `project_id` 一致。
- `graph_nodes.source_ref` 需能映射到当前项目的 `document_chunks.id`、`documents.id`、`documents.relative_path` 或 `documents.source_path`。
- 基础检索必须先产生 keyword 命中或启用的向量候选，图谱扩展只从这些 seed chunk 出发，不从全库 chunk 出发。

## 3. 检索规则

1. `search_documents()` 先执行既有 BM25 keyword、向量候选、Qdrant fallback 逻辑。
2. 对基础候选中已有关键词分数或向量候选记录的 chunk，调用 `KnowledgeStore.list_graph_related_chunks()` 做只读图谱查询。
3. 图谱查询按 `graph_edges` 查找一跳相邻节点，并把相邻节点 `source_ref` 映射到当前项目 chunk。
4. 图谱候选并入候选池后继续统一排序；如果启用了 reranker，reranker 会接收扩展后的候选池。
5. 当 graph 表不存在、字段不兼容、没有 seed 节点、没有相邻来源或相邻来源无法映射到 chunk 时，检索保持原有行为。

## 4. 响应字段

`/api/search`、`/api/search/debug`、`/api/answer` 和 `/api/answer/stream` 的 `hits` / `sources` 继续复用 `SearchHit.to_dict()`。B-126 新增字段：

| 字段 | 说明 |
|------|------|
| `graph_score` | 图谱扩展分数；当前取一跳边 `confidence`。非图谱候选为 `0.0` |
| `graph_depth` | 图谱扩展深度；当前只支持一跳，值为 `1`；非图谱候选为 `null` |

图谱候选仅由图谱召回时，`retrieval` 为 `graph`；如果同一 chunk 同时有 keyword/vector 和图谱分数，`retrieval` 会追加 `+graph`，例如 `hybrid+graph`。

## 5. 边界

- 不新增 HTTP API 请求参数。
- 不替换现有 BM25、向量检索、Qdrant 候选或 reranker。
- 不修改 Web MVP SQLite schema。
- 不自动生成图谱节点或关系。
- 不做二跳以上自动遍历，避免在本地 MVP 中引入不可控召回噪声。
