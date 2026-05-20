# 数据库设计

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-16
> Scope：SQLite 及向量模型存储边界

## 1. 当前已落地实体

以下实体在本轮数据库 schema 中可用，含历史兼容字段：

- `projects`
- `documents`
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

### mastery_records
- `status` 三态：`claimed / evidence_found / verified`

### graph_edges
- `source_node_id`、`target_node_id`、`relationship`、`confidence`

## 3. 约束与策略

- 外键删除采用 SQLite 外键级联，清理文档时联动 chunk/source/关系。
- 增量摄入中会按 `document_id` 删除旧数据，防止重建重复。
- 向量库侧与 `chunks.id` 保持一一对应便于回填来源。

## 4. 当前不在定稿范围

- 文档里列出的未来模型（如部分学习建议图谱扩展字段）若未落库，不在定稿内扩展为新约束。
