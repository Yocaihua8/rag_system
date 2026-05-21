# 开发日志

记录每次代码变更的内容、原因和影响，与 Git commit 对应。

---

## devlog 日志文件索引

- [2026-04-15](devlog/2026-04-15.md)
- [2026-04-16](devlog/2026-04-16.md)
- [2026-04-17](devlog/2026-04-17.md)
- [2026-04-18](devlog/2026-04-18.md)
- [2026-05-02](devlog/2026-05-02.md)
- [2026-05-11](devlog/2026-05-11.md)
- [2026-05-16](devlog/2026-05-16.md)
- [2026-05-18](devlog/2026-05-18.md)
- [2026-05-20](devlog/2026-05-20.md)

## 2026-05-21 | B-72 — Web 回答工具建议第一片

### 目标

在不让模型自动执行工具的前提下，让 `/api/answer` 在来源不足时返回结构化工具建议，提示用户手动运行只读 `search_sources` 扩大来源检索。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 更新 | `webapp/answers.py`、`webapp/models.py`、`webapp/api.py` | `AnswerResult` 增加可选 `tool_suggestion`，无有效来源时返回 `search_sources` 建议 |
| 更新 | `webapp/static/js/ui.js` | 回答区展示建议工具、原因和查询词，不调用工具接口 |
| 更新 | `tests/test_webapp/test_api.py`、`tests/test_webapp/test_frontend_static.py`、`tests/test_webapp/test_docs_contract.py` | 覆盖 API 字段、前端展示和文档契约，并确认不自动写入工具审计 |
| 更新 | `README.md`、`docs/design/api-spec.md`、`docs/guides/setup.md`、`docs/guides/testing.md`、`CHANGELOG.md`、`docs/BACKLOG.md` | 同步工具建议边界 |

### 关键行为

- 来源不足时返回 `tool_suggestion.tool=search_sources` 和原问题查询词。
- 建议只用于 UI 提示，不自动执行 `/api/agent/tools/run`，也不写入 `agent_tool_runs`。
- 有可用来源时不返回 `tool_suggestion`，避免干扰正常回答。

## 2026-05-21 | B-71 — Web Agent 只读来源检索工具

### 目标

在现有 Agent 只读工具白名单中补充 `search_sources`，让工具能力可以复用 Web RAG 检索返回来源片段，同时继续保持只读和审计。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 更新 | `webapp/agent_tools.py` | 新增 `search_sources` 只读工具，参数为 `query`，最多返回 5 条命中 |
| 更新 | `webapp/static/index.html`、`webapp/static/js/app.js`、`webapp/static/js/ui.js` | 工作台 Agent 工具区新增来源检索输入、按钮和结果展示 |
| 更新 | `tests/test_webapp/test_agent_tools.py`、`tests/test_webapp/test_frontend_static.py`、`tests/test_webapp/test_docs_contract.py` | 覆盖工具列表、来源检索、缺少 query、前端接线和文档契约 |
| 更新 | `README.md`、`docs/design/api-spec.md`、`docs/guides/setup.md`、`docs/guides/testing.md`、`CHANGELOG.md`、`docs/BACKLOG.md` | 同步 `search_sources` 边界 |

### 关键行为

- `search_sources` 使用现有 `search_documents()`，不新增检索逻辑或外部依赖。
- 工具只读返回 `query / hit_count / hits`，命中项沿用搜索响应字段。
- 成功与失败都会写入 `agent_tool_runs`，空 query 会被拒绝。

## 2026-05-21 | B-70 — Web Agent 只读工具第一片

### 目标

在不开放高风险权限的前提下，为 Web MVP 增加 Agent / 工具能力的第一片：只读工具白名单、项目概览工具和工具调用审计。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 新增 | `webapp/agent_tools.py` | 定义只读工具白名单和 `project_overview` 运行逻辑 |
| 更新 | `webapp/api.py`、`webapp/storage.py`、`webapp/models.py` | 新增 `/api/agent/tools`、`/api/agent/tools/run`、`agent_tool_runs` 审计表和模型 |
| 新增/更新 | `webapp/static/js/agent.js`、`webapp/static/index.html`、`webapp/static/js/app.js`、`webapp/static/js/ui.js` | 工作台新增只读项目概览入口和结果展示 |
| 新增/更新 | `tests/test_webapp/` | 覆盖工具列表、项目概览、未知工具拒绝、审计记录和前端接线 |
| 更新 | `README.md`、`docs/design/api-spec.md`、`docs/design/database-design.md`、`docs/guides/testing.md`、`CHANGELOG.md`、`docs/BACKLOG.md` | 同步只读工具边界 |

### 关键行为

- 当前只开放 `project_overview`，返回文档数、分块数、向量数和聊天记录数。
- 每次工具运行写入 `agent_tool_runs`；未知工具在项目存在时记录失败审计。
- 不开放 shell、任意命令执行、任意文件写入或外部自动化。

## 2026-05-21 | B-69 — Web 多轮上下文第一片

### 目标

让真实 LLM 问答使用当前项目最近对话，解决“历史只展示、不参与回答”的问题；范围限定为最近 3 轮 `question/answer` prompt 注入，不扩展为完整 Agent 记忆。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 更新 | `webapp/api.py` | `/api/answer` 调用回答生成前读取当前项目最近 3 条聊天记录 |
| 更新 | `webapp/answers.py`、`webapp/llm.py` | LLM client 支持 `history_messages`，prompt 增加“最近对话”段 |
| 更新 | `tests/test_webapp/test_api.py`、`tests/test_webapp/test_llm.py`、`tests/test_webapp/test_docs_contract.py` | 覆盖历史传参、LLM payload 和文档边界 |
| 更新 | `README.md`、`docs/design/api-spec.md`、`docs/guides/setup.md`、`docs/guides/testing.md`、`CHANGELOG.md`、`docs/BACKLOG.md` | 同步多轮上下文边界 |

### 关键行为

- 真实 LLM 请求最多带入同项目最近 3 轮问答。
- 本地 fallback 仍只基于当前检索片段组合回答，不伪造多轮推理。
- prompt 中历史对话不能替代来源片段约束；资料不足仍要求说明缺口。

## 2026-05-21 | B-68 — Web 项目聊天记录第一片

### 目标

让 Web 工作台从单次回答升级为按项目持久化的最小聊天体验：提问后保存问题、回答、模式、provider 和来源快照，刷新页面或切换项目后可恢复最近对话。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 更新 | `webapp/models.py`、`webapp/storage.py` | 新增 `ChatMessage` 和 `chat_messages` SQLite 表，支持写入与按项目读取 |
| 更新 | `webapp/api.py` | `/api/answer` 写入聊天记录；新增 `GET /api/chat/messages` |
| 更新 | `webapp/static/index.html`、`webapp/static/js/*.js`、`webapp/static/styles.css` | 工作台新增最近对话列表，前端加载并追加当前项目聊天记录 |
| 新增/更新 | `tests/test_webapp/` | 覆盖聊天记录 API、前端接线和文档契约 |
| 更新 | `README.md`、`docs/design/api-spec.md`、`docs/design/database-design.md`、`docs/guides/testing.md`、`CHANGELOG.md`、`docs/BACKLOG.md` | 同步聊天记录能力边界 |

### 关键行为

- 每次 `/api/answer` 成功返回时，保存一条当前项目聊天消息。
- 历史消息保存当次来源快照，不依赖后续文档是否被更新。
- 这是单项目消息历史，不是完整多轮上下文注入；后续仍需把历史摘要传给 LLM。

## 2026-05-21 | B-66 — Web 真实 embedding provider 接入

### 目标

在 Web MVP 中接入 OpenAI-compatible `/embeddings`，让 chunk 向量可来自真实 embedding provider；未配置或请求失败时继续回退本地 hashing，保证导入不中断。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 新增 | `webapp/embeddings.py` | 新增 EmbeddingConfig、OpenAI-compatible embeddings 客户端、本地 hashing fallback |
| 更新 | `webapp/storage.py` | `KnowledgeStore` 支持注入 embedding client；`chunk_vectors` 记录 `provider/model` |
| 更新 | `webapp/search.py`、`webapp/models.py` | 搜索查询向量可走 embedding client；响应返回 `vector_provider/vector_model` |
| 更新 | `src/config/settings.py`、`src/config/defaults.py`、`.env.example` | 新增 `RAG_EMBED_API_BASE`、`RAG_EMBED_API_KEY`、`RAG_EMBED_API_MODEL` |
| 更新 | `compose.yaml`、`scripts/docker_up.ps1`、`README-Docker-Quickstart.txt` | Docker 模式透传 embedding provider 环境变量和 Key |
| 新增/更新 | `tests/test_webapp/` | 覆盖 embeddings 请求体、fake API embedding 写入、搜索 provider/model 字段 |
| 更新 | `README.md`、`docs/design/api-spec.md`、`docs/design/database-design.md`、`docs/guides/testing.md`、`CHANGELOG.md`、`docs/BACKLOG.md` | 同步配置和能力边界 |

### 关键行为

- `RAG_EMBED_PROVIDER=api` 且存在 `RAG_EMBED_API_KEY` 时请求 `{api_base}/embeddings`。
- API embedding 请求失败时自动回退本地 hashing 向量，不阻断导入。
- DeepSeek 聊天 Key 不自动复用为 embedding Key；如果当前 DeepSeek 端点不支持 `/embeddings`，需要单独配置支持 embeddings 的服务。

## 2026-05-21 | B-65 — Web 本地向量检索接入

### 目标

