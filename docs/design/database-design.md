# 数据库设计

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-24
> Scope：Web MVP SQLite 存储与 legacy 数据模型边界

## 1. 当前已落地实体

当前默认交付形态是本地 Web MVP，其运行时直接使用 `webapp/storage.py` 初始化和读写 SQLite。下列实体中标注 Web MVP 的表是当前默认入口会直接使用的表；未标注 Web MVP 的实体主要服务 legacy 分层代码或历史兼容，不代表 Web MVP 已完成对应 UI 闭环。

- `projects`
- `documents`
- `document_chunks`（Web MVP）
- `chunk_vectors`（Web MVP）
- `prompt_presets`（Web MVP）
- `chat_sessions`（Web MVP）
- `chat_messages`（Web MVP）
- `answer_feedback`（Web MVP）
- `agent_tool_runs`（Web MVP）
- `retrieval_reviews`（Web MVP）
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

### projects（Web MVP）
- `id / name / root_path / created_at`
- 项目级检索默认值：`retrieval_top_k / retrieval_min_score / retrieval_use_keyword / retrieval_use_vector`
- 项目级默认 Prompt 预设：`default_prompt_preset_id`
- `root_path` 可为真实目录，也可为浏览器上传创建的虚拟根，例如 `browser-upload:<name>`。

### prompt_presets（Web MVP）
- `id / project_id / name / description / system_prompt / answer_format / created_at / updated_at`
- 保存当前项目空间可选的 Prompt 预设，用于真实 LLM 回答风格和回答结构。
- 不保存 API Key、模型凭证、检索参数或工具权限配置。
- 删除项目空间时级联清理；删除预设时会清空当前项目引用的默认预设。

### documents
- `id / project_id / workspace_id / source_path / source_type`
- `raw_content / normalized_markdown / plain_text / rendered_html`
- `created_at / updated_at / content / domain / tags`（兼容字段）

### chunks（legacy）
- `id / document_id / project_id / workspace_id / chunk_index`
- `chunk_markdown / chunk_plain_text / heading_path / token_count / embedding_id / order`
- 服务旧应用层和 legacy 向量检索链路，不是 Web MVP 当前检索的默认 chunk 表。

### document_chunks（Web MVP）
- `id / document_id / project_id / chunk_index`
- `content / token_count / created_at`
- 用于本地 Web MVP 的轻量 RAG 分块检索；legacy `chunks` 表继续服务旧应用层和向量检索链路。

### chunk_vectors（Web MVP）
- `chunk_id / project_id / vector_json / provider / model / updated_at`
- `chunk_id` 与 `document_chunks.id` 一一对应，用于 Web MVP keyword + vector 混合召回。
- `provider/model` 记录向量来源；配置 OpenAI-compatible Embeddings 时写入真实 embedding，否则写入本地 hashing 向量。

### chat_sessions（Web MVP）
- `id / project_id / title / created_at / updated_at`
- 表示当前项目空间下的聊天主题。
- 删除项目空间时级联清理；删除会话时清理该会话下的 `chat_messages`。

### chat_messages（Web MVP）
- `id / project_id / session_id / question / answer / mode / provider / warning / sources_json / created_at`
- 每次 `/api/answer` 返回后写入一条记录，用于 Web 工作台按项目恢复最近问答。
- `session_id` 可为空；为空时归入默认会话，用于兼容历史消息。
- `sources_json` 保存本轮回答使用的来源片段快照，避免后续文档更新导致历史对话失去当时来源。

### answer_feedback（Web MVP）
- `id / project_id / message_id / rating / note / created_at`
- 保存用户对本地回答质量的反馈，用于后续人工复盘；不调用外部服务，不自动调整检索或模型参数。
- `rating` 只允许 `useful / not_useful / source_wrong / need_more_context`。

### agent_tool_runs（Web MVP）
- `id / project_id / tool_name / arguments_json / result_json / status / error / created_at`
- 记录 Agent 只读工具调用审计；当前用于 `project_overview` 和未知工具拒绝记录。
- `arguments_json` 与 `result_json` 只保存工具调用参数和摘要结果，不保存 API Key。

### retrieval_reviews（Web MVP）
- `id / project_id / query / parameters_json / hits_json / quality_json / note / created_at`
- 保存一次检索复盘快照，用于记录当时的检索参数、命中来源、来源质量和人工备注。
- `hits_json` 保存命中片段快照，避免后续文档更新导致复盘记录失去当时上下文。

### mastery_records
- `status` 三态：`claimed / evidence_found / verified`

### graph_edges
- `source_node_id`、`target_node_id`、`relationship`、`confidence`

## 3. 约束与策略

- 外键删除采用 SQLite 外键级联，清理文档时联动 chunk/source/关系。
- Web MVP 删除或重建文档时会同步删除并重建 `document_chunks`，避免旧 chunk 残留影响检索来源。
- Web MVP 删除或重建 `document_chunks` 时级联清理 `chunk_vectors`，并在同一写入流程中重建向量。Embedding API 失败时回退本地 hashing，不阻断文档入库。
- Web MVP 删除项目空间时通过外键级联清理 `chat_messages`，避免孤立聊天记录。
- Web MVP 删除项目空间或聊天消息时通过外键级联清理 `answer_feedback`，避免孤立回答反馈。
- Web MVP 删除项目空间时通过外键级联清理 `agent_tool_runs`，避免孤立工具审计记录。
- Web MVP 删除项目空间时通过外键级联清理 `retrieval_reviews`，避免孤立检索复盘记录。
- Web MVP 项目级检索默认值直接随 `projects` 记录保存，删除项目空间时一并消失；不会影响其他项目空间。
- Web MVP Prompt 预设按项目隔离保存；默认预设只保存预设 ID，不影响其他项目，也不改变检索设置。
- Web MVP 增量摄入中会按 `document_id` 删除旧 `document_chunks` 与 `chunk_vectors`，防止重建重复。
- legacy 向量库侧与 `chunks.id` 保持一一对应便于回填来源。

## 4. 当前不在定稿范围

- 文档里列出的未来模型（如部分学习建议图谱扩展字段）若未落库，不在定稿内扩展为新约束。
