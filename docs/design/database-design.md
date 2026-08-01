# 数据库设计

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：当前 SQLite Schema、关键约束、数据代际与可选向量边界
> Related：`architecture-overview.md`、`api-spec.md`、`permission-matrix.md`、`../adr/ADR-002-sqlite-storage.md`

## 1. 权威边界

当前正式入口通过 `KnowledgeStore` 组合四个存储模块，共初始化 **37 张当前表**。API 和领域代码不得绕过 `backend/storage/` 直接操作 SQLite。

| 分组 | 模块 | 表数 |
|------|------|------|
| 知识库、问答与兼容评估 | `backend/storage/knowledge_store.py` | 19 |
| Coach 分析与技能映射 | `backend/storage/coach_store.py` | 6 |
| Coach 评估与学习计划 | `backend/storage/coach_progress_store.py` | 6 |
| Obsidian Bridge | `backend/storage/obsidian_store.py` | 6 |

默认数据库为 `runtime/v2/app.db`。正式启动要求 `app_metadata.data_generation=v2`，不会自动把旧代际数据库原地升级为 v2。

## 2. 当前表与字段

以下字段清单按当前 `CREATE TABLE` 与启动时补列逻辑核对。字段名未出现在本节时，不应被当作当前 Schema。

### 2.1 知识库、问答与兼容评估（19）

| 表 | 当前字段 | 核心约束 / 职责 |
|----|----------|-----------------|
| `app_metadata` | `key`, `value` | `key` 主键；保存数据代际 |
| `projects` | `id`, `name`, `root_path`, `created_at`, `retrieval_top_k`, `retrieval_min_score`, `retrieval_use_keyword`, `retrieval_use_vector`, `default_prompt_preset_id` | 项目与项目级检索/Prompt 默认值 |
| `prompt_presets` | `id`, `project_id`, `name`, `description`, `system_prompt`, `answer_format`, `created_at`, `updated_at` | 随项目级联删除 |
| `model_profiles` | `id`, `name`, `provider`, `api_base`, `model`, `temperature`, `max_tokens`, `api_key_ref`, `is_default`, `created_at`, `updated_at` | 本机全局 Profile；SQLite 只保存 Key 引用 |
| `documents` | `id`, `project_id`, `source_path`, `relative_path`, `content`, `checksum`, `updated_at` | `UNIQUE(project_id, relative_path)`；随项目级联删除 |
| `document_collections` | `id`, `project_id`, `name`, `description`, `color`, `created_at`, `updated_at` | `UNIQUE(project_id, name)` |
| `document_collection_items` | `id`, `project_id`, `collection_id`, `document_id`, `created_at` | `UNIQUE(collection_id, document_id)`；集合/文档删除时级联 |
| `import_batches` | `id`, `project_id`, `source_type`, `status`, `started_at`, `finished_at`, `summary_json`, `message`, `created_at` | 只保存批次摘要，不是备份 |
| `import_batch_items` | `id`, `batch_id`, `project_id`, `kind`, `relative_path`, `document_id`, `reason`, `created_at` | `document_id` 是历史引用字符串，不设文档外键 |
| `document_chunks` | `id`, `document_id`, `project_id`, `chunk_index`, `content`, `token_count`, `created_at` | `UNIQUE(document_id, chunk_index)`；文档删除时级联 |
| `chunk_vectors` | `chunk_id`, `project_id`, `vector_json`, `provider`, `model`, `updated_at` | `chunk_id` 主键且外键到 chunk；SQLite 向量兼容副本 |
| `chat_sessions` | `id`, `project_id`, `title`, `created_at`, `updated_at` | 随项目级联删除 |
| `chat_messages` | `id`, `project_id`, `session_id`, `parent_message_id`, `branch_index`, `question`, `answer`, `mode`, `provider`, `warning`, `sources_json`, `created_at` | 保存来源快照和分支关系；当前不对 session/parent 声明外键 |
| `answer_feedback` | `id`, `project_id`, `message_id`, `rating`, `note`, `created_at` | 随消息或项目级联删除 |
| `assessment_questions` | `id`, `project_id`, `source_path`, `question_type`, `knowledge_point`, `prompt`, `expected_points_json`, `reference_snippet`, `created_at` | 兼容评估题库 |
| `assessment_answers` | `id`, `project_id`, `question_id`, `answer`, `created_at` | 随题目或项目级联删除 |
| `assessment_results` | `id`, `project_id`, `question_id`, `answer_id`, `status`, `score`, `matched_points_json`, `missing_points_json`, `feedback`, `source_path`, `created_at` | 兼容评估结果 |
| `agent_tool_runs` | `id`, `project_id`, `tool_name`, `arguments_json`, `result_json`, `status`, `error`, `created_at` | 只读 Agent 工具运行审计 |
| `retrieval_reviews` | `id`, `project_id`, `query`, `parameters_json`, `hits_json`, `quality_json`, `note`, `created_at` | 保存检索复盘快照 |