在不新增运行时依赖的前提下，把 Web MVP 从纯关键词 chunk 召回推进到 keyword + vector 混合召回，为后续真实 embedding provider 留出替换点。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 新增 | `webapp/vector_index.py` | 使用标准库 hashing 生成本地轻量文本向量，并提供 cosine 相似度 |
| 更新 | `webapp/storage.py` | 新增 `chunk_vectors` 表；文档 chunk 写入时同步持久化向量 |
| 更新 | `webapp/search.py`、`webapp/models.py` | 搜索结果合成 keyword/vector 分数，并返回 `retrieval`、`keyword_score`、`vector_score` |
| 更新 | `tests/test_webapp/test_search.py` | 覆盖向量持久化和 hybrid 分数字段 |
| 更新 | `README.md`、`docs/design/api-spec.md`、`docs/design/database-design.md`、`docs/guides/testing.md`、`CHANGELOG.md`、`docs/BACKLOG.md` | 同步混合召回边界 |

### 关键行为

- 本地向量使用标准库生成，不依赖外部 embedding 服务。
- 搜索结果仍保留 `score` 字段；`score = keyword_score + vector_score`。
- 当前不是语义 embedding，后续 B-66 继续接入真实 embedding API / vector store / reranker。

## 2026-05-21 | B-64 — Web RAG 分块检索第一片

### 目标

把 Web MVP 检索从整篇文档关键词计数推进到 chunk 级 RAG 召回：导入时生成可追踪分块，搜索和问答使用命中的分块片段作为来源。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 新增 | `webapp/chunking.py` | 按段落和长度拆分文档内容，并统计轻量 token 数 |
| 更新 | `webapp/storage.py`、`webapp/models.py` | 新增 `document_chunks` 表和 `DocumentChunk` 模型；文档写入时重建分块 |
| 更新 | `webapp/search.py` | 搜索改为遍历 chunk，命中结果返回 `chunk_id` / `chunk_index` |
| 更新 | `tests/test_webapp/test_search.py` | 覆盖分块生成、更新清理和 chunk 级搜索结果 |
| 更新 | `README.md`、`docs/design/api-spec.md`、`docs/design/database-design.md`、`docs/guides/testing.md`、`CHANGELOG.md`、`docs/BACKLOG.md` | 同步检索与存储行为 |

### 关键行为

- 新导入或更新文档会生成 `document_chunks`；删除文档记录时通过外键级联清理分块。
- 搜索结果仍兼容旧字段 `path/document_id/snippet/score`，额外返回 `chunk_id/chunk_index`。
- 这是 chunk 级关键词召回，不等同于向量检索或 reranker；后续 B-65 继续补 embedding / vector store。

## 2026-05-21 | B-63 — Web 文档处理管线第一片

### 目标

把 Web MVP 的导入从“只读文本文件”推进到最小真实文档处理管线：目录导入和浏览器文件夹导入共用后端处理模块，支持 DOCX 正文抽取，并让 PDF 在无可选解析器时返回明确跳过原因。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 新增 | `webapp/document_processing.py` | 统一处理文本、DOCX、PDF 候选文件，DOCX 使用标准库解包 `word/document.xml` 抽取正文 |
| 更新 | `webapp/ingestion.py`、`webapp/upload_import.py`、`webapp/import_rules.py` | 目录导入和上传导入共用文档处理管线；支持 `.docx/.pdf` 进入后端判断 |
| 更新 | `webapp/static/js/projects.js` | 浏览器文件夹导入对 DOCX/PDF 使用 `arrayBuffer` + base64 payload |
| 新增/更新 | `tests/test_webapp/` | 覆盖目录 DOCX 抽取、上传 DOCX base64、PDF 跳过原因和前端二进制上传约束 |
| 更新 | `README.md`、`README-Docker-Quickstart.txt`、`docs/design/api-spec.md`、`docs/guides/*`、`docs/release/*`、`CHANGELOG.md`、`docs/BACKLOG.md` | 同步导入格式、接口字段和验收边界 |

### 关键行为

- 文本文件仍沿用 `Path.read_text()`，保持既有换行规范化和读取错误行为。
- DOCX 不新增运行时依赖，使用 Python 标准库 `zipfile` 和 `xml.etree.ElementTree` 抽取正文段落。
- PDF 当前只识别并返回 `pdf extraction requires optional parser`，避免假装已解析。

## 2026-05-21 | B-61 — Web 掌握评估图表概览

### 目标

在 Web MVP 掌握评估页加入 A+B 可视化：保留雷达图的能力画像感，同时用得分环和命中/缺失要点保证信息来源真实；不引入新依赖，不修改评估 API、存储结构或后端评分逻辑。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 更新 | `webapp/static/index.html` | 在评估视图新增 `assessment-overview` 图表区域 |
| 更新 | `webapp/static/js/ui.js` | 新增 `renderAssessmentOverview()`，用当前评估结果派生雷达图和得分环 |
| 更新 | `webapp/static/js/app.js` | 在开始评估、提交回答和刷新文档时同步刷新图表概览 |
| 更新 | `webapp/static/styles.css` | 新增雷达图、得分环、命中/待补充标签和响应式布局样式 |
| 更新 | `tests/test_webapp/test_frontend_static.py` | 新增评估图表入口与渲染函数静态约束 |
| 更新 | `docs/design/ui-wireframes.md`、`CHANGELOG.md`、`docs/BACKLOG.md` | 同步 B-61 前端行为 |

### 关键行为

- 图表只消费现有 `score`、`matched_points`、`missing_points` 和 `source_path`，不新增接口字段。
- 雷达图的五个维度是当前单题结果的派生视图，不代表长期能力画像数据。
- 未提交回答时显示空状态；提交回答后展示百分比分数、命中要点、待补充要点和建议阅读来源。

### 测试结果

```text
.venv\Scripts\python.exe -m pytest tests\test_webapp -q
50 passed

.venv\Scripts\python.exe -m compileall -q app.py webapp
通过，无输出错误

Get-ChildItem webapp\static\js\*.js | ForEach-Object { node --check $_.FullName }
通过，无输出错误

.venv\Scripts\python.exe scripts\check_docs_consistency.py
[PASS] docs consistency checks passed.
```

## 2026-05-21 | B-62 — Web 模型设置页

### 目标

参考 Cherry Studio 的 provider 配置体验，在 Web 设置页补齐模型配置入口，让用户不用只依赖环境变量即可配置 DeepSeek / OpenAI-compatible API。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 新增 | `webapp/settings_api.py` | 读取、保存和测试 LLM 设置；响应不回显 API Key 明文 |
| 更新 | `webapp/api.py` | 新增 `GET/POST /api/settings/llm` 与 `POST /api/settings/llm/test` |
| 新增 | `webapp/static/js/settings.js` | 设置页 API 调用封装 |
| 更新 | `webapp/static/index.html`、`webapp/static/js/app.js` | 在设置视图接入模型设置表单和连接测试 |
| 更新 | `tests/test_webapp/` | 覆盖设置读取、保存、未配置测试错误和前端入口 |
| 更新 | `README.md`、`docs/design/api-spec.md`、`docs/guides/*`、`CHANGELOG.md`、`docs/BACKLOG.md` | 同步接口契约和使用方式 |

### 关键行为

- 设置页可保存 `provider`、`api_base`、`model` 和非空 `api_key`。
- API Key 只保存到配置层 appdata `.env`，接口和前端状态不回显明文。
- 连接测试复用现有 OpenAI-compatible Chat Completions 客户端；未配置 Key 时返回可读错误。

## 2026-05-21 | B-60 — Web 首页工作台分视图重设计

### 目标

根据已确认的 Figma `Workbench Simplified V2` 方向，把 Web MVP 首页从旧双栏暗色页面调整为简洁工作台；左侧只保留主导航，工作台、资料库、掌握评估和设置改为独立视图切换，降低默认信息密度并保留现有 API 调用与前端业务逻辑。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 更新 | `webapp/static/index.html` | 拆分为工作台、资料库、评估、设置四个独立视图 |
| 更新 | `webapp/static/styles.css` | 改为浅灰底、白色面板、青绿色主色，并补充分视图显示规则 |
| 更新 | `webapp/static/js/app.js` | 新增左侧导航视图切换逻辑，替代页面内锚点跳转 |
| 更新 | `tests/test_webapp/test_frontend_static.py` | 新增工作台结构、独立视图导航与主题 token 静态约束 |
| 更新 | `docs/design/ui-wireframes.md` | 同步 Web MVP 分视图工作台结构与信息密度原则 |
| 更新 | `CHANGELOG.md`、`docs/BACKLOG.md` | 记录 B-60 已完成 |

### 关键行为

- 保留 `project-select`、`folder-import-button`、`documents`、`question`、`answer`、`sources`、`assessment-*` 等现有 DOM ID，避免改动既有 API 调用和数据渲染逻辑。
- 左侧导航按钮使用 `data-view-target` 切换 `workspace-view`，不再通过 `href="#..."` 跳到页面内卡片。
- 工作台只展示问答主流程；项目选择、导入、文件列表、文件预览和导入状态集中在资料库视图。
- 点击来源或文件预览时会切换到资料库视图，继续复用 `document-preview` 展示当前文件片段。

### 测试结果

```text
.venv\Scripts\python.exe -m pytest tests\test_webapp -q
49 passed

.venv\Scripts\python.exe -m compileall -q app.py webapp
通过，无输出错误

Get-ChildItem webapp\static\js\*.js | ForEach-Object { node --check $_.FullName }
通过，无输出错误

.venv\Scripts\python.exe scripts\check_docs_consistency.py
[PASS] docs consistency checks passed.
```

## 2026-05-20 | B-54 — 默认入口切换为本地 Web MVP

### 目标

