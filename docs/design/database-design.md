# 数据库设计

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-02
> Scope：v2 当前 SQLite Schema、v3 alpha SQLAlchemy/Alembic Schema、数据代际与存储边界
> Related：`architecture-overview.md`、`agent-runtime-and-tool-contract.md`、`api-spec.md`、`permission-matrix.md`、`../adr/ADR-002-sqlite-storage.md`、`../adr/ADR-015-v3-data-api-storage.md`、`../adr/ADR-016-agent-message-stream.md`

## 1. 权威边界

v2.0.0 发布基线由 `KnowledgeStore` 组合四个存储模块，共初始化 **37 张 v2 表**。当前 Unreleased 源码在 `coach_progress_store.py` 增量增加六张逐点学习表，因此 v2 初始化 **43 张当前表**；该增量不能解释为已经进入 v2.0.0 Tag 或安装包。独立 v3 alpha Schema 见 § 7，不属于这 43 张 v2 表。API 和领域代码不得绕过对应 storage 边界直接操作 SQLite。

| 分组 | 模块 | 表数 |
|------|------|------|
| 知识库、问答与兼容评估 | `backend/storage/knowledge_store.py` | 19 |
| Coach 分析与技能映射 | `backend/storage/coach_store.py` | 6 |
| Coach 评估、学习计划与交互学习 | `backend/storage/coach_progress_store.py` | 12 |
| Obsidian Bridge | `backend/storage/obsidian_store.py` | 6 |

默认数据库为 `runtime/v2/app.db`。正式启动要求 `app_metadata.data_generation=v2`，不会自动把旧代际数据库原地升级为 v2。

## 2. v2 当前表与字段

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

### 2.4 Coach 逐知识点交互学习（6）

| 表 | 当前字段 | 核心约束 / 职责 |
|----|----------|-----------------|
| `coach_learning_sessions` | `id`, `project_id`, `analysis_run_id`, `target_type`, `target_id`, `origin_type`, `plan_id`, `plan_item_id`, `status`, `current_step_id`, `version`, `outcome`, `created_at`, `updated_at`, `completed_at`, `abandoned_at` | 目标为 `knowledge_point/skill`；入口为 `coach/learning_map/learning_plan`；七态会话；同项目、同分析运行至多一个非终态会话 |
| `coach_learning_steps` | `id`, `session_id`, `knowledge_point_id`, `title`, `explanation`, `completion_threshold`, `max_attempts`, `status`, `outcome`, `sort_order`, `created_at`, `completed_at` | session 内排序唯一；阈值在 `[0,1]`；最多三次 attempt；知识点删除受限制 |
| `coach_learning_step_sources` | `step_id`, `source_id`, `sort_order` | `(step_id,source_id)` 主键且排序唯一；来源是会话创建时的真实项目来源快照 |
| `coach_learning_exercises` | `id`, `step_id`, `variant`, `question_type`, `prompt`, `expected_points_json`, `reference_answer`, `sort_order`, `revealed_at`, `created_at` | 每步骤 `primary/reinforcement` 各至多一题；题型为 `concept/flow/code_location/sql_query`；评分依据不提前公开 |
| `coach_sql_exercise_fixtures` | `exercise_id`, `schema_json`, `seed_rows_json`, `expected_columns_json`, `expected_rows_json`, `order_sensitive`, `required_semantics_json`, `limits_json`, `fixture_hash`, `created_at` | 与 SQL exercise 一对一；保存结构化 fixture、预期结果、必要语义、资源限制和完整性 hash |
| `coach_learning_attempts` | `id`, `session_id`, `step_id`, `exercise_id`, `attempt_no`, `idempotency_key`, `request_hash`, `answer`, `status`, `evaluator`, `score`, `confidence`, `feedback`, `error_code`, `error_message`, `result_preview_json`, `scoring_details_json`, `counts_for_mastery`, `created_at`, `evaluated_at` | step 内 attempt_no 唯一、会话内幂等键唯一；状态为 `grading/evaluated/failed`；评分与置信度限制在 `[0,1]`；证据资格独立保存 |

会话状态为 `ready / learning / awaiting_answer / evaluated / retrying / completed / abandoned`，结果为 `mastered / needs_work / assisted` 或空值。新表由现有初始化器增量创建，不 ALTER、回填或改写旧 Coach 评估与学习计划记录；旧代码回滚后新表保留为未使用数据，不自动 DROP。

