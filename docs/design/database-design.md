# 数据库设计

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-06-29
> Scope：Web MVP SQLite 存储与 legacy 数据模型边界

## 1. 当前已落地实体

当前默认交付形态是本地 Web MVP，其运行时直接使用 `backend/storage/knowledge_store.py` 初始化和读写 SQLite。下列实体中标注 Web MVP 的表是当前默认入口会直接使用的表；未标注 Web MVP 的实体主要服务 legacy 分层代码或历史兼容，不代表 Web MVP 已完成对应 UI 闭环。

- `projects`
- `documents`
- `document_collections`（Web MVP）
- `document_collection_items`（Web MVP）
- `import_batches`（Web MVP）
- `import_batch_items`（Web MVP）
- `document_chunks`（Web MVP）
- `chunk_vectors`（Web MVP）
- `prompt_presets`（Web MVP）
- `model_profiles`（Web MVP）
- `chat_sessions`（Web MVP）
- `chat_messages`（Web MVP）
- `answer_feedback`（Web MVP）
- `assessment_questions`（Web MVP）
- `assessment_answers`（Web MVP）
- `assessment_results`（Web MVP）
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
- `graph_nodes`（legacy；Web MVP B-126 只读兼容）
- `graph_edges`（legacy；Web MVP B-126 只读兼容）

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

### model_profiles（Web MVP）
- `id / name / provider / api_base / model / temperature / max_tokens / api_key_ref / is_default / created_at / updated_at`
- 保存本机可复用的 LLM Profile，用于在 DeepSeek、OpenAI-compatible 或本地配置之间切换。
- `api_key_ref` 只保存受控引用，不保存 API Key 明文；当前允许空值、`env:RAG_LLM_API_KEY`、`env:DEEPSEEK_API_KEY`、`saved:RAG_LLM_API_KEY`。
- `is_default` 表示全局默认 Profile；同一时间由应用层保证最多一个默认 Profile。没有默认 Profile 时，Web 问答继续使用现有单配置 `load_settings()` 行为。

### documents
- `id / project_id / workspace_id / source_path / source_type`
- `raw_content / normalized_markdown / plain_text / rendered_html`
- `created_at / updated_at / content / domain / tags`（兼容字段）

### document_collections（Web MVP）
- `id / project_id / name / description / color / created_at / updated_at`
- 保存当前项目空间内的轻量文档集合，用于资料库列表过滤。
- 只保存集合元数据，不保存文档正文、chunk、vector、模型配置或 API Key。
- 删除项目空间时级联清理；删除集合时只清理集合和关联记录，不删除文档。

### document_collection_items（Web MVP）
- `id / project_id / collection_id / document_id / created_at`
- 保存集合与文档的关联关系，`UNIQUE(collection_id, document_id)` 防止同一文档重复加入同一集合。
- `collection_id` 指向 `document_collections.id`，`document_id` 指向 `documents.id`，删除集合或文档时级联清理关联。
- 应用层校验集合与文档必须属于同一 `project_id`，跨项目加入集合必须拒绝。

### import_batches（Web MVP）
- `id / project_id / source_type / status / started_at / finished_at / summary_json / message / created_at`
- 保存当前项目空间每次完成导入后的批次摘要，用于资料库页展示最近导入历史。
- `source_type` 支持 `directory_sync / browser_folder_upload / file_upload / text_note / url_excerpt`。
- `status` 支持 `success / partial / failed`；当前第一片主要记录已解析出项目且导入流程完成后的 `success/partial` 批次。
- `summary_json` 只保存 `imported/created/updated/unchanged/deleted/skipped/errors` 计数，不保存文档正文、上传原始内容、chunk/vector、API Key 或模型配置。
- 删除项目空间时级联清理批次。

### import_batch_items（Web MVP）
- `id / batch_id / project_id / kind / relative_path / document_id / reason / created_at`
- 保存批次明细，第一片主要用于查看 `skipped` 和 `error` 项；文本笔记和 URL 摘录也会记录当次文档写入项。
- `document_id` 不强外键绑定到 `documents.id`，避免后续删除文档后破坏历史批次可读性。
- 删除项目空间或批次时级联清理明细。