将默认启动方式从 PySide6 桌面端切换为本地 Web MVP，优先保证项目能快速投入试用；旧桌面端代码暂时保留为 legacy，避免覆盖当前未提交改动。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 新增 | `webapp/` | 标准库 HTTP 服务、SQLite 存储、目录导入、关键词检索、回答组合和原生前端 |
| 更新 | `app.py` | 默认启动 `webapp.server.run_server()` |
| 新增 | `tests/test_webapp/` | 覆盖导入、检索排序、API 问答流程 |
| 新增 | `AGENT.md` | 记录 Web 栈边界、文件拆分和验证规则 |
| 更新 | `README.md`、`docs/guides/setup.md`、`docs/guides/testing.md` | 同步默认启动与验证方式 |

### 关键行为

- 导入 API 返回当前项目空间文档列表，前端侧栏展示已导入文件。
- 切换项目空间时，前端会刷新对应项目的文件列表。
- 项目工具栏下方显示当前项目空间绑定的本地目录，切换、创建、改名和删除后同步刷新。
- 项目列表返回 `root_exists`，绑定目录被移动或删除时前端提示“目录不存在”并阻止导入；导入 API 同时返回明确 400 错误。
- 重新导入会统计新增、更新、未变更、删除和跳过数量；源目录中已删除的文本文件会从当前项目空间文档列表中移除。
- 新增单文件预览 API，前端点击已导入文件后可查看正文内容。
- 新增独立检索入口，不生成回答也可以直接搜索文件片段，并点击结果打开文件预览。
- 新增单文档移除 API 和前端“移除”按钮，只删除当前项目空间内的文档记录，不删除磁盘源文件。
- 已导入文件列表新增路径过滤输入框，前端基于当前文档列表本地过滤，不改变搜索 API。
- 已导入文件列表新增当前显示数量和总文件数提示，便于确认过滤范围。
- 导入扫描默认跳过 `.git`、`.venv`、`node_modules`、`.claude`、`.codex`、`.agents`、`.vscode`、`.idea`、`__pycache__` 和常见构建/缓存目录，避免真实项目导入时扫进依赖、版本库和本机工具配置。
- 导入扫描默认跳过超过 1MB 的单个文本文件，并计入本轮跳过数量。
- 导入规则集中到 `webapp/import_rules.py`，后续调整后缀、排除目录和大小上限不需要修改扫描流程。
- 导入结果新增 `skipped_details`，前端展示被跳过文件的路径和原因。
- 前端新增导入错误列表，单独展示 `result.errors`，避免读取失败和普通跳过文件混在一起。
- 新增项目空间删除 API 和前端删除按钮，删除项目空间时同步清理其文档记录。
- 项目空间删除按钮增加浏览器二次确认，取消时不会调用删除 API。
- 新增项目空间改名 API 和前端改名按钮，改名只更新项目名称，不修改绑定目录和文档记录。
- 前端为空文件列表、空检索结果、空来源、空跳过详情和空文件预览增加明确提示。
- 前端使用浏览器本地存储记录最近选中的项目空间，刷新页面后优先恢复该项目；项目删除后会清除该记录。

### 测试结果

```text
.venv\Scripts\python.exe -m pytest tests\test_webapp -q
10 passed
```

## 2026-05-20 | 本地 Web MVP 收口文档与接口契约同步

### 目标

补齐默认 Web MVP 切换后的接口契约与发布验收说明，避免 `docs/design/api-spec.md` 仍停留在“无 HTTP/API 服务”的旧状态。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 更新 | `docs/design/api-spec.md` | 增加本地 Web MVP `/api/*` HTTP 接口、字段和错误契约 |
| 新增 | `docs/release/WEB_MVP_READINESS_2026-05-20.md` | 增加可交付范围、非承诺范围、验收命令和浏览器验收清单 |
| 更新 | `README.md` | 将 API 契约与 Web MVP 收口文档加入阅读入口 |
| 新增 | `tests/test_webapp/test_docs_contract.py` | 防止 Web MVP API 文档再次退回旧的“无 HTTP/API 服务”描述 |

### 关键行为

- Web MVP HTTP API 明确限定为本机服务，不承诺远程多用户部署。
- API 契约覆盖项目空间、文档导入、文档预览、检索和问答。
- 发布收口文档明确当前不包含安装包、目录选择器、语义向量检索和完整 LLM 推理质量承诺。
- 真实仓库导入验收后，导入规则补充忽略 `.claude`、`.codex`、`.agents`、`.vscode`、`.idea` 等本机工具配置目录。

## 2026-05-20 | B-55 — Web 端 DeepSeek、掌握评估与首次引导

### 目标

把 C 端 Web MVP 从“本地片段问答”推进到可试用版本：配置 DeepSeek 后使用真实 LLM 回答，同时补齐 Web 掌握评估入口和首次使用引导。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 新增 | `webapp/llm.py` | 使用 Python 标准库 `urllib` 调用 OpenAI-compatible Chat Completions |
| 新增 | `webapp/assessment.py` | 从已导入文档生成最小评估题，并按来源关键词反馈回答 |
| 更新 | `webapp/answers.py`、`webapp/api.py` | `/api/answer` 优先真实 LLM，失败时回退本地片段；新增评估 API |
| 更新 | `webapp/static/` | 增加首次使用引导、评估入口、评估反馈渲染和回答模式提示 |
| 新增/更新 | `tests/test_webapp/` | 覆盖 LLM 请求体、API 回退、评估 API、前端静态入口 |
| 更新 | `README.md`、`docs/guides/*`、`docs/design/api-spec.md`、`docs/release/*`、`CHANGELOG.md` | 同步 C 端能力边界、启动配置和验收说明 |

### 关键行为

- `RAG_LLM_PROVIDER=api` 且存在 `RAG_LLM_API_KEY` / DeepSeek Key 别名时，Web `/api/answer` 优先请求真实模型。
- 真实模型不可用、网络失败或未配置 Key 时，Web 自动回退到本地片段回答，并返回 `mode=local|api|fallback`。
- Web 评估不复用 legacy 桌面端完整 mastery store，先提供从导入文档生成题目、提交回答、反馈得分和建议阅读来源的最小闭环。
- 首屏引导覆盖创建项目空间、导入目录、提问或评估、配置 DeepSeek。

### 测试结果

```text
.venv\Scripts\python.exe -m pytest tests\test_webapp\test_llm.py tests\test_webapp\test_assessment_api.py tests\test_webapp\test_api.py::test_api_import_search_and_answer_flow tests\test_webapp\test_api.py::test_answer_api_uses_injected_llm_client_when_available tests\test_webapp\test_api.py::test_answer_api_falls_back_to_local_answer_when_llm_fails tests\test_webapp\test_frontend_static.py::test_first_run_guide_is_visible_on_web_homepage tests\test_webapp\test_frontend_static.py::test_web_assessment_entrypoint_is_wired -q
9 passed
```

## 2026-05-21 | B-56 — Windows 持久环境变量读取 DeepSeek Key

### 目标

修复当前 Codex/终端进程未继承 Windows User 级 `DEEPSEEK_API_KEY` 时，Web 端无法识别本机已配置 Key 的问题。

### 根因

`load_settings()` 只读取当前进程 `os.environ`。Windows 用户通过系统设置写入环境变量后，已打开的 Codex/PowerShell 进程不会自动刷新，因此进程环境为空，但 User 级持久环境实际存在。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 更新 | `src/config/settings.py` | 新增 Windows User/Machine 持久环境变量读取；当前进程变量仍保持更高优先级 |
| 更新 | `tests/test_application/test_settings_usecases.py` | 新增未继承进程环境时读取持久 DeepSeek Key 的回归测试 |
| 更新 | `README.md`、`docs/guides/setup.md`、`docs/architecture/LLM_PROVIDER_DESIGN.md`、`CHANGELOG.md`、`docs/BACKLOG.md` | 同步配置行为 |

### 验证结果

```text
.venv\Scripts\python.exe -m pytest tests\test_application\test_settings_usecases.py::TestDeepSeekEnvAlias -q
4 passed

真实 DeepSeek 最小调用：
PROVIDER=deepseek
ANSWER_HAS_APP_PY=True
```

## 2026-05-21 | B-57 — Docker 一键启动 Web MVP

### 目标

提供 Docker 模式一键启动，让用户无需本机 Python 虚拟环境即可运行 Web MVP，并保留 DeepSeek 环境变量、运行时数据和可导入目录。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 新增 | `Dockerfile` | 构建只包含 Web MVP 所需文件的 Python 3.11 slim 镜像，不安装 legacy 桌面依赖 |
| 新增 | `compose.yaml` | 映射 `8765:8765`，持久化 `runtime/docker`，挂载 `docker-workspace` 到容器 `/workspace` |
| 新增 | `.dockerignore` | 排除 `.venv`、runtime、release、缓存和本地导入目录 |
| 新增 | `scripts/docker_up.ps1` | Windows 一键启动脚本，自动注入 User 级 `DEEPSEEK_API_KEY` 且不打印 Key |
| 更新 | `.gitignore` | 忽略本地 `docker-workspace/` |
| 新增 | `tests/test_webapp/test_docker_startup.py` | 覆盖 Dockerfile、Compose 和一键脚本关键约束 |
| 更新 | `README.md`、`docs/guides/setup.md`、`docs/guides/testing.md`、`CHANGELOG.md`、`docs/BACKLOG.md` | 同步 Docker 启动和验证方式 |

### 使用方式

```powershell
.\scripts\docker_up.ps1
```

Web 页面创建项目空间时，Docker 默认导入目录填写 `/workspace`，对应宿主机 `docker-workspace/`。

### 验证结果

```text
.\scripts\docker_up.ps1 -NoOpen
HEALTH=healthy
HAS_DEEPSEEK_KEY=True
HTTP /api/health => {"status":"ok"}
Docker API 冒烟：imported=1, answerMode=api, provider=deepseek, sourceCount=1
```

## 2026-05-21 | B-58 — Docker 双击启动与停止入口

### 目标

