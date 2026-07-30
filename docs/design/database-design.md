# 数据库设计

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-07-30
> Scope：Knowledge Island v2.0.0 当前 SQLite Schema、2.0 数据代际与只读 legacy 兼容边界
> Related：docs/design/architecture-overview.md, docs/adr/ADR-008-project-knowledge-coach-v2.md, docs/adr/ADR-009-obsidian-plugin-bridge.md

> 阅读边界：§ 1 是当前源码会初始化的完整表清单；§ 2～§ 4 保留核心表和 legacy 兼容字段的详细说明；§ 5～§ 7 描述 v2 数据代际、Coach 与 Obsidian Bridge。历史实体不等于当前 Schema。

## 1. 当前已落地实体

当前入口通过 `KnowledgeStore` 组合四个 storage 模块，共初始化 37 张表。API 和业务层不得直接操作 SQLite。

| 分组 | 初始化模块 | 当前表 |
|------|------------|--------|
| 核心知识库与问答（19） | `backend/storage/knowledge_store.py` | `app_metadata`、`projects`、`prompt_presets`、`model_profiles`、`documents`、`document_collections`、`document_collection_items`、`import_batches`、`import_batch_items`、`document_chunks`、`chunk_vectors`、`chat_sessions`、`chat_messages`、`answer_feedback`、`assessment_questions`、`assessment_answers`、`assessment_results`、`agent_tool_runs`、`retrieval_reviews` |
| Coach 分析与技能映射（6） | `backend/storage/coach_store.py` | `coach_analysis_runs`、`coach_knowledge_points`、`coach_knowledge_sources`、`coach_skill_taxonomies`、`coach_skill_nodes`、`coach_knowledge_skill_mappings` |
| Coach 评估与学习计划（6） | `backend/storage/coach_progress_store.py` | `coach_assessment_sessions`、`coach_assessment_questions`、`coach_assessment_answers`、`coach_assessment_results`、`coach_learning_plans`、`coach_learning_plan_items` |
| Obsidian Bridge（6） | `backend/storage/obsidian_store.py` | `obsidian_pairings`、`obsidian_connections`、`obsidian_sync_events`、`obsidian_publications`、`obsidian_publication_revisions`、`obsidian_publication_results` |

`graph_nodes` 和 `graph_edges` 不在当前 `_init_schema()` 中创建；仅当既有数据库已包含兼容表结构时，检索链路才做条件式只读查询。`chunks`、`workspaces`、`tasks`、`conversations`、`tags`、`document_tags`、`sources`、`skill_areas`、`knowledge_points`、`evidences`、`mastery_records` 等名称属于历史模型说明，不得据此推断当前数据库会创建这些表。

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

## 5. 2.0 数据代际（B-161 已实现）

2.0 使用独立数据根 `runtime/v2/`，默认 SQLite 为 `runtime/v2/app.db`；向量索引、日志和输出也必须派生到该代际下。现有 `runtime/app.db`、`runtime/vectors/`、既有 Qdrant 路径、`runtime/outputs/` 及其他 1.x 运行时文件不得迁移、删除或覆盖。

- 当前应用默认读写 `runtime/v2/`，SQLite 为 `runtime/v2/app.db`，Qdrant 本地索引为 `runtime/v2/vectors/qdrant/`。
- 2.0 首次启动创建全新 schema，并写入 `app_metadata.data_generation=v2`；用户需要重新导入项目。
- 2.0 不自动读取 1.x 数据，也不提供隐式 schema 升级。
- 生产 `create_app` 在建表、补列和向量初始化前验证数据代际；配置指向既有非 v2 数据库时只读拒绝，不能原地建表。
- 1.x 数据保留用于原版本回退或人工归档；删除必须是独立、显式的维护动作。

## 6. 2.0 Coach 逻辑实体

为避免与 1.x/legacy 的 `knowledge_points`、`assessment_*` 混淆，2.0 新实体统一使用 `coach_` 前缀。B-161 已落地分析、知识点、来源与技能映射六张表；B-162 已落地评估与学习计划六张表。