### chunks（legacy）
- `id / document_id / project_id / workspace_id / chunk_index`
- `chunk_markdown / chunk_plain_text / heading_path / token_count / embedding_id / order`
- 服务旧应用层和 legacy 向量检索链路，不是 Web MVP 当前检索的默认 chunk 表。

### conversations（legacy）
- `id / workspace_id / session_id / question / answer / created_at`
- 保存 legacy `QueryKnowledgeBaseUseCase` 的问答历史。
- `session_id` 为空字符串时表示默认 legacy 会话，用于兼容旧记录和未传会话的调用方。
- B-20 后，legacy 问答会按同一 `workspace_id + session_id` 读取最近 3 轮历史注入 prompt；不会读取其他会话历史。
- 索引：`idx_conversations_workspace_session_created(workspace_id, session_id, created_at)` 用于读取同一 workspace、同一会话的最近记录。

### document_chunks（Web MVP）
- `id / document_id / project_id / chunk_index`
- `content / token_count / created_at`
- 用于本地 Web MVP 的轻量 RAG 分块检索；legacy `chunks` 表继续服务旧应用层和向量检索链路。

### chunk_vectors（Web MVP）
- `chunk_id / project_id / vector_json / provider / model / updated_at`
- `chunk_id` 与 `document_chunks.id` 一一对应。
- B-134 后该表继续保存 Web MVP 向量兼容副本，用于备份恢复、项目健康统计和 Qdrant 未启用/不可用时的 SQLite fallback。
- 启用 `RAG_VECTOR_STORE_PROVIDER=qdrant` 时，查询时的向量候选由 Qdrant 本地索引返回，不再为了向量相似度遍历本表全量记录。
- `provider/model` 记录向量来源；配置 OpenAI-compatible Embeddings 时写入真实 embedding，否则写入本地 hashing 向量。

### chat_sessions（Web MVP）
- `id / project_id / title / created_at / updated_at`
- 表示当前项目空间下的聊天主题。
- 删除项目空间时级联清理；删除会话时清理该会话下的 `chat_messages`。

### chat_messages（Web MVP）
- `id / project_id / session_id / parent_message_id / branch_index / question / answer / mode / provider / warning / sources_json / created_at`
- 每次 `/api/answer` 返回后写入一条记录，用于 Web 工作台按项目恢复最近问答。
- `session_id` 可为空；为空时归入默认会话，用于兼容历史消息。
- `parent_message_id` 可为空；非空时表示本条消息来自历史消息编辑重发，并指向被编辑的父消息。
- `branch_index` 默认为 `0`；同一 `parent_message_id` 下的编辑重发消息按创建顺序递增。
- `sources_json` 保存本轮回答使用的来源片段快照，避免后续文档更新导致历史对话失去当时来源。

### answer_feedback（Web MVP）
- `id / project_id / message_id / rating / note / created_at`
- 保存用户对本地回答质量的反馈，用于后续人工复盘；不调用外部服务，不自动调整检索或模型参数。
- `rating` 只允许 `useful / not_useful / source_wrong / need_more_context`。

### assessment_questions（Web MVP）
- `id / project_id / source_path / question_type / knowledge_point / prompt / expected_points_json / reference_snippet / created_at`
- 保存从当前项目已导入文档生成的评估题，`question_type` 当前支持 `concept / flow / code_location`，`knowledge_point` 保存规则化提取出的轻量知识点标签，`expected_points_json` 保存规则评分使用的关键词要点。
- `source_path` 使用文档相对路径，便于结果页提示建议阅读来源；删除项目空间时级联清理。

### assessment_answers（Web MVP）
- `id / project_id / question_id / answer / created_at`
- 保存用户提交的评估回答，`question_id` 指向 `assessment_questions.id`。
- 删除题目或项目空间时级联清理回答。