把 Docker 启动从 PowerShell 命令进一步降低为可双击入口，方便非技术用户在已安装 Docker Desktop 后启动和停止本地 Web MVP。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 新增 | `Start-KnowledgeIsland-Docker.bat` | 双击调用 `scripts/docker_up.ps1` 启动 Docker Web |
| 新增 | `Stop-KnowledgeIsland-Docker.bat` | 双击调用 `scripts/docker_down.ps1` 停止 Docker Web |
| 新增 | `scripts/docker_down.ps1` | 执行 `docker compose down`，支持可选 `-RemoveVolumes` |
| 新增 | `README-Docker-Quickstart.txt` | 面向非技术用户说明启动、导入 `/workspace`、停止和数据位置 |
| 更新 | `README.md`、`docs/guides/setup.md`、`docs/guides/testing.md`、`docs/release/*`、`CHANGELOG.md`、`docs/BACKLOG.md` | 同步 Docker 双击入口和验收方式 |
| 更新 | `tests/test_webapp/test_docker_startup.py` | 覆盖停止脚本、双击包装文件和快速开始说明 |

### 关键行为

- 双击启动入口只负责调用已有 PowerShell 启动脚本，避免复制 Docker Compose 逻辑。
- 双击停止入口调用 `docker compose down`，默认保留 `runtime/docker/` 数据。
- 快速开始明确 Docker 模式页面路径填写 `/workspace`，宿主机文件放入 `docker-workspace/`。

## 2026-05-21 | B-59 — Web 浏览器文件夹导入

### 目标

解决 Docker 模式下后端无法直接读取 Windows 路径的问题，让用户可以像普通本机应用一样在浏览器里选择本地项目文件夹导入。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 新增 | `webapp/upload_import.py` | 接收浏览器上传的文件相对路径和内容，按导入规则入库 |
| 更新 | `webapp/api.py` | 新增 `POST /api/import/upload` |
| 更新 | `webapp/models.py` | `browser-upload:` 项目空间视为可导入来源 |
| 更新 | `webapp/static/index.html`、`webapp/static/js/app.js`、`webapp/static/js/projects.js` | 新增“选择文件夹导入”入口，使用 `webkitdirectory` 读取本地文件夹 |
| 更新 | `tests/test_webapp/` | 覆盖上传导入创建项目、复用项目、跳过规则和前端入口 |
| 更新 | `README.md`、`README-Docker-Quickstart.txt`、`docs/design/api-spec.md`、`docs/guides/*`、`docs/release/*`、`CHANGELOG.md`、`docs/BACKLOG.md` | 同步 Docker 模式导入方式和接口契约 |

### 关键行为

- 浏览器文件夹导入不要求后端访问 Windows 路径，适合 Docker 模式直接选择 `E:\Code\your-project`。
- 未传 `project_id` 时，后端创建 `browser-upload:<project_name>` 项目空间并写入文档记录。
- 前后端都会按文本后缀、忽略目录和 1MB 大小限制跳过文件；后端仍保留最终校验。

## 2026-05-18 | B-50/B-51/B-52 — 追问闭环与优先复测

### 目标

在能力差距报告之后，补齐追问闭环与错题复测能力：支持“继续追问”题目级重答，支持错题优先复测，并补齐边界回归测试。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 扩展 | `src/application/knowledge_mastery_usecases.py` | 新增错题记录实体与内存态追踪，支持 `prioritize_missed` / `focus_knowledge_point_ids` |
| 重构 | `src/desktop/controllers/assessment_controller.py` | 新增 `start_follow_up` 与 `retry_missed_questions` |
| 更新 | `src/desktop/views/assessment_view.py` | 新增“继续追问 / 错题复测”按钮与信号 |
| 更新 | `src/desktop/views/main_window.py` | 接入追问与复测信号 |
| 新增 | `tests/test_application/test_knowledge_mastery_usecases.py` | 新增错题优先与复测清理测试 |
| 更新 | `tests/test_desktop/test_project_knowledge_ui.py` | 增加追问按钮状态与信号回放测试 |

### 关键行为

- 评估会话支持按错题优先复测，缺失错题时按普通策略回退。
- 错题提交会按知识点存储最新状态，并在达标后清理对应记录。
- 差距报告会返回 `follow_up_question_ids`，驱动“继续追问”入口。
- 按钮级回归覆盖“继续追问”和“错题复测”信号触发。

### 测试结果

```text
.venv\Scripts\python -m pytest tests/test_application/test_knowledge_mastery_usecases.py tests/test_desktop/test_project_knowledge_ui.py
18 passed

.venv\Scripts\python -m pytest tests/test_application tests/test_desktop
98 passed
```

---

## 2026-05-18 | B-21 — `.env` 保存保留注释

### 目标

改造 settings 配置写回行为，避免重写 `.env` 时清除注释、空行与手工顺序。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 更新 | `src/config/settings.py` | `save_setting()` 改为按行更新 key，未命中行保留原内容，仅追加新增 key |
| 新增 | `tests/test_application/test_settings_usecases.py` | 新增 `.env` 注释与空行保留回归用例 |
| 更新 | `docs/BACKLOG.md` | 将 B-21 标记为完成 |

### 验证结果

```text
.venv\Scripts\python -m pytest tests\test_application\test_settings_usecases.py tests\test_desktop\test_project_knowledge_ui.py
26 passed
```

---

## 2026-05-18 | B-53 — 阶段10 发布前收口

### 目标

完成上线前最后一轮可交付检查：形成体验压测记录、异常提示覆盖、发布验收清单与发布说明。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 新增 | `docs/release/RELEASE_READINESS_2026-05-18.md` | 新增发布说明（能力边界、验收、体验压测、后续排期） |
| 更新 | `docs/release/NON_TECH_RELEASE_CHECKLIST.md` | 增加评估闭环异常提示与版本验收记录 |
| 更新 | `docs/BACKLOG.md` | 将 B-53 置为完成 |
| 更新 | `CHANGELOG.md` | 记录可发布收口项 |

### 验证结果

```text
.venv\Scripts\python -m pytest tests\test_application\test_knowledge_mastery_usecases.py tests\test_desktop\test_project_knowledge_ui.py -q
18 passed

.venv\Scripts\python.exe scripts\check_docs_consistency.py
[PASS] docs consistency checks passed.
```

---

## 2026-05-11 | B-36~B-37 — 项目知识点模型与提炼用例（完成）

### 目标

完成项目知识库助手的后端第一段能力：持久化项目知识点，并从已入库项目文档中用确定性规则提炼可追溯的知识点。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 新增 | `src/domain/models/project_knowledge.py` | 新增 `ProjectKnowledgePoint` 模型，记录来源文件、证据片段和置信度 |
| 新增 | `src/ports/project_knowledge_store.py` | 新增 `IProjectKnowledgeStore` 持久化接口 |
| 更新 | `src/adapters/storage/db.py` | 新增 `project_knowledge_points` 表和按工作区、类型查询的索引 |
| 新增 | `src/adapters/storage/sqlite_project_knowledge_store.py` | 新增 SQLite 项目知识点存储实现 |
| 更新 | `src/application/container.py` | 将项目知识点存储接入 `AppContainer` |
| 新增 | `src/application/project_analysis_usecases.py` | 新增 `ProjectAnalysisUseCase`，从已存储文档中规则式提炼知识点 |
| 更新 | `tests/test_domain/test_models.py` | 覆盖项目知识点模型创建和序列化 |
| 更新 | `tests/test_adapters/test_storage.py` | 覆盖 SQLite 存储、计数、清空和工作区级联删除 |
| 新增 | `tests/test_application/test_project_analysis_usecases.py` | 覆盖容器接线、提炼规则、重复分析替换旧结果和工作区不存在错误 |

### 关键行为

- `ProjectKnowledgePoint` 保留知识点名称、类型、摘要、来源文件、证据片段和置信度。
- `IProjectKnowledgeStore` 与 SQLite 实现支持按工作区批量保存、查询、删除和计数。
- `project_knowledge_points` 表通过 `workspace_id` 关联工作区，并补充工作区索引和工作区加类型索引。
- `AppContainer` 已暴露 `project_knowledge_store`，供应用用例复用。
- `ProjectAnalysisUseCase` 从已存储的 `Document` 记录中提炼知识点，不直接扫描文件系统。
- 提炼范围覆盖技术栈关键词、配置文件名、测试目录或测试文件线索、Markdown 流程类标题。
- 当前是规则式粗提炼，不是精确依赖分析。
- 去重按当前文档遍历顺序保留第一条证据。

### 测试结果

```text
.venv\Scripts\python.exe -m pytest tests\test_domain tests\test_adapters\test_storage.py tests\test_application\test_project_analysis_usecases.py tests\test_application\test_ingestion_usecases.py -v
```

结果：57 passed。

### 未涉及

- 未调用 LLM。
- 未实现自动出题。
- 未实现回答评分。
- 未实现能力差距报告。
- 未新增 UI 展示。

---

## 2026-05-11 | B-32~B-35 — 项目知识库界面骨架（完成）

### 目标

完成项目知识库助手第一阶段骨架：产品定位文档、主导航、首次使用指引和掌握评估页面占位。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 更新 | `README.md` | 产品定位从 Career Assistant 调整为项目知识库助手 |
| 更新 | `docs/architecture/SYSTEM_ARCHITECTURE.md` | 更新产品定位和第一版主线 |
| 更新 | `docs/architecture/RAG_PIPELINE.md` | 补充项目知识库与掌握评估扩展链路 |
| 更新 | `src/desktop/views/main_window.py` | 主导航调整为项目问答 / 我的项目 / 知识库 / 掌握评估 / 设置 |
| 更新 | `src/desktop/views/query_view.py` | 页面文案调整为项目问答，并增加开始评估入口 |
| 更新 | `src/desktop/views/guide_view.py` | 首次使用指引改为导入项目 / 建立索引 / 开始使用三步 |
| 新增 | `src/desktop/views/assessment_view.py` | 新增掌握评估页面占位 |
| 新增 | `tests/test_desktop/test_project_knowledge_ui.py` | 增加 UI 文案和页面导入测试 |