特别说明：`documents` **只有** `id / project_id / source_path / relative_path / content / checksum / updated_at`，没有其他当前字段。

### 2.2 Coach 分析与技能映射（6）

| 表 | 当前字段 | 核心约束 / 职责 |
|----|----------|-----------------|
| `coach_analysis_runs` | `id`, `project_id`, `analyzer_version`, `source_fingerprint`, `status`, `summary_json`, `started_at`, `finished_at` | 保存分析运行；随项目级联删除 |
| `coach_knowledge_points` | `id`, `project_id`, `stable_key`, `title`, `category`, `summary`, `current_run_id`, `created_at`, `updated_at` | `UNIQUE(project_id, stable_key)`；运行删除时当前引用置空 |
| `coach_knowledge_sources` | `id`, `run_id`, `knowledge_point_id`, `document_id`, `source_path`, `chunk_id`, `source_hash`, `excerpt`, `locator_json` | 保存来源快照；文档/chunk 删除时对应引用置空 |
| `coach_skill_taxonomies` | `id`, `version`, `name`, `status`, `created_at` | `version` 唯一 |
| `coach_skill_nodes` | `id`, `taxonomy_id`, `stable_key`, `parent_id`, `name`, `category`, `sort_order` | `UNIQUE(taxonomy_id, stable_key)`；父节点删除时置空 |
| `coach_knowledge_skill_mappings` | `id`, `run_id`, `knowledge_point_id`, `skill_node_id`, `confidence`, `source_id`, `rationale` | `UNIQUE(run_id, knowledge_point_id, skill_node_id)`；映射必须引用来源 |

### 2.3 Coach 评估与学习计划（6）

| 表 | 当前字段 | 核心约束 / 职责 |
|----|----------|-----------------|
| `coach_assessment_sessions` | `id`, `project_id`, `analysis_run_id`, `target_type`, `target_id`, `status`, `created_at`, `completed_at` | 目标为 `knowledge_point/skill`；状态为 `active/completed/abandoned`；同目标至多一个 active 会话 |
| `coach_assessment_questions` | `id`, `session_id`, `knowledge_point_id`, `prompt`, `question_type`, `expected_points_json`, `source_ids_json`, `sort_order` | `UNIQUE(session_id, sort_order)` |
| `coach_assessment_answers` | `id`, `session_id`, `question_id`, `answer`, `created_at` | `UNIQUE(session_id, question_id)` |
| `coach_assessment_results` | `id`, `answer_id`, `evaluator`, `score`, `confidence`, `status`, `evaluation_warning`, `feedback`, `matched_evidence_json`, `missing_points_json`, `source_ids_json`, `created_at` | `answer_id` 唯一；分数/置信度限制在 `[0,1]` |
| `coach_learning_plans` | `id`, `project_id`, `revision`, `status`, `based_on_run_id`, `created_at`, `confirmed_at` | `UNIQUE(project_id, revision)`；每项目至多一个 confirmed 版本 |
| `coach_learning_plan_items` | `id`, `plan_id`, `stable_key`, `item_type`, `objective`, `knowledge_point_id`, `skill_node_id`, `source_ids_json`, `practice_question`, `completion_criteria`, `estimated_minutes`, `status`, `sort_order` | plan 内 stable_key 与 sort_order 分别唯一；时长必须大于 0 |

评估结果状态为 `unassessed / needs_work / developing / mastered`。计划状态为 `draft / confirmed / archived`；任务类型为 `learning / source_gap`，任务状态为 `todo / in_progress / done / skipped`。`source_ids_json` 和多态 `target_id` 的项目归属由领域层校验，不由数据库外键表达。

### 2.4 Obsidian Bridge（6）

