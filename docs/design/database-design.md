# 数据库设计

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-21
> Scope：SQLite 及向量模型存储边界

## 1. 当前已落地实体

以下实体在本轮数据库 schema 中可用，含历史兼容字段：

- `projects`
- `documents`
- `document_chunks`（Web MVP）
- `chunk_vectors`（Web MVP）
- `chat_messages`（Web MVP）
- `chunks`
- `workspaces`
- `tasks`
- `conversations`
- `tags`
- `document_tags`
- `sources`
- `skill_areas`
- `knowledge_points`
- `evidences`
- `mastery_records`
- `graph_nodes`
- `graph_edges`

## 2. 字段要点

### documents
- `id / project_id / workspace_id / source_path / source_type`
- `raw_content / normalized_markdown / plain_text / rendered_html`
- `created_at / updated_at / content / domain / tags`（兼容字段）

### chunks
- `id / document_id / project_id / workspace_id / chunk_index`
- `chunk_markdown / chunk_plain_text / heading_path / token_count / embedding_id / order`

### document_chunks（Web MVP）
- `id / document_id / project_id / chunk_index`
- `content / token_count / created_at`
- 用于本地 Web MVP 的轻量 RAG 分块检索；legacy `chunks` 表继续服务旧应用层和向量检索链路。

### chunk_vectors（Web MVP）
- `chunk_id / project_id / vector_json / provider / model / updated_at`
- `chunk_id` 与 `document_chunks.id` 一一对应，用于 Web MVP keyword + vector 混合召回。
- `provider/model` 记录向量来源；配置 OpenAI-compatible Embeddings 时写入真实 embedding，否则写入本地 hashing 向量。

### chat_messages（Web MVP）
- `id / project_id / question / answer / mode / provider / warning / sources_json / created_at`
- 每次 `/api/answer` 返回后写入一条记录，用于 Web 工作台按项目恢复最近问答。
- `sources_json` 保存本轮回答使用的来源片段快照，避免后续文档更新导致历史对话失去当时来源。

### mastery_records
- `status` 三态：`claimed / evidence_found / verified`

### graph_edges
- `source_node_id`、`target_node_id`、`relationship`、`confidence`

## 3. 约束与策略

- 外键删除采用 SQLite 外键级联，清理文档时联动 chunk/source/关系。
- Web MVP 删除或重建文档时会同步删除并重建 `document_chunks`，避免旧 chunk 残留影响检索来源。
- Web MVP 删除或重建 `document_chunks` 时级联清理 `chunk_vectors`，并在同一写入流程中重建向量。Embedding API 失败时回退本地 hashing，不阻断文档入库。
- Web MVP 删除项目空间时通过外键级联清理 `chat_messages`，避免孤立聊天记录。
- 增量摄入中会按 `document_id` 删除旧数据，防止重建重复。
- 向量库侧与 `chunks.id` 保持一一对应便于回填来源。

## 4. 当前不在定稿范围

- 文档里列出的未来模型（如部分学习建议图谱扩展字段）若未落库，不在定稿内扩展为新约束。