### 测试结果

```text
.venv\Scripts\python.exe -m pytest tests\test_desktop\test_project_knowledge_ui.py -v
.venv\Scripts\python.exe -m pytest tests\test_application tests\test_domain tests\test_adapters -v
git diff --check -- 本次改动文件
```

全量 `git diff --check` 仍受任务外既有文档尾随空格影响，失败文件为
`docs/architecture/ARCHITECTURE_ENTERPRISE_BASELINE.md` 与
`docs/architecture/STRUCTURE_BASELINE.md`，本次未扩大清理范围。

### 未涉及

- 未新增数据库表。
- 未实现自动出题。
- 未实现回答评估和能力差距报告。
- 简历、JD 匹配、面试脚本仍保留为后续输出能力。

---

## 2026-05-11 | 项目知识库助手方向设计（文档）

### 目标

将项目主线从 Career Assistant / 简历助手调整为“项目知识库助手”。第一版不拆 Web 前端，继续基于现有 PySide6 桌面端，优先完成代码项目导入、项目问答、掌握评估和能力差距报告闭环。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 新增 | `docs/superpowers/specs/2026-05-11-project-knowledge-base-design.md` | 定义产品定位、界面文案、主界面布局、项目导入、知识点提炼、自动出题、掌握评估、知识库辅助管理和分阶段落地 |
| 更新 | `docs/BACKLOG.md` | 新增 B-32~B-42，作为项目知识库助手方向的后续实现队列 |
| 更新 | `docs/DEVLOG.md` | 记录本次设计决策和文档范围 |

### 关键决策

- UI 不直接使用“第二大脑”词语，对外统一为“项目知识库 / 项目问答 / 掌握评估 / 能力差距”。
- 主体验采用 Codex 聊天式项目问答，辅助区参考 SAS 后台式知识库，用于追踪项目状态、文件、知识点和题库。
- 简历、JD 匹配、面试脚本降级为后续输出工具，不作为第一版主导航核心。
- 第一版掌握评估采用自动出题：系统围绕项目知识点生成题目，用户回答后输出掌握情况和建议阅读文件。
- AI 评估必须保留来源、参考要点和判断原因，避免黑盒结论。

### 未涉及

- 未修改业务代码。
- 未新增数据库表。
- 未调整 PySide6 页面。
- 未执行测试；本次为设计和计划文档更新。

---

## 2026-04-18 | P1–P7 — 代码质量优化（完成）

### 目标

修复分析阶段识别的 7 处 Bug / UX 缺陷 / 功能缺失，并补充测试覆盖。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 重写 | `src/desktop/views/generation_view.py` | P1：`on_failed` 将错误写入输出框；P2：`_active_output` 追踪避免遍历逻辑；P4：按钮点击时校验必填项，空值弹出 `QMessageBox.warning` |
| 修复 | `src/application/generation_usecases.py` | P3：三个用例均在空检索时提前返回 `⚠️` 警告，不再将空 context 发给 LLM |
| 修复 | `src/desktop/views/settings_view.py` | P5：新增 `QDoubleSpinBox`（温度 0.0–2.0）和 `QSpinBox`（最大 Token 256–8192）并加载/保存 |
| 修复 | `src/application/settings_usecases.py` | P5：新增 `save_llm_temperature` / `save_llm_max_tokens` 两个方法 |
| 修复 | `src/desktop/views/main_window.py` | P5：`_on_settings_save` 中增加数值型字段的保存逻辑（独立判断，0.0 也合法） |
| 新增 | `tests/test_application/test_generation_usecases.py` | P6：覆盖三个生成用例正常路径 + P3 空检索保护，共 9 个测试 |
| 新增 | `tests/test_application/test_settings_usecases.py` | P7：settings 读写往返测试（含 P5 新字段），共 17 个测试；用 `monkeypatch` 隔离 `_app_data_dir` |

### Bug 详情

**P1（🔴）** `generation_view.on_failed` 原实现仅恢复按钮，用户看不到任何错误信息。
→ 现在将 `❌ 生成失败：{error}` 写入活跃输出框。

**P2（🔴）** `on_finished/on_progress` 通过扫描三个输出框的第一个空框来判断目标，
多标签快速点击时会写错框。→ 用 `self._active_output: Optional[QTextEdit]` 在点击时记录，
`on_*` 直接写入，完成后置 `None`。

**P3（🟠）** 检索结果为空时将空字符串 context 发给 LLM 导致幻觉输出。
→ 三个用例在 `if not result.chunks` 时立即返回 `sources_used=0` 的警告结果。

**P4（🟠）** 用户点击生成按钮时若未填写关键词或项目名称，信号会被 emit 但 LLM 收到空提示。
→ 每个点击槽先校验，不通过则弹出 `QMessageBox.warning` 并 return。

**P5（🟡）** 设置页缺少 LLM 温度和最大 Token 控制，用户无法通过 UI 调节。
→ UI + UseCase + MainWindow 三层全部打通，温度和 Token 数可在设置页持久化。

### 测试结果

```
98 passed in 1.31s（含新增 26 个测试：9 generation + 17 settings）
```

---

## 2026-04-18 | B-13 — Crimson × Gold 主题（完成）

### 目标

将 Codex 蓝色主题替换为「红黑渐变 + 金色点缀」主题，同时修复设计系统审计发现的全部 hardcoded 颜色值。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 重写 | `src/desktop/style.py` | 全新 Crimson × Gold 色板；新增 `BTN_PRIMARY_*` / `SPACE_*` / `QRadioButton` 样式；侧边栏 `qlineargradient` 渐变 |
| 修复 | `src/desktop/views/query_view.py` | 9 处 hardcoded hex → token；CTA 按钮改用 `primary="true"` 属性；标签改用 `secondary="true"` 属性 |
| 修复 | `src/desktop/views/workspace_view.py` | `#4493f8` → `ACCENT`；导入 style tokens |
| 修复 | `src/desktop/views/ingestion_view.py` | `color: gray` → `secondary="true"` 属性；`font-weight: bold` → `title="true"` 属性 |
| 修复 | `src/desktop/views/generation_view.py` | 页面标题改用 `title="true"` 属性 |

### 色板变化

| Token | 旧值（Codex 蓝） | 新值（Crimson × Gold） |
|-------|----------------|----------------------|
| `BG_PRIMARY` | `#0f1117` | `#0e0b0b` |
| `BG_SECONDARY` | `#161b22` | `#160d0d` |
| `BG_SELECTED` | `#1e2a3a` | `#2e1a0e` |
| `ACCENT` | `#4493f8`（蓝） | `#c9a84c`（金）|
| `TEXT_PRIMARY` | `#e6edf3`（冷白） | `#f0e6dc`（暖白）|
| `BORDER` | `#30363d` | `#3a2020` |

### 新增 token

```python
BTN_PRIMARY_BG      = "#5c1a1a"   # CTA 按钮背景
BTN_PRIMARY_HOVER   = "#7a2020"
BTN_PRIMARY_PRESSED = "#3e1010"
SPACE_XS / SM / MD / LG / XL     # 8px 网格间距常量
```

---

## 2026-04-18 | B-12 — 使用流程简化（完成）

### 目标

将原来需要 6 步的新用户启动流程压缩到 3 步，消除页面跳转摩擦感。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 重写 | `src/desktop/views/workspace_view.py` | 状态指示符；▶索引快捷按钮；创建对话框「目录→名称自动填写」；emit Workspace 对象 |
| 重写 | `src/desktop/views/query_view.py` | 三态设计（空/未索引/就绪）；未索引态内联「立即建立索引」按钮 |
| 重写 | `src/desktop/views/main_window.py` | 导航 5→4 项（指引改为 ？ 帮助弹窗）；默认落地页改为问答；创建工作区后自动触发索引；索引完成后刷新列表状态 |

### 流程对比

| | 旧流程 | 新流程 |
|---|--------|--------|
| 步骤数 | 6 步 | 3 步 |
| 落地页 | 知识库索引（空页） | 问答（友好空状态） |
| 建立索引 | 需要手动跳转页面 + 点按钮 | 创建工作区后自动触发 |
| 工作区名称 | 手动填写 | 从所选目录名自动填写 |
| 指引入口 | 主导航第 5 项 | 侧边栏底部 ？按钮弹窗 |

### 关键设计决策

- `workspace_selected` 信号改为 emit `Workspace` 对象（不只是 ID），使问答页能直接判断索引状态
- `QueryView` 用 `QStackedWidget` 管理三种状态，每种状态对应独立 UI 片段
- `_on_workspace_created` 在创建后自动调 `ingest_ctrl.start()`，无需用户切换页面

---

## 2026-04-17 | B-02 — README 重写（完成）

### 目标

将完全过时的 README（仍引用已删除的 `backend/`、`desktop/`、`frontend/`、`archive/` 目录）替换为反映当前六边形架构的完整文档。

### 变更文件

| 操作 | 路径 |
|------|------|
| 重写 | `README.md` |

### 内容覆盖

- 功能概览表
- 安装步骤（venv + pip）
- Ollama 配置（serve + 模型拉取命令）
- 云端 API 配置（DeepSeek / OpenAI / 通义 / Kimi 参数表）
- API Key 三级安全策略说明
- 完整项目目录树（含每层说明）
- 架构原则（六边形 / 唯一组装点 / frozen 模型 / Qt 线程隔离）
- 测试运行命令
- 开发文档索引

---

## 2026-04-17 | B-01 — 自动化测试套件（完成）

### 目标

建立零网络依赖的 pytest 测试基础，覆盖 domain / adapter / application 三层，为后续重构提供安全网。