`coach_learning_attempts` 先以 `grading` 保存幂等请求，再在独立评分阶段写回终态。会话 `version` 用作 CAS；写回 attempt、步骤、会话和绑定计划任务在同一事务内完成。SQL fixture 只用于创建每次评分的临时数据库，不能保存或推导正式 `runtime/v2/app.db` 路径。

### 2.5 Obsidian Bridge（6）

| 表 | 当前字段 | 核心约束 / 职责 |
|----|----------|-----------------|
| `obsidian_pairings` | `id`, `project_id`, `code_hash`, `output_root`, `expires_at`, `consumed_at`, `created_at` | `code_hash` 唯一；只保存配对码哈希 |
| `obsidian_connections` | `id`, `project_id`, `vault_id`, `vault_name`, `output_root`, `token_hash`, `status`, `sync_status`, `last_synced_at`, `created_at`, `revoked_at` | `token_hash` 唯一；每项目至多一个 active 连接 |
| `obsidian_sync_events` | `id`, `project_id`, `connection_id`, `event_id`, `action`, `path`, `old_path`, `content_hash`, `payload_json`, `status`, `result_json`, `received_at`, `processed_at` | `UNIQUE(connection_id, event_id)`；操作为 `upsert/rename/delete` |
| `obsidian_publications` | `id`, `project_id`, `connection_id`, `revision`, `status`, `created_at`, `updated_at`, `confirmed_at`, `completed_at` | `UNIQUE(project_id, revision)`；发布聚合状态 |
| `obsidian_publication_revisions` | `id`, `project_id`, `publication_id`, `artifact_type`, `stable_id`, `target_path`, `content`, `content_hash`, `expected_vault_hash`, `status`, `created_at`, `updated_at` | 同一发布内 stable_id 和 target_path 分别唯一；保存不可变内容基线 |
| `obsidian_publication_results` | `id`, `project_id`, `publication_id`, `revision_id`, `connection_id`, `status`, `actual_hash`, `error_code`, `message`, `created_at` | `revision_id` 唯一；终态仅 `applied/conflict/failed` |

## 3. v2 非当前 Schema 与兼容读取

`graph_nodes`、`graph_edges` 不由当前初始化器创建、补列或迁移。只有既有数据库已经包含兼容表时，检索链路才会条件式只读一跳关系；表不存在、字段不兼容或来源无法映射时保持原 BM25/向量结果。

以下历史名称也不是 v2 当前 43 张表的一部分：`chunks`、`workspaces`、`tasks`、`conversations`、`tags`、`document_tags`、`sources`、`skill_areas`、`knowledge_points`、`evidences`、`mastery_records`。其中 `sources` 是 v3 alpha 的独立表名，但不会因此出现在 v2 数据库；文档、测试或旧数据库出现这些名称不能推导 v2 初始化器会创建它们。

## 4. v2 分块、向量与可选存储

- 当前 `backend/domain/chunking.py` 按段落分块；长段使用固定 `700` 字符上限和 `80` 字符重叠。
- `load_settings()` 会读取 `RAG_CHUNK_SIZE` 和 `RAG_CHUNK_OVERLAP`，但当前 Web 入库调用没有把这两个值传入 `split_into_chunks()`；因此不能把环境配置写成已生效行为。
- `document_chunks` 是当前 Web 检索分块表；`chunk_vectors` 保存向量兼容副本，供备份/恢复、健康统计和 Qdrant 回退使用。
- 未配置外部 Embedding 或调用失败时使用本地 `hashing-96`；启用 Qdrant 时向量候选来自 Qdrant local collection，失败时回退 SQLite cosine similarity。
- `sentence-transformers` 不在默认 requirements，Cross-Encoder rerank 默认关闭；缺失时 `rerank_score` 可为空。

## 5. v2 生命周期与一致性