### assessment_results（Web MVP）
- `id / project_id / question_id / answer_id / status / score / matched_points_json / missing_points_json / feedback / source_path / created_at`
- 保存一次回答评估结果，包含掌握状态、得分、命中要点、缺失要点、反馈文案和建议阅读来源。
- `status` 当前支持 `已掌握 / 基本理解 / 需要补充 / 暂未掌握`；评分使用服务端持久化题目的参考要点，避免前端篡改影响评估。

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

### graph_nodes（legacy；Web MVP B-126 只读兼容）
- `id / workspace_id / name / label / node_type / source_ref / confidence / created_at / updated_at`
- B-126 不在 Web MVP schema 中创建或迁移该表；仅当当前数据库已有该表时，`backend/storage/knowledge_store.py` 会只读查询。
- Web MVP 只读兼容时将 `workspace_id` 视为当前 `project_id`，并把 `source_ref` 尝试映射到当前项目的 `document_chunks.id`、`documents.id`、`documents.relative_path` 或 `documents.source_path`。

### graph_edges（legacy；Web MVP B-126 只读兼容）
- `id / workspace_id / source_node_id / target_node_id / relationship / confidence / source_path / source_snippet / created_at / updated_at`
- B-126 只读取一跳相邻关系，`confidence` 会作为检索结果的 `graph_score`。
- 图谱表不存在、字段不兼容或无法映射到 Web MVP chunk 时，检索流程保持原有 BM25 / 向量行为。

## 3. 约束与策略

- 外键删除采用 SQLite 外键级联，清理文档时联动 chunk/source/关系。
- Web MVP 删除或重建文档时会同步删除并重建 `document_chunks`，避免旧 chunk 残留影响检索来源。
- Web MVP 删除文档时通过外键级联清理 `document_collection_items`；删除集合不删除文档。
- Web MVP 删除项目空间时通过外键级联清理 `import_batches` 和 `import_batch_items`；导入批次历史不是备份，不提供回滚。
- Web MVP 删除或重建 `document_chunks` 时级联清理 `chunk_vectors`，并在同一写入流程中重建向量。启用 Qdrant 时，同步删除旧 point 并 upsert 新 point；Qdrant 同步失败只打印 `WARNING`，不阻断 SQLite 入库。
- Web MVP 删除项目空间时通过外键级联清理 `chat_messages`，避免孤立聊天记录。
- Web MVP 删除项目空间或聊天消息时通过外键级联清理 `answer_feedback`，避免孤立回答反馈。
- Web MVP 删除项目空间时通过外键级联清理 `assessment_questions`、`assessment_answers` 和 `assessment_results`；删除题目时级联清理对应回答与结果。
- Web MVP 删除项目空间时通过外键级联清理 `agent_tool_runs`，避免孤立工具审计记录。
- Web MVP 删除项目空间时通过外键级联清理 `retrieval_reviews`，避免孤立检索复盘记录。
- Web MVP 项目级检索默认值直接随 `projects` 记录保存，删除项目空间时一并消失；不会影响其他项目空间。
- Web MVP Prompt 预设按项目隔离保存；默认预设只保存预设 ID，不影响其他项目，也不改变检索设置。
- Web MVP 模型 Profile 是本机全局配置，不随项目删除；删除默认 Profile 时默认选择会消失，问答回退到现有单配置行为。
- Web MVP 增量摄入中会按 `document_id` 删除旧 `document_chunks` 与 `chunk_vectors`，并在启用 Qdrant 时删除旧 point，防止重建重复。
- Web MVP 备份恢复会把导出的 `documents.content`、`document_chunks` 和 `chunk_vectors` 写入新的项目空间，并为文档、chunk 生成新 ID；聊天来源中的旧 ID 会映射到新 ID。启用 Qdrant 时，恢复写入的 chunk 向量也会同步 upsert 到 Qdrant。
- legacy 向量库侧与 `chunks.id` 保持一一对应便于回填来源。
- Web MVP B-126 只读兼容 legacy `graph_nodes` / `graph_edges`，不会在 `_init_schema()` 中创建图谱表，也不会自动生成或修改图谱节点/关系。

## 4. 当前不在定稿范围

- 文档里列出的未来模型（如部分学习建议图谱扩展字段）若未落库，不在定稿内扩展为新约束。