### 变更文件

| 操作 | 路径 |
|------|------|
| 新建 | `tests/__init__.py` |
| 新建 | `tests/conftest.py` |
| 新建 | `tests/test_domain/__init__.py` |
| 新建 | `tests/test_domain/test_models.py` |
| 新建 | `tests/test_adapters/__init__.py` |
| 新建 | `tests/test_adapters/test_storage.py` |
| 新建 | `tests/test_application/__init__.py` |
| 新建 | `tests/test_application/test_workspace_usecases.py` |
| 新建 | `tests/test_application/test_ingestion_usecases.py` |
| 新建 | `tests/test_application/test_query_usecases.py` |
| 修改 | `src/adapters/storage/sqlite_workspace_store.py` — `INSERT OR REPLACE` 修复 upsert 语义 |

### 测试结构

```
tests/
├── conftest.py                    # session 级 fixtures：AppContainer.build_for_testing()
├── test_domain/
│   └── test_models.py             # Document / Chunk / Workspace / Task / ConversationRecord / Errors
├── test_adapters/
│   └── test_storage.py            # 全部 5 个 SQLite Store + 级联删除
└── test_application/
    ├── test_workspace_usecases.py # WorkspaceUseCases CRUD
    ├── test_ingestion_usecases.py # 摄入流程：正常 / 空目录 / 重建索引 / 进度事件
    └── test_query_usecases.py     # execute / execute_streaming / get_history / _build_prompt
```

### 设计决策

- `AppContainer.build_for_testing()` 使用 `:memory:` SQLite + `DummyEmbedder` + `KeywordRetriever` + `_FakeLLM`，全程无网络 / 无文件残留
- `conftest.py` 中 `container` fixture 每个测试独立实例化，数据完全隔离
- `_FakeLLM.generate()` 固定返回 `[test answer]`，`stream()` yield 同一字符串，使 LLM 行为确定性可断言
- `ConversationStore` 受 FK 约束（`workspace_id` → `workspaces`），测试须先建 workspace

### 结果

```
72 passed in 0.85s
```

---

## 2026-04-15 | Step 1 — 配置层（src/config/）

### 目标

消灭 `backend/app/config.py` 中硬编码的 `F:\PersonalRAG` 路径，建立唯一、可测试的配置入口。

### 变更文件

| 操作 | 路径 |
|------|------|
| 新建 | `src/__init__.py` |
| 新建 | `src/config/__init__.py` |
| 新建 | `src/config/defaults.py` |
| 新建 | `src/config/settings.py` |
| 新建 | `src/config/paths.py` |
| 新建 | `.env.example` |

### 设计决策

- `AppSettings` 使用 `@dataclass(frozen=True)`，构造后不可变，可安全跨线程传递
- `load_settings()` 按优先级合并：OS 环境变量 > appdata/.env > 项目根 .env > defaults.py
- 不引入 `python-dotenv` 外部依赖，使用标准库手动解析 .env（保持 config 层零第三方依赖）
- `kb_root` 默认指向用户主目录下的 `CareerAssistantKB`，不依赖特定盘符

### 解决的 Bug

- **P0**：`backend/app/config.py:4` `DATA_ROOT = Path(r"F:\PersonalRAG")` 在无 F: 盘机器上崩溃

### 验证结果

```
kb_root       : C:\Users\...\CareerAssistantKB   ✅ 无硬编码盘符
ollama_model  : qwen2.5:7b                        ✅ 默认值生效
chunk_size    : 512                               ✅ int 转换正确
override_env  : 传入覆盖字典后立即生效             ✅ 测试友好
frozen        : FrozenInstanceError               ✅ 不可变，线程安全
save_setting  : 持久化写入 appdata/.env           ✅ 格式正确
```

### 未涉及

- 旧 `backend/app/config.py` 尚未删除（等 Step 4 存储层迁移完成后一并清理）

---

## 2026-04-15 | Step 2 — 领域模型层（src/domain/）

### 目标

建立项目的核心数据模型，全部使用 `frozen=True` dataclass，零 I/O，零第三方依赖。

### 变更文件

| 操作 | 路径 |
|------|------|
| 新建 | `src/domain/__init__.py` |
| 新建 | `src/domain/errors.py` |
| 新建 | `src/domain/models/__init__.py` |
| 新建 | `src/domain/models/document.py` |
| 新建 | `src/domain/models/chunk.py` |
| 新建 | `src/domain/models/workspace.py` |
| 新建 | `src/domain/models/task.py` |
| 新建 | `src/domain/models/conversation.py` |

### 设计决策

- 所有模型 `frozen=True`：不可变，可安全跨 QThread 传递，无需加锁
- `Document` 不再内置 `from_path()` classmethod（移至 Step 10 的 `tagger` 领域服务）
- `Task` 使用枚举类型 `TaskStatus` / `TaskKind`，避免散落的魔法字符串
- `id` 字段统一用 `uuid4()` 生成，不依赖数据库自增

### 验证结果

```
Document / Chunk / Workspace / Task / ConversationRecord  ✅ 全部可构建
frozen=True                                               ✅ FrozenInstanceError
Task.update() / Workspace.with_index_stats()              ✅ 返回新实例
TaskStatus / TaskKind 枚举                                ✅ .value 序列化正常
NotFoundError / IndexNotReadyError                        ✅ 异常层级正确
```

### 未涉及

- 领域服务（chunker / tagger / jd_analyzer）在 Step 10 用例层实现时一并加入

---

## 2026-04-15 | Step 3 — Port 接口层（src/ports/）

### 目标

定义所有抽象接口契约，确保 adapters 与 application 层通过接口而非具体实现耦合。

### 变更文件

| 操作 | 路径 |
|------|------|
| 新建 | `src/ports/__init__.py` |
| 新建 | `src/ports/embedder.py`（IEmbedder）|
| 新建 | `src/ports/vector_store.py`（IVectorStore）|
| 新建 | `src/ports/retriever.py`（IRetriever + RetrievalQuery/Result）|
| 新建 | `src/ports/llm_client.py`（ILLMClient + LLMRequest/Response）|
| 新建 | `src/ports/document_store.py`（IDocumentStore）|
| 新建 | `src/ports/chunk_store.py`（IChunkStore）|
| 新建 | `src/ports/task_store.py`（ITaskStore）|
| 新建 | `src/ports/workspace_store.py`（IWorkspaceStore）|
| 新建 | `src/ports/conversation_store.py`（IConversationStore）|

### 设计决策

- 全部使用 `ABC` + `@abstractmethod`，无法直接实例化
- `IEmbedder.dimension` 为 `@property @abstractmethod`，强制实现声明维度
- `IVectorStore.search()` 支持 `domain` 过滤参数，为生成类用例（只检索 resume 域）提供性能优化空间
- `ILLMClient.stream()` 返回 `Iterator[str]`，配合 Qt Worker 的 `token_received` 信号实现流式输出

### 验证结果

```
9 个接口全部为 ABC（无法直接实例化）  ✅
RetrievalQuery / LLMRequest 冻结数据类  ✅
```

---

## 2026-04-15 | Step 4 — 存储适配层（src/adapters/storage/）

### 目标

实现所有 SQLite Port 接口，消灭旧 `backend/infra/storage/db/sqlite.py` 中 `PROJECT_ROOT` 硬编码。

### 变更文件

| 操作 | 路径 |
|------|------|
| 新建 | `src/adapters/__init__.py` |
| 新建 | `src/adapters/storage/__init__.py` |
| 新建 | `src/adapters/storage/db.py`（连接工厂 + Schema DDL）|
| 新建 | `src/adapters/storage/sqlite_workspace_store.py` |
| 新建 | `src/adapters/storage/sqlite_document_store.py` |
| 新建 | `src/adapters/storage/sqlite_chunk_store.py` |
| 新建 | `src/adapters/storage/sqlite_task_store.py` |
| 新建 | `src/adapters/storage/sqlite_conversation_store.py` |

### 设计决策

- `create_connection(db_path: Path)` 接收路径参数，不持有任何全局状态
- `init_schema()` 幂等：`CREATE TABLE IF NOT EXISTS` + `CREATE INDEX IF NOT EXISTS`
- `row_factory = sqlite3.Row`：允许按列名访问，无需位置索引
- `FOREIGN KEY ... ON DELETE CASCADE`：删除工作区自动清理关联文档、分块、对话
- tags 字段用 JSON 字符串存储（`json.dumps`），避免引入额外依赖
- `INSERT OR REPLACE` 实现 upsert 语义，重建索引时无需先删再插

### 验证结果

```
Workspace CRUD（含 update 索引状态）  ✅
Document batch save / exists          ✅
Chunk batch save / count              ✅
Task create / update status           ✅
Conversation save / list_recent       ✅
级联删除（DELETE workspace → 清空子表）✅
```

---

## 2026-04-16 | Steps 5-10 — Adapters + Application 层

### 变更文件

| 操作 | 路径 |
|------|------|
| 新建 | `src/adapters/llm/ollama_adapter.py`（OllamaAdapter）|
| 新建 | `src/adapters/embedding/ollama_embedder.py`（OllamaEmbedder + DummyEmbedder）|
| 新建 | `src/adapters/vector_store/chroma_store.py`（ChromaVectorStore）|
| 新建 | `src/adapters/vector_store/numpy_store.py`（NumpyVectorStore，零依赖备选）|
| 新建 | `src/adapters/retrieval/vector_retriever.py`（VectorRetriever）|
| 新建 | `src/adapters/retrieval/keyword_retriever.py`（KeywordRetriever，降级）|
| 新建 | `src/application/container.py`（AppContainer，唯一组装点）|
| 新建 | `src/application/workspace_usecases.py` |
| 新建 | `src/application/ingestion_usecases.py`（含分块 + 标签推断）|
| 新建 | `src/application/query_usecases.py`（阻塞 + 流式）|
| 新建 | `src/application/generation_usecases.py`（简历 / JD / 面试）|
| 新建 | `src/application/task_usecases.py` |
| 新建 | `src/application/settings_usecases.py` |
| 安装 | `ollama`, `chromadb`, `numpy` |