- SQLite 连接启用 `PRAGMA foreign_keys=ON` 和 30 秒 busy timeout。
- 项目删除会级联清理当前项目的大多数子记录；模型 Profile 和技能 taxonomy 是本机全局数据，不随单个项目删除。
- 文档更新会重建其 `document_chunks` 和 `chunk_vectors`；启用 Qdrant 时同步删除旧 point 并写入新 point。Qdrant 同步失败不回滚已经完成的 SQLite 入库。
- 导入批次只保存摘要和明细，不保存上传正文副本，也不提供回滚。
- 聊天和检索复盘保存当时来源/命中快照，避免后续文档更新让历史记录失去上下文。
- 学习计划和发布使用修订、hash 与状态约束阻止静默覆盖；跨项目、多态 ID 和 JSON 内 ID 由领域层校验。
- 学习会话使用 `version`、幂等键和请求 hash 阻止并发或重放覆盖；attempt 历史不可原地替换，答案揭示后的证据资格显式保存。
- 当前知识覆盖动态合并旧 Coach 评估结果和有效学习 attempt，不新增汇总 mastery 表；来源过期只使证据失效，不删除历史记录。
- Obsidian 配对码与服务端连接令牌只保存哈希；插件自己的 Vault 数据文件会保存可恢复令牌，属于独立客户端安全边界。

## 6. v2 路径与备份边界

| 数据 | 默认位置 | 说明 |
|------|----------|------|
| SQLite | `runtime/v2/app.db` | 当前权威业务数据库 |
| Qdrant local | `runtime/v2/vectors/qdrant/` | 启用时的可重建向量索引 |
| 运行日志 | `runtime/v2/logs/` | 由运行配置派生 |
| 配置对象输出目录 | `runtime/v2/outputs/` | `AppSettings.outputs_dir` |
| 结果导出端点默认目录 | `runtime/v2/outputs/` | 默认复用 `AppSettings.outputs_dir`；可由 `KI_OUTPUT_DIR` / `RAG_OUTPUT_DIR` 覆盖，前者优先 |
| 用户应用配置 | 平台应用数据目录下 `KnowledgeIsland/.env` | 兼容全局 LLM 设置可能写入明文 API Key |

备份必须覆盖 SQLite，并在启用 Qdrant 或需要导出文件时明确纳入相应目录。`/api/health` 不验证备份完整性、数据库读写或向量一致性。

## 7. v3 Agent 数据代际（alpha）

### 7.1 物理隔离与迁移

v3 使用 `backend/storage/v3/schema.py` 的 SQLAlchemy 2 Core metadata 和 `backend/storage/v3/migrations/` 的 Alembic 迁移。默认数据库为 `runtime/v3/app.db`，初始 revision 为 `0001_v3_initial`，`app_metadata` 同时写入 `data_generation=v3` 与 `schema_version=0001_v3_initial`。

初始化顺序为：先以只读 SQLite 连接检查既有文件的代际，再创建 SQLAlchemy engine 并升级到 Alembic head。已有非空数据库若没有 `app_metadata`、代际不是 v3、缺少 `alembic_version` 或 revision 不等于当前 head，启动会 fail closed；检查失败前不会创建表、迁移或覆盖原文件。v3 不读取、ALTER、回填或删除 `runtime/v2/app.db`。

连接启用 `foreign_keys=ON`、30 秒 busy timeout、WAL 和 `synchronous=NORMAL`。Store 使用显式事务；需要领取和状态变更的写路径使用 `BEGIN IMMEDIATE`，资源 `version`、请求 hash 和幂等记录用于阻止并发覆盖或同 Key 异载荷重放。

### 7.2 表计数与职责

v3 metadata 当前定义 **19 张业务表 + 2 张运行治理表，共 21 张应用表**；Alembic 另外维护 `alembic_version`。这里的“19 张业务表”口径不包含 `app_metadata` 和 `idempotency_records`。

| 分组 | 表 | 职责 |
|------|----|------|
| 项目、来源与模型（8） | `projects`、`sources`、`documents`、`document_chunks`、`chunk_vectors`、`model_profiles`、`settings`、`integrations` | v3 项目上下文、内容、向量、模型引用和连接配置；当前 alpha API 只使用 `projects` |
| 工作流（3） | `workflow_definitions`、`workflow_versions`、`workflow_bindings` | 工作流身份、不可变版本和项目绑定；HTTP 已开放创建/读取、草稿、发布、绑定和归档，发布工作流尚不能由通用 executor 执行 |
| Agent 执行（8） | `agent_tasks`、`agent_task_messages`、`agent_runs`、`agent_steps`、`agent_step_attempts`、`agent_events`、`agent_approvals`、`agent_artifacts` | 任务对话、运行、步骤尝试、可重放事件、审批快照和产物 |
| 运行治理（2） | `app_metadata`、`idempotency_records` | 数据代际/schema 标记和命令幂等回放 |

