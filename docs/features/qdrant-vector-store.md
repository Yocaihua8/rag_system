# Qdrant 向量存储

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-06-28
> Related：docs/design/architecture-overview.md, docs/design/database-design.md, docs/design/api-spec.md, docs/adr/ADR-007-qdrant-vector-store.md

## 1. 功能目标

B-134 目标是将 Web MVP 检索链路中的向量相似度全量 SQLite 扫描替换为 Qdrant 本地模式检索，降低大文档库（> 5000 chunks）下的查询成本。

## 2. 启用方式

默认仍使用 SQLite `chunk_vectors` 兼容路径。启用 Qdrant 需要设置：

```text
RAG_VECTOR_STORE_PROVIDER=qdrant
RAG_QDRANT_PATH=<本地 Qdrant 持久化目录>
RAG_QDRANT_COLLECTION=knowledge_island_chunks
RAG_QDRANT_VECTOR_SIZE=96
```

未设置 `RAG_VECTOR_STORE_PROVIDER=qdrant` 时，`backend.config.vector_store.build_vector_store()` 返回 `None`，搜索继续走 SQLite fallback。

## 3. 写入与同步规则

- 文档入库、更新和备份恢复会继续写入 SQLite `document_chunks` / `chunk_vectors`。
- 启用 Qdrant 时，同一写入流程会把 chunk 向量同步 upsert 到 Qdrant collection。
- 文档更新会删除旧 chunk 对应的 Qdrant point，再写入新 chunk point。
- 删除单文档、目录同步删除缺失文档、删除项目空间时，会同步删除对应 Qdrant point。
- Qdrant 写入或删除失败只打印 `WARNING`，不回滚 SQLite 写入；SQLite 仍是兼容数据和降级来源。

## 4. 检索规则

- `search_documents()` 默认读取 `backend.config.vector_store.get_default_vector_store()`。
- 启用 Qdrant 且可用时，向量候选由 Qdrant `query_points` 返回，避免查询时遍历 SQLite `chunk_vectors`。
- BM25 keyword 仍在本地 chunk 列表上计算，最终候选为 keyword 候选与 Qdrant vector 候选的并集。
- Qdrant 未启用、未安装或查询失败时，搜索回退到 SQLite `chunk_vectors` + cosine similarity，保持现有结果字段。

## 5. API 兼容性

`/api/search`、`/api/search/debug`、`/api/answer` 不新增请求参数，也不改变现有响应字段。命中结果继续返回：

- `retrieval`
- `keyword_score`
- `vector_score`
- `vector_provider`
- `vector_model`
- `rerank_score`
- `chunk_id`
- `chunk_index`

`vector_provider` 和 `vector_model` 表示 embedding 来源，不表示 Qdrant 本身。

## 6. 架构落点

- Provider 层：`backend/providers/vector_store/`
- 过渡期集成点：`webapp/storage.py`、`webapp/search.py`
- 正式设计文档：`docs/design/architecture-overview.md`
- 架构决策记录：`docs/adr/ADR-007-qdrant-vector-store.md`

## 7. 验证范围

- `tests/test_backend/test_qdrant_vector_store.py`
- `tests/test_webapp/test_vector_store_sync.py`
- `tests/test_webapp/test_search.py`
- `tests/test_webapp/test_api.py`