### 设计决策

- `AppContainer.build_for_testing()` 提供零网络依赖的测试工厂（内存 SQLite + DummyEmbedder + KeywordRetriever + FakeLLM）
- `IngestWorkspaceUseCase.execute()` 为生成器，yield `IngestProgress`，调用方（Worker）驱动迭代并转发进度信号
- `QueryKnowledgeBaseUseCase` 同时支持 `execute()`（阻塞）和 `execute_streaming()`（流式，传入 `on_token` 回调）
- `ChromaVectorStore` cosine distance [0,2] 转换为相似度 [0,1]：`score = 1 - dist/2`
- `KeywordRetriever` 作为 Ollama 不可用时的降级，`retriever_kind=keyword` 时启动自动热载 DB 中的 chunks

### 验证结果

```
AppContainer.build_for_testing()        ✅
WorkspaceUseCases CRUD                  ✅
IngestWorkspaceUseCase（真实文件 I/O）  ✅  1 文件 / 1 片段
QueryKnowledgeBaseUseCase               ✅  sources=1, history 持久化
GenerateResumeUseCase                   ✅
MatchJDUseCase                          ✅
GenerateInterviewScriptUseCase          ✅
TaskUseCases                            ✅
```

---

## 2026-04-16 | Step 11 — Qt Worker 基础设施（src/desktop/workers/）

### 目标

建立 Qt 线程安全基础：所有长时操作在 QThread 中执行，通过 Signal 与主线程通信。

### 变更文件

| 操作 | 路径 |
|------|------|
| 新建 | `src/desktop/__init__.py` |
| 新建 | `src/desktop/workers/__init__.py` |
| 新建 | `src/desktop/workers/base_worker.py` |
| 新建 | `src/desktop/workers/ingest_worker.py` |
| 新建 | `src/desktop/workers/query_worker.py` |
| 新建 | `src/desktop/workers/generate_worker.py` |

### 设计决策

- `BaseWorker(QThread)` 统一 try/except，子类只需实现 `_execute()`
- `QueryWorker` 额外定义 `token_received = Signal(str)` 支持流式输出
- 所有 Worker 持有 use-case 引用（接口类型），不直接 import adapter

---

## 2026-04-16 | Steps 11-12 — Qt 桌面层（workers / controllers / views）

### 变更文件

| 操作 | 路径 |
|------|------|
| 新建 | `src/desktop/workers/base_worker.py`（BaseWorker, WorkerResult）|
| 新建 | `src/desktop/workers/ingest_worker.py` |
| 新建 | `src/desktop/workers/query_worker.py`（含 token_received Signal）|
| 新建 | `src/desktop/workers/generate_worker.py` |
| 新建 | `src/desktop/controllers/workspace_controller.py` |
| 新建 | `src/desktop/controllers/ingestion_controller.py` |
| 新建 | `src/desktop/controllers/query_controller.py` |
| 新建 | `src/desktop/controllers/generation_controller.py` |
| 新建 | `src/desktop/views/task_status_bar.py` |
| 新建 | `src/desktop/views/workspace_view.py` |
| 新建 | `src/desktop/views/ingestion_view.py` |
| 新建 | `src/desktop/views/query_view.py`（流式打字机显示）|
| 新建 | `src/desktop/views/generation_view.py`（三标签页）|
| 新建 | `src/desktop/views/settings_view.py` |
| 新建 | `src/desktop/views/main_window.py`（完整布局 + 全部 Controller 组装）|
| 新建 | `src/desktop/bootstrap.py`（启动序列 + 首次运行检测）|
| 新建 | `app.py`（唯一可执行入口）|

### 设计决策

- `BaseWorker.run()` 统一 try/except，子类只需实现 `_execute()`，异常自动转为 `error_occurred` 信号
- `QueryWorker` 额外定义 `token_received = Signal(str)`，配合 `execute_streaming(on_token=...)` 实现打字机效果
- `GenerateWorker` 统一处理三种生成用例，通过鸭子类型不区分具体类
- `MainWindow.__init__` 接收 `AppContainer`，在 `_wire_controllers()` 中完成所有信号-槽连接
- `bootstrap.py` 负责首次运行检测（kb_root 不存在时询问创建），Ollama 不可用时给 warning 但不阻断启动

### 验证结果

```
config / domain / ports / adapters / application 层  ✅ 全部导入成功
desktop 层（Worker / Controller / View）             ✅ 导入成功（依赖 PySide6）
app.py 入口                                          ✅ 创建完成
```

---

## 2026-04-16 | Step 13 — 清理旧代码（backend/ & desktop/）

### 目标

删除迁移前遗留的 `backend/` 和 `desktop/` 旧目录，重写 `scripts/` 脚本以使用新 `src/` 路径，完成架构切割。

### 变更文件

| 操作 | 路径 |
|------|------|
| 重写 | `scripts/init_storage.py` |
| 重写 | `scripts/seed_demo_files.py` |
| 重写 | `scripts/first_run_check.py` |
| 重写 | `scripts/import_markdown_paths.py` |
| 重写 | `scripts/migration_gate_check.py` |
| **删除** | `backend/`（整个目录） |
| **删除** | `desktop/`（整个目录） |
| 更新 | `docs/architecture/STRUCTURE_BASELINE.md`（移除遗留目录描述） |

### 脚本迁移对照

| 脚本 | 旧依赖 | 新依赖 |
|------|--------|--------|
| `init_storage.py` | `backend.app.config.REQUIRED_DIRS` | `src.config.paths.ensure_runtime_dirs/ensure_kb_dirs` + `src.adapters.storage.db` |
| `seed_demo_files.py` | `backend.app.config.RAW_PATH` | `src.config.settings.load_settings().kb_root` |
| `first_run_check.py` | `SettingsService / WorkspaceService / init_runtime_db / startup_checks` | `src.config.settings` + `src.adapters.storage.db` + `ollama` 可用性检查 |
| `import_markdown_paths.py` | `backend.app.modules.knowledge_base.ingestion.PathImportService` | 内联实现（`shutil.copy2` + `src.config.paths.kb_domain_dir`） |
| `migration_gate_check.py` | 检查旧 `backend.*` 路径 | 检查新 `src.*` 路径，调用重写后的 `first_run_check` |

### 设计决策

- `import_markdown_paths.py` 不再依赖旧 `PathImportService`，改为内联 `shutil.copy2` 实现，保持脚本自包含
- `migration_gate_check.py` 的 `REQUIRED_IMPORTS` 列表覆盖新架构全部 31 个关键模块，作为日后重大变更的快速冒烟测试
- 保留 `frontend/` 和 `archive/` 目录（归档用途，不参与新架构）

### 验证结果

```
backend/ 已删除    ✅
desktop/ 已删除    ✅
scripts/ 全部无旧 backend/desktop 引用  ✅
STRUCTURE_BASELINE 遗留目录说明已更新   ✅
```

---

## 2026-04-16 | Step 14 — 彻底清理历史遗留

### 目标

删除所有与新架构无关的历史目录和脚本，确保项目根目录中不存在任何遗留引用。

### 变更文件

| 操作 | 路径 |
|------|------|
| **删除** | `archive/legacy-20260407/`（旧 FastAPI + pywebview 方案，功能已全部迁移至 `src/`） |
| **删除** | `frontend/`（旧 Vite + Vue3 Web 前端，已被 PySide6 Qt 原生 UI 替代） |
| **删除** | `scripts/gui.py`（旧 Tkinter 启动器，含硬编码 `F:\PersonalRAG`，已被 `app.py` + `MainWindow` 替代） |
| 重写 | `scripts/check_import_paths.py`（扫描目录从已删除的 `backend/` `desktop/` 改为 `src/` `scripts/`；拦截前缀扩展为完整旧路径列表） |

### 清理后的目录结构

```
rag_system/
├── app.py          唯一可执行入口
├── src/            新架构（六层，100% 完成）
├── scripts/        运维脚本（全部已适配 src/）
├── docs/           架构文档 + 开发日志
├── data/           示例数据占位
├── ops/            运维框架占位
└── runtime/        运行时目录（db + vectors）
```

### 验证结果

```
check_import_paths.py   ✅ 76 个文件，0 处旧架构引用
migration_gate_check.py ✅ 31 个 src/ 模块全部导入成功
                        ⚠️ Ollama 未运行（预期，非问题）
```

---

## 2026-04-16 | Step 15 — 端到端启动验证与 Bug 修复

### 目标

首次真实运行 `app.py`，修复静态审查和启动测试中发现的 bug，确认全部依赖就绪。

### Bug 修复

| 文件 | 行 | 问题 | 修复 |
|------|----|------|------|
| `src/desktop/views/main_window.py` | 121 | `_build_ui()` 中引用了未定义的局部变量 `container`，应为 `self._container` | 改为 `self._container.settings` |

### 依赖安装

| 包 | 版本 | 说明 |
|----|------|------|
| `chromadb` | 1.5.7 | 向量存储依赖，此前未安装 |

### 验证结果

```
依赖检查（PySide6 / chromadb / ollama / numpy）  ✅ 全部可用
AppContainer.build()（vector 模式）              ✅ 无异常
app.py 启动（超时退出）                          ✅ 无 stderr 输出，无崩溃
信号链静态核查（全部 View / Controller / Worker） ✅ 参数类型匹配
check_import_paths.py                           ✅ 76 文件 0 违规
```

### 已建立

- `docs/BACKLOG.md`：记录 B-01 ~ B-08 后续工作项