关键执行约束：

- Task、Run 和 Step 使用显式状态 CheckConstraint；Run 额外保存 workflow key/version/checksum、深度、重试来源、租约、CAS version 和错误结果。
- `agent_step_attempts` 对 `(step_id, attempt_no)` 唯一；每次领取、成功、失败或取消保留独立尝试记录。
- `agent_events` 对 `(run_id, sequence)` 唯一，为 SSE 恢复提供持久单调游标。
- Approval 冻结 action、target、payload、request hash、resource version 和 CAS version；Artifact 保存内容或 content ref、checksum、metadata、状态和版本。
- `idempotency_records` 对 `(scope, idempotency_key)` 唯一；相同 Key 只有请求 hash 相同才可回放。
- 当前 `project.inspect.v1` 只读取已登记项目根的相对结构元数据，最终把 JSON 检查结果保存到 `agent_artifacts.content`；`runtime/v3/artifacts/` 在本 alpha 中只是预留目录。

### 7.3 alpha.2 消息流复用现有 Schema

alpha.2 的任务首消息、运行输入快照和 Agent 分段回答不新增表、列、索引或 Alembic revision，继续使用 `0001_v3_initial`。API/OpenAPI 版本变化不等于数据库 schema 版本变化。

| 现有表 | alpha.2 复用方式 |
|--------|------------------|
| `agent_tasks` | 与首条用户消息在同一事务创建；表结构不变 |
| `agent_task_messages` | 保存首条用户消息，以及 completed/interrupted 后的完整或明确标记的部分 Agent 消息；`metadata_json` 保存 format、chunk count、content hash 和 complete 标记 |
| `agent_steps` | `trigger.manual.input_json` 只冻结 `input_message_id` 与内容 SHA-256；完整正文保留在不可变 `agent_task_messages`，不向 Step、Run 或 SSE 复制 |
| `agent_events` | 通过既有 `event_type/payload_json` 保存 `assistant.message.*`、补充 Step 事件与 `approval.expired`；继续使用 `(run_id, sequence)` 唯一约束 |
| `idempotency_records` | 复用既有 scope/key/request hash，保证任务首消息、分块追加和终结消息不会重复写入 |

消息完成或中断时，任务消息与 `assistant.message.completed/interrupted` 在同一事务写入。语义 delta 只属于 append-only 事件，不拆成多条长期任务消息。已有 workflow version 1 Run、消息和事件保持原记录可读；固定工作流升级为 version 2 只改变新 Run 的 workflow 快照和 Step 数量，不迁移旧行。

因此本轮不得生成 `0002` 空迁移，也不得通过 ALTER 为 API 响应字段建立数据库列。若未来需要搜索增量片段、独立消息状态或跨 Run 草稿，再单独评估 schema 与迁移。

### 7.4 v3 路径与配置

| 数据 | 默认位置 | 配置 / 当前边界 |
|------|----------|-----------------|
| 数据根 | `runtime/v3/` | `KI_DATA_ROOT` 可覆盖；必须保持与 v2 物理隔离 |
| SQLite | `runtime/v3/app.db` | `KI_V3_DB_PATH` 只覆盖数据库文件；代际检查仍强制执行 |
| 向量目录 | `runtime/v3/vectors/` | 已创建目录，当前项目检查闭环未写向量 |
| 外部产物目录 | `runtime/v3/artifacts/` | 已创建目录，当前产物正文保存在 SQLite |
| 日志目录 | `runtime/v3/logs/` | 预留；当前没有独立 v3 日志轮转器 |
| 备份目录 | `runtime/v3/backups/` | 预留；现有 `ops/scripts/backup_db.sh` 仍只验证 v2 |

现阶段没有 v2 → v3 数据迁移器，也没有经过恢复测试的 v3 自动备份脚本。备份和恢复操作边界见 [`../guides/runbook.md`](../guides/runbook.md)；不能把 v2 脚本成功结果当作 v3 备份证据。