| 表 | 状态 | 核心字段 / 约束 | 职责 |
|--------|------|-----------------|------|
| `coach_analysis_runs` | B-161 已实现 | `id / project_id / analyzer_version / source_fingerprint / status / summary_json / started_at / finished_at` | 保存不可变分析运行；`status` 为 `pending / running / completed / failed / stale` |
| `coach_knowledge_points` | B-161 已实现 | `id / project_id / stable_key / title / category / summary / current_run_id / created_at / updated_at`；`UNIQUE(project_id, stable_key)` | 保存跨重新分析稳定的项目知识点身份 |
| `coach_knowledge_sources` | B-161 已实现 | `id / run_id / knowledge_point_id / document_id / source_path / chunk_id / source_hash / excerpt / locator_json` | 为知识点、映射和结论保存真实来源快照 |
| `coach_skill_taxonomies` | B-161 已实现 | `id / version / name / status / created_at`；`version` 唯一 | 版本化通用技能树 |
| `coach_skill_nodes` | B-161 已实现 | `id / taxonomy_id / stable_key / parent_id / name / category / sort_order` | 保存语言、框架、数据、测试、交付、AI 等辅助技能节点 |
| `coach_knowledge_skill_mappings` | B-161 已实现 | `id / run_id / knowledge_point_id / skill_node_id / confidence / source_id / rationale`；知识点、技能和来源同项目 | 保存有来源的知识点—技能映射 |
| `coach_assessment_sessions` | B-162 已实现 | `id / project_id / analysis_run_id / target_type / target_id / status / created_at / completed_at`；目标为 `knowledge_point / skill`，状态为 `active / completed / abandoned` | 持久化固定分析运行的定向评估会话 |
| `coach_assessment_questions` | B-162 已实现 | `id / session_id / knowledge_point_id / prompt / question_type / expected_points_json / source_ids_json / sort_order`；`UNIQUE(session_id, sort_order)` | 保存题目和服务端评分依据；作答前不向客户端返回 `expected_points_json` |
| `coach_assessment_answers` | B-162 已实现 | `id / session_id / question_id / answer / created_at`；`UNIQUE(session_id, question_id)` | 一题只保存一份原始回答，相同回答可幂等重放 |
| `coach_assessment_results` | B-162 已实现 | `id / answer_id / evaluator / score / confidence / status / evaluation_warning / feedback / matched_evidence_json / missing_points_json / source_ids_json / created_at`；`answer_id` 唯一 | 保存 `rule / model` 评分、证据、低置信回退说明和项目内掌握状态 |
| `coach_learning_plans` | B-162 已实现 | `id / project_id / revision / status / based_on_run_id / created_at / confirmed_at`；`revision > 0`、`UNIQUE(project_id, revision)`；`based_on_run_id` 可空且分析运行删除时 `ON DELETE SET NULL` | 保存 `draft / confirmed / archived` 计划；新生成只创建新 revision |
| `coach_learning_plan_items` | B-162 已实现 | `id / plan_id / stable_key / item_type / objective / knowledge_point_id / skill_node_id / source_ids_json / practice_question / completion_criteria / estimated_minutes / status / sort_order` | 保存 `learning / source_gap` 任务与 `todo / in_progress / done / skipped` 进度 |

B-162 表级约束：

- `coach_assessment_sessions` 以部分唯一索引限制同项目、同分析运行、同目标最多一个 `active` 会话；会话按 `(project_id, created_at)` 查询。
- 题目按 `(session_id, sort_order)` 唯一排序；回答按 `(session_id, question_id)` 唯一；结果的 `answer_id` 唯一，`score / confidence` 均限制在 `[0, 1]`。
- 评估会话、题目、回答和结果随上级记录级联删除。`question_type` 当前由领域层生成 `concept / flow / code_location`。
- 计划按 `(project_id, revision)` 索引，并以部分唯一索引保证每项目最多一个 `confirmed` 版本；确认新版本时旧确认版转为 `archived`。
- 计划任务要求 `(plan_id, stable_key)` 和 `(plan_id, sort_order)` 分别唯一，`estimated_minutes > 0`；计划删除时任务级联删除，知识点或技能节点删除时关联字段置空。
- `learning` 任务必须关联同项目、同分析运行的真实来源；`source_gap` 任务的来源必须为空，不能伪造阅读材料。草稿确认后只允许更新任务进度。
- `source_ids_json` 和多态 `target_id` 没有数据库外键；其项目、分析运行、知识点与技能映射归属由 Coach 领域层在写入前校验。