| 表 | 当前字段 | 核心约束 / 职责 |
|----|----------|-----------------|
| `obsidian_pairings` | `id`, `project_id`, `code_hash`, `output_root`, `expires_at`, `consumed_at`, `created_at` | `code_hash` 唯一；只保存配对码哈希 |
| `obsidian_connections` | `id`, `project_id`, `vault_id`, `vault_name`, `output_root`, `token_hash`, `status`, `sync_status`, `last_synced_at`, `created_at`, `revoked_at` | `token_hash` 唯一；每项目至多一个 active 连接 |
| `obsidian_sync_events` | `id`, `project_id`, `connection_id`, `event_id`, `action`, `path`, `old_path`, `content_hash`, `payload_json`, `status`, `result_json`, `received_at`, `processed_at` | `UNIQUE(connection_id, event_id)`；操作为 `upsert/rename/delete` |
| `obsidian_publications` | `id`, `project_id`, `connection_id`, `revision`, `status`, `created_at`, `updated_at`, `confirmed_at`, `completed_at` | `UNIQUE(project_id, revision)`；发布聚合状态 |
| `obsidian_publication_revisions` | `id`, `project_id`, `publication_id`, `artifact_type`, `stable_id`, `target_path`, `content`, `content_hash`, `expected_vault_hash`, `status`, `created_at`, `updated_at` | 同一发布内 stable_id 和 target_path 分别唯一；保存不可变内容基线 |
| `obsidian_publication_results` | `id`, `project_id`, `publication_id`, `revision_id`, `connection_id`, `status`, `actual_hash`, `error_code`, `message`, `created_at` | `revision_id` 唯一；终态仅 `applied/conflict/failed` |

## 3. 非当前 Schema 与兼容读取

`graph_nodes`、`graph_edges` 不由当前初始化器创建、补列或迁移。只有既有数据库已经包含兼容表时，检索链路才会条件式只读一跳关系；表不存在、字段不兼容或来源无法映射时保持原 BM25/向量结果。

以下历史名称也不是当前 37 张表的一部分：`chunks`、`workspaces`、`tasks`、`conversations`、`tags`、`document_tags`、`sources`、`skill_areas`、`knowledge_points`、`evidences`、`mastery_records`。文档、测试或旧数据库出现这些名称不能推导当前应用会创建它们。

## 4. 分块、向量与可选存储

- 当前 `backend/domain/chunking.py` 按段落分块；长段使用固定 `700` 字符上限和 `80` 字符重叠。
- `load_settings()` 会读取 `RAG_CHUNK_SIZE` 和 `RAG_CHUNK_OVERLAP`，但当前 Web 入库调用没有把这两个值传入 `split_into_chunks()`；因此不能把环境配置写成已生效行为。
- `document_chunks` 是当前 Web 检索分块表；`chunk_vectors` 保存向量兼容副本，供备份/恢复、健康统计和 Qdrant 回退使用。
- 未配置外部 Embedding 或调用失败时使用本地 `hashing-96`；启用 Qdrant 时向量候选来自 Qdrant local collection，失败时回退 SQLite cosine similarity。
- `sentence-transformers` 不在默认 requirements，Cross-Encoder rerank 默认关闭；缺失时 `rerank_score` 可为空。

## 5. 生命周期与一致性

- SQLite 连接启用 `PRAGMA foreign_keys=ON` 和 30 秒 busy timeout。
- 项目删除会级联清理当前项目的大多数子记录；模型 Profile 和技能 taxonomy 是本机全局数据，不随单个项目删除。
- 文档更新会重建其 `document_chunks` 和 `chunk_vectors`；启用 Qdrant 时同步删除旧 point 并写入新 point。Qdrant 同步失败不回滚已经完成的 SQLite 入库。
- 导入批次只保存摘要和明细，不保存上传正文副本，也不提供回滚。
- 聊天和检索复盘保存当时来源/命中快照，避免后续文档更新让历史记录失去上下文。
- 学习计划和发布使用修订、hash 与状态约束阻止静默覆盖；跨项目、多态 ID 和 JSON 内 ID 由领域层校验。
- Obsidian 配对码与服务端连接令牌只保存哈希；插件自己的 Vault 数据文件会保存可恢复令牌，属于独立客户端安全边界。

## 6. 路径与备份边界

| 数据 | 默认位置 | 说明 |
|------|----------|------|
| SQLite | `runtime/v2/app.db` | 当前权威业务数据库 |
| Qdrant local | `runtime/v2/vectors/qdrant/` | 启用时的可重建向量索引 |
| 运行日志 | `runtime/v2/logs/` | 由运行配置派生 |
| 配置对象输出目录 | `runtime/v2/outputs/` | `AppSettings.outputs_dir` |
| 结果导出端点默认目录 | `runtime/v2/outputs/` | 默认复用 `AppSettings.outputs_dir`；可由 `KI_OUTPUT_DIR` / `RAG_OUTPUT_DIR` 覆盖，前者优先 |
| 用户应用配置 | 平台应用数据目录下 `KnowledgeIsland/.env` | 兼容全局 LLM 设置可能写入明文 API Key |

备份必须覆盖 SQLite，并在启用 Qdrant 或需要导出文件时明确纳入相应目录。`/api/health` 不验证备份完整性、数据库读写或向量一致性。