---

## 2026-04-16 | Step 16 — UI 重设计（Codex 风格）+ 使用指引

### 目标

参考 Codex 桌面端视觉风格重新设计界面：深色主题、低对比度选中态、统一间距；
同时新增使用指引页，帮助用户快速上手。

### 变更文件

| 操作 | 路径 |
|------|------|
| 新建 | `src/desktop/style.py`（全局 QSS 样式表） |
| 新建 | `src/desktop/views/guide_view.py`（使用指引页） |
| 重写 | `src/desktop/views/main_window.py`（应用样式 + 加入指引导航） |

### 设计决策

**色彩系统（`style.py`）**

| 用途 | 颜色 | 原因 |
|------|------|------|
| 主背景 | `#0f1117` | 近黑但不纯黑，减少对比疲劳 |
| 侧边栏 | `#161b22` | 比主背景亮一级，形成层次感 |
| 选中背景 | `#1e2a3a` | 低饱和蓝调，不刺眼 |
| 选中指示 | 左侧 2px `#4493f8` 边框 | 与高亮填充相比视觉噪音更小 |
| 强调色 | `#4493f8` | 仅用于边框/图标，不大面积填充 |

旧版选中态 `background: #e0e8ff` 替换为 `background: #1e2a3a + 左边框`，减少视觉刺激。

**使用指引（`guide_view.py`）**

- 6 步骤卡片：Ollama 安装 → 创建工作区 → 索引 → 问答 → 生成 → 设置
- 每张卡片含彩色标签（前提/知识库/问答/生成/设置）
- 首次启动自动跳转到指引页（通过 `runtime/.guide_shown` 标记文件判断）

**导航栏调整**

- 新增第 5 项导航：`📖 指引`（index = 4）
- 导航按钮改用 `nav="true"` property，与 QSS 中的专用规则绑定
- 侧边栏底部增加版本号标注

### 验证结果

```
src.desktop.style       ✅ 导入成功
src.desktop.views.guide_view  ✅ 导入成功
src.desktop.views.main_window ✅ 导入成功
```

### Backlog 状态更新

- B-09（UI 重设计）→ 已完成
- B-10（使用指引）→ 已完成

---

## 2026-04-16 | Step 17 — 云端 LLM API 支持（B-11）

### 目标

新增 OpenAI 兼容 API 适配器，支持 DeepSeek / OpenAI / 通义千问 / Kimi 等云端服务；
设置页提供提供商切换 UI；API Key 支持通过 OS 环境变量注入，无需写入文件。

### 变更文件

| 操作 | 路径 |
|------|------|
| 更新 | `src/config/defaults.py`（新增 5 个默认值） |
| 更新 | `src/config/settings.py`（AppSettings 新增 5 个字段，OS 环境变量扫描扩展） |
| 新建 | `src/adapters/llm/openai_compat_adapter.py` |
| 更新 | `src/application/container.py`（LLM + Embed 双路由逻辑） |
| 更新 | `src/application/settings_usecases.py`（新增 5 个 save 方法） |
| 重写 | `src/desktop/views/settings_view.py`（提供商分组 + 环境变量感知 UI） |
| 更新 | `src/desktop/views/main_window.py`（_on_settings_save 处理新字段） |
| 新建 | `docs/architecture/LLM_PROVIDER_DESIGN.md` |
| 安装 | `openai` SDK |

### API Key 安全策略（核心设计）

| 来源 | 安全级别 | UI 行为 |
|------|---------|---------|
| OS 环境变量 `RAG_LLM_API_KEY` | 最高（内存，不写盘） | 显示绿色「已从环境变量读取」，字段禁用 |
| `appdata/.env`（UI 填写） | 中（本机明文文件） | 密文输入框，右侧「显示」按钮 |
| 项目 `.env` | 低（注意 .gitignore） | 同上 |

无论哪种来源，UI 均不回显明文 API Key。

### 新增配置字段

| 字段 | 环境变量 | 默认值 |
|------|---------|--------|
| `llm_provider` | `RAG_LLM_PROVIDER` | `"ollama"` |
| `llm_api_base` | `RAG_LLM_API_BASE` | `"https://api.deepseek.com/v1"` |
| `llm_api_key` | `RAG_LLM_API_KEY` | `""` |
| `llm_api_model` | `RAG_LLM_API_MODEL` | `"deepseek-chat"` |
| `embed_provider` | `RAG_EMBED_PROVIDER` | `"ollama"` |

### 支持的提供商（内置快捷填充）

- DeepSeek：`https://api.deepseek.com/v1`
- OpenAI：`https://api.openai.com/v1`
- 通义千问：`https://dashscope.aliyuncs.com/compatible-mode/v1`
- Kimi（Moonshot）：`https://api.moonshot.cn/v1`
- 任意 OpenAI 兼容接口（自定义 base_url）

### 验证结果

```
src.config.settings                      ✅
src.adapters.llm.openai_compat_adapter   ✅
src.application.container                ✅
src.application.settings_usecases        ✅
src.desktop.views.settings_view          ✅
src.desktop.views.main_window            ✅
```

---

---

## 2026-05-02 | B-14~B-19, B-04 — 功能完善与性能优化（P0+P1）

### 目标

修复项目分析中识别的 7 处关键缺陷，涵盖工程化缺失、核心逻辑 Bug、性能瓶颈和检索质量。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 新建 | `requirements.txt` | 核心依赖清单（PySide6 / ollama / chromadb / numpy / openai / jieba）|
| 新建 | `requirements-dev.txt` | 开发依赖（pytest）|
| 更新 | `docs/BACKLOG.md` | 新增 B-14~B-31 共 18 个工作项 |
| **重写** | `src/application/ingestion_usecases.py` | B-15: `force_reindex` 增量索引；B-17: Markdown 结构感知分块；B-04: `IngestProgress` 增加 `stage`/`elapsed_ms` 字段 |
| 更新 | `src/ports/document_store.py` | B-15: 新增 `delete(document_id)` 抽象方法 |
| 更新 | `src/adapters/storage/sqlite_document_store.py` | B-15: 实现 `delete()`，利用 ON DELETE CASCADE 清理关联 chunks |
| **重写** | `src/adapters/retrieval/keyword_retriever.py` | B-16: `_tokenize` 升级为 jieba + bigram 中文分词；懒加载 jieba |
| **重写** | `src/adapters/embedding/ollama_embedder.py` | B-18: `embed_batch` 使用 `ThreadPoolExecutor` 并行（默认 3 线程）；每线程独立 `ollama.Client` |
| 更新 | `src/ports/chunk_store.py` | B-19: 新增 `list_by_ids(chunk_ids)` 批量加载接口 |
| 更新 | `src/adapters/storage/sqlite_chunk_store.py` | B-19: 实现 `list_by_ids`，单次 SQL `IN (...)` 查询替代 N 次 `get()` |
| **重写** | `src/adapters/retrieval/vector_retriever.py` | B-19: `search()` 批量加载 chunk + 新增 tag 过滤支持 |
| 更新 | `src/desktop/workers/ingest_worker.py` | B-04: 新增 `progress_detailed` Signal（含 stage / elapsed_ms）|

### 关键设计决策

#### B-15: 增量索引

- `force_reindex=True` → 全量重建（清空 → 扫描 → 索引入库）
- `force_reindex=False` → 增量：比较 `existing_docs[source_path].content`，跳过未变更文件
- 内容变更时先 `delete()` 旧文档（级联删除 chunks），再插入新文档
- 增量模式从 DB 重新加载全部 chunks 重建 retriever 索引（保证一致性）

#### B-16: 中文分词

- 优先使用 `jieba`（可选依赖，pip install jieba）
- 未安装时自动降级为 bigram（连续双字切分：「架构设计」→ "架构"/"构设"/"设计"）
- 过滤纯数字 token 和单字符

#### B-17: Markdown 结构感知分块

- `_extract_md_sections()` 按 `##` 标题切分段落组
- 短段落组（≤ chunk_size）→ 独立 chunk
- 长段落组 → 内部滑窗切分，每个子块前附标题上下文
- 无标题的纯文本 → 回退传统滑窗

#### B-18: Embedding 并行

- `ThreadPoolExecutor` 默认 3 workers（Ollama 嵌入是 I/O+CPU 混合）
- 小批量（≤2）回退串行，避免线程开销大于收益
- 每线程独立创建 `ollama.Client`，避免 httpx 连接池冲突

#### B-19: VectorRetriever N+1 修复

- 原来每个 result 调用 `chunk_store.get()` → N+1 查询
- 现在 `list_by_ids(all_ids)` → 一次 SQL `WHERE id IN (...)` 查询
- 同时修复了 VectorRetriever 不支持 tag 过滤的问题
- `list_by_ids` 限流 500 防止 SQL 过长

#### B-04: 进度信号细化

- `IngestProgress` 新增 `stage: str`（scan/process/embed/store/done）和 `elapsed_ms: int`
- `_run()` 内部使用 `_p()` 闭包自动计算耗时
- `IngestWorker` 新增 `progress_detailed` Signal（向后兼容，旧 `progress_updated` 保留）

### 测试结果

```
98 passed in 1.14s ✅  零回归
```

### 代码审查发现（已入 Backlog）

| # | 问题 |
|---|------|
| B-26 | `import time` 应在模块顶层而非函数体内 |
| B-27 | 错误分支 `IngestProgress` 未传 `stage` 参数 |
| B-28 | `list_by_ids` 返回类型应标注 `list[Chunk]` |
| B-29 | 增量索引对 Vector 模式需重新嵌入全量 — 待增加 `remove_by_document()` |
| B-30 | 极短 Markdown section 应合并避免碎片化 |
| B-31 | 新功能待补充专项测试 |

<!-- 新条目追加在下方 -->