评估状态统一为：

- 无有效结果：`unassessed`
- `score < 0.50`：`needs_work`
- `0.50 <= score < 0.75`：`developing`
- `score >= 0.75`：`mastered`

通用技能状态只聚合当前项目关联知识点，必须保留“未验证”与“评估较弱”的差异，不能推导跨项目或职业能力结论。

## 7. 2.0 Obsidian 插件桥实体与约束（B-163 已实现）

| 表 | 核心字段 / 约束 | 职责 |
|----|-----------------|------|
| `obsidian_pairings` | `id / project_id / code_hash / output_root / expires_at / consumed_at / created_at`；`code_hash` 唯一 | 保存一次性限时配对码哈希与待确认输出根；不持久化明文配对码 |
| `obsidian_connections` | `id / project_id / vault_id / vault_name / output_root / token_hash / status / sync_status / last_synced_at / created_at / revoked_at`；`token_hash` 唯一；部分唯一索引保证每项目最多一个 `active` 连接 | 保存 Vault 连接、同步状态和可撤销令牌哈希 |
| `obsidian_sync_events` | `id / project_id / connection_id / event_id / action / path / old_path / content_hash / payload_json / status / result_json / received_at / processed_at`；`UNIQUE(connection_id, event_id)` | 幂等接收和重放 `upsert / rename / delete` 事件结果 |
| `obsidian_publications` | `id / project_id / connection_id / revision / status / created_at / updated_at / confirmed_at / completed_at`；`revision > 0`、`UNIQUE(project_id, revision)` | 保存一次多 artifact 发布聚合及 `draft / confirmed / queued / applied / conflict / failed` 状态 |
| `obsidian_publication_revisions` | `id / project_id / publication_id / artifact_type / stable_id / target_path / content / content_hash / expected_vault_hash / status / created_at / updated_at`；同一发布内 `stable_id` 与 `target_path` 分别唯一 | 保存不可变 artifact 内容与 Vault hash 基线，支持审计和回滚来源 |
| `obsidian_publication_results` | `id / project_id / publication_id / revision_id / connection_id / status / actual_hash / error_code / message / created_at`；`revision_id` 唯一 | 每个 artifact 修订只接受一个插件终态结果 |

共同约束：

- 所有记录按 `project_id` 或其连接间接隔离；跨项目事件、修订或来源引用必须拒绝。
- 配对码和连接令牌只以密码学哈希持久化；明文只在创建/换取时返回一次，不进入日志、事件负载或发布内容。
- `event_id` 是连接内幂等键；重复事件返回原处理结果，不重复导入或删除。
- `rename` 保留既有文档身份和来源映射；`delete` 清理对应索引并将依赖分析标记为 `stale`。
- `output_root` 和每个 `target_path` 必须规范化并验证仍位于配置根目录内。
- 可更新 Markdown 必须包含 `knowledge_island_managed`、稳定 ID、项目 ID、产物类型和修订号。缺失标记、身份不符或 `expected_vault_hash` 不匹配时写入结果为 `conflict`，禁止自动合并或覆盖。
- 已确认计划和不可变发布修订不得被重新生成原地覆盖；回滚通过发布旧修订的新执行请求完成，不修改历史记录。
- 发布预览以项目级单调 `revision` 创建新聚合；确认只推进现有修订状态，不改写内容、目标路径或 hash。
- `obsidian_publication_results` 只接受 `applied / conflict / failed`。所有 artifact 回报后，发布聚合按结果汇总终态；成功 `actual_hash` 成为同一 `stable_id` 下次预览的 `expected_vault_hash`。
- 六张表只通过 `backend/storage/obsidian_store.py` 读写，并由 `KnowledgeStore` 组合初始化；路由和插件均不能直接访问 SQLite。
