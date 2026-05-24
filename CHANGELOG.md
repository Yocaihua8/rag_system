# Changelog

## 2026-05-24

- 新增 B-111 模型 Profile 多配置设计：规划多 provider / 多模型 Profile、默认 Profile、连接测试和 API Key 引用边界；本次只写设计，不建表、不改现有模型设置行为。
- Web MVP 新增项目级 Prompt 设置第一片：设置页支持新增、编辑、删除 Prompt 预设，并可设置或清空当前项目默认预设。
- 新增 `GET/POST /api/prompt-presets`、`POST /api/prompt-presets/update`、`POST /api/prompt-presets/delete`、`POST /api/prompt-presets/default`；预设按项目隔离，不保存 API Key。
- `/api/answer` 在真实 LLM 模式下会读取当前项目默认 Prompt 预设，并在固定来源约束之后注入 `system_prompt` 与 `answer_format`；未选择预设时保持原有行为。

## 2026-05-23

- Web MVP 新增多会话聊天第一片：工作台可新建、切换、改名和删除聊天会话，`/api/answer` 支持按 `session_id` 保存消息并按当前会话读取最近上下文。
- Web MVP 新增项目级检索默认值：当前项目可保存 `top_k`、最低分、关键词/向量开关，问答和检索诊断共用这组设置。
- Web MVP 新增问答可观察性第一片：`POST /api/answer` 返回并展示本轮默认检索参数、命中来源数量、模型模式和耗时，不改变检索行为、不新增数据库表。
- Web MVP 新增回答质量反馈入口：回答下方可标记“有用 / 无用 / 来源不准 / 需要更多上下文”，通过 `POST /api/answer/feedback` 保存到本地 `answer_feedback` 表，不调用外部服务。
- Web MVP 新增 URL 摘录占位导入：保存 URL、标题和人工粘贴正文为 `url:` 虚拟来源，第一版不自动抓取网页。
- Web MVP 新增备份导出第一片：`GET /api/export/project` 只读返回当前项目、文档元数据、聊天记录和模型配置摘要；不写文件、不新增数据库表、不导出文档正文或 API Key。
- Web MVP 资料库新增文件上传导入入口：可一次选择一个或多个临时 PDF/DOCX/Markdown 等文件，复用 `POST /api/import/upload`；有当前项目时导入当前项目，没有项目时创建 `browser-upload` 项目。
- Web MVP 资料库新增剪贴板文本导入入口：复用文本笔记导入，把网页摘录、会议记录和临时材料快速写入当前项目空间。
- Web MVP 工作台新增 Agent 轻量工具面板运行入口：按 `/api/agent/tools` 元数据展示只读工具、参数 schema 和运行按钮，`search_sources` 明确使用 `query` 工具参数，运行后复用现有工具结果与运行历史。
- Web MVP 新增工具结果引用入口：成功运行 `search_sources` 后可一键把工具运行 ID 带入下一轮提问，并在页面明确显示引用的运行 ID。
- Web MVP 新增聊天记录删除能力：支持删除单条或清空当前项目聊天记录，前端删除前二次确认，只影响本地 `chat_messages`。
- Web MVP 新增检索复盘详情与删除入口：`GET /api/retrieval/reviews/detail` 返回单条复盘快照，`POST /api/retrieval/reviews/delete` 仅删除 `retrieval_reviews` 记录；前端列表提供“查看详情”和二次确认删除。
- Web MVP 新增导入预检只读接口：`GET /api/import/preview` 预估当前项目可导入文件数、跳过数和跳过原因，不写入文档。
- Web MVP 工作台新增 Agent 工具能力说明与运行详情展示：读取 `/api/agent/tools` 展示只读工具说明、参数摘要和适用场景，并在工具运行历史中通过“查看详情”读取 B-91 单条详情接口；详情读取失败只影响详情区域。
- Web MVP 扩展 Agent 只读工具白名单元数据：`GET /api/agent/tools` 为 `project_overview`、`search_sources` 返回 `label`、`parameters_schema`、`result_summary` 和 `use_cases`，保留既有 `name` / `description` 兼容字段。
- Web MVP 新增工具运行详情只读 API：`GET /api/agent/tools/runs/detail` 按 `run_id` 返回单条 `agent_tool_runs` 审计记录，不开放 shell、不写文件。
- Web MVP 资料库新增项目健康概览第一片：通过 `GET /api/projects/summary` 展示文档、Chunk、向量、聊天、工具运行、检索复盘数量和最近活动时间。
- Web MVP 新增检索健康只读提示：基于项目 summary 推导是否已有 Chunk、向量和检索复盘；未选择项目时不请求 summary，读取失败不影响项目和文档列表。
- Web MVP 新增项目健康概览只读 API：`GET /api/projects/summary` 返回当前项目文档、chunk、向量、聊天、工具运行、检索复盘数量和最近活动时间。
- 参考 Cherry Studio / AnythingLLM 补充产品化 backlog：拆分知识库控制台、模型配置、助手/Prompt、会话主题、Agent 工具、导入扩展、备份导出和可观察性任务，并按近期/中期/长期分类。
- Web MVP 资料库导入状态说明收口第一片：跳过文件说明改为“未导入”并解释常见原因，导入错误改为“读取失败”，降低跳过与失败混淆。
- Web MVP 模型设置输入提示收口第一片：API 地址、模型名称和 API Key 输入框补充非技术用户提示，使用中性示例说明、权限一致性和 Key 不回显边界。
- Web MVP 模型设置状态摘要第一片：设置页读取、保存和连接测试成功后显示模型服务、API 地址、模型名称和 API Key 来源状态，不回显 API Key 明文。
- Web MVP 模型设置错误提示细分第一片：连接测试失败时针对 API Key 未配置、模型服务连接失败、鉴权或权限错误给出更具体的恢复提示。

## 2026-05-22

- Web MVP 服务不可用错误兜底第一片：前端 API 层在本地服务断开、非 JSON 响应和无可读错误体的 HTTP 异常下返回可恢复提示，避免直接暴露浏览器解析错误。
- Web MVP 错误提示可恢复化第一片：前端状态栏保留原始错误原因，并针对项目目录不可访问、未选择文件夹、无可导入文件、未选择项目空间等高频失败补充下一步操作提示。
- Web MVP 首次使用空状态补充下一步动作提示：暂无文件、暂无来源、暂无检索结果和评估前提示会指向资料库导入或更换关键词。
- Web MVP 首次使用引导改为设置页创建项目空间、选择本机文件夹导入、提问/评估和设置页配置模型；关键异步按钮运行中会禁用并显示进行中状态。
- 统一 Web MVP 当前产品边界文档：明确 `app.py` 本地 Web 服务是默认入口，PySide6 桌面端作为 legacy 参考保留，并标注 2026-05-20 发布说明为历史快照。
- Web MVP 新增检索复盘第一片：可把一次检索诊断保存为快照，记录查询参数、命中来源、来源质量和人工备注，并在当前项目查看最近复盘。
- Web MVP 资料库页新增文本笔记导入：可把标题和正文作为 `note:` 虚拟来源写入当前项目空间，同标题再次导入会更新原记录，目录同步和浏览器文件夹导入不会误删或覆盖笔记。
- Web MVP 新增检索调试接口与工作台诊断区：可临时设置 `top_k`、最低分、关键词/向量开关，查看命中 chunk、分数、来源质量和上下文预览。
- Web MVP 问答返回 `source_quality`，用于提示来源较充分、来源偏少或没有可用来源；该字段不是事实正确性评分。
- Web MVP PDF 正文抽取接入可选 `pymupdf`；未安装解析器时继续返回明确跳过原因，不阻断其他文件入库。
- Web MVP 新增工具来源回填：用户运行 `search_sources` 后，下一轮 `/api/answer` 可通过 `tool_run_id` 合并工具命中来源，并返回 `tool_context`。
- Web MVP 新增 Agent 工具运行历史：`GET /api/agent/tools/runs` 返回当前项目审计记录，工作台展示工具名、状态、参数和错误。
- Web MVP 回答区新增“运行建议工具”按钮：来源不足时可由用户手动运行只读 `search_sources`，不会自动执行 Agent 工具。

## 2026-05-21

- Web MVP 问答在来源不足时新增 `tool_suggestion`，提示手动运行只读 `search_sources` 扩大来源检索，不自动执行工具。
- Web MVP Agent 只读工具新增 `search_sources`：复用现有 RAG 检索返回来源片段，并写入工具调用审计。
- Web MVP 新增 Agent 只读工具第一片：开放 `project_overview` 项目概览工具，写入 `agent_tool_runs` 审计记录，并拒绝 shell/未知工具。
- Web MVP 真实 LLM 问答新增最近 3 轮项目聊天历史上下文，保留来源片段约束。
- Web MVP 新增项目聊天记录：`/api/answer` 返回后保存 question/answer/mode/provider/sources，工作台可按项目恢复最近对话。
- 新增 `GET /api/chat/messages`，用于加载当前项目聊天历史。
- Web MVP 新增 OpenAI-compatible embeddings 接入：配置 `RAG_EMBED_PROVIDER=api` 后可请求 `/embeddings` 写入真实 chunk 向量，失败时回退本地 hashing。
- Docker 一键启动透传 `RAG_EMBED_*` 配置，支持容器模式使用真实 Embedding API。
- Web 搜索结果新增 `vector_provider`、`vector_model` 字段，便于确认来源使用真实 embedding 还是本地 fallback。
- Web MVP 新增本地向量检索：导入 chunk 时写入 `chunk_vectors`，搜索使用 keyword + vector 混合召回。
- Web 搜索结果新增 `retrieval`、`keyword_score`、`vector_score` 字段，便于区分关键词分和向量分。
- Web MVP 新增 RAG 分块检索第一片：导入时写入 `document_chunks`，搜索和问答按 chunk 召回来源片段。
- Web 搜索结果新增 `chunk_id` / `chunk_index` 字段，保留原有 `path`、`document_id`、`snippet`、`score` 兼容字段。
- Web MVP 新增文档处理管线第一片：目录导入和浏览器文件夹导入共用处理模块，支持 DOCX 正文抽取。
- 浏览器文件夹导入支持 DOCX/PDF 二进制 base64 上传；PDF 当前在无可选解析器时明确跳过，不阻断其他文件入库。
- Web MVP 掌握评估页新增 A+B 可视化：使用原生 SVG 雷达图展示派生能力画像，并用得分环、命中要点和待补充要点展示本次评估结果。
- Web 设置页新增模型设置：可保存 DeepSeek/OpenAI-compatible API Base、模型名和 API Key，支持连接测试且不回显 Key 明文。
- Web MVP 首页重排为简洁工作台：左侧只保留主导航，工作台、资料库、掌握评估、设置改为独立视图切换，不再把全部功能堆在首页。
- Web MVP 视觉主题从旧暗色棕金风格调整为浅灰底、白色面板、青绿色主色和靛蓝辅助状态，降低默认信息密度。
- 前端静态测试新增工作台布局、独立视图导航与主题 token 约束，防止首页退回旧双栏暗色布局或锚点跳转式导航。

## 2026-05-20

- Web MVP 新增浏览器文件夹导入：通过 `webkitdirectory` 选择本地项目文件夹，上传允许的文本文件内容并入库，解决 Docker 模式不能直接读取 Windows 路径的问题。
- 新增 Docker 双击启动/停止入口：`Start-KnowledgeIsland-Docker.bat`、`Stop-KnowledgeIsland-Docker.bat`、`scripts/docker_down.ps1` 和 `README-Docker-Quickstart.txt`。
- 新增 Docker 一键启动：`Dockerfile`、`compose.yaml` 和 `scripts/docker_up.ps1`，默认映射 `http://127.0.0.1:8765`，持久化 `runtime/docker/`，挂载 `docker-workspace/` 为容器内 `/workspace`。
- Windows 配置层补读 User/Machine 级持久环境变量，当前进程未继承 `DEEPSEEK_API_KEY` 时也能启用 Web DeepSeek。
- Web MVP 接入 OpenAI-compatible Chat Completions：配置 DeepSeek / `RAG_LLM_PROVIDER=api` 后，`/api/answer` 优先使用真实 LLM，失败时回退本地片段回答。
- Web MVP 新增掌握评估入口：从已导入文件生成最小评估题，提交回答后返回状态、得分、命中/缺失要点和建议阅读来源。
- Web 首页新增首次使用引导，覆盖创建项目空间、导入目录、提问/评估、配置 DeepSeek。
- 默认入口切换为本地 Web MVP：`app.py` 现在启动 `http://127.0.0.1:8765`。
- 新增 `webapp/`：使用 Python 标准库 HTTP 服务、SQLite、原生 HTML/CSS/JS，支持创建项目空间、导入本地文本目录、关键词问答和来源展示。
- Web MVP 会显示当前项目空间绑定的本地目录，便于确认操作范围。
- Web MVP 会标记绑定目录是否存在，目录丢失时前端提示并在发起请求前阻止导入。
- Web MVP 导入完成后会返回并展示当前项目空间的已导入文件列表。
- Web MVP 重新导入时会显示新增、更新、未变更、删除和跳过数量，并移除源目录中已删除的文本文件记录。
- Web MVP 支持点击已导入文件查看正文预览。
- Web MVP 支持从当前项目空间移除单个文档记录，不删除磁盘源文件。
- Web MVP 已导入文件列表支持按路径本地过滤，便于快速定位文件。
- Web MVP 已导入文件列表显示当前过滤结果数和总文件数。
- Web MVP 支持独立检索文件片段，并从检索结果打开文件预览。
- Web MVP 导入扫描默认跳过 `.git`、`.venv`、`node_modules`、`.claude`、`.codex`、`.agents`、`.vscode`、`.idea`、`__pycache__` 和常见构建/缓存目录。
- Web MVP 导入扫描默认跳过超过 1MB 的单个文本文件，并计入跳过数量。
- Web MVP 导入规则集中到 `webapp/import_rules.py`，便于后续调整。
- Web MVP 导入后展示跳过详情，包括被跳过文件路径和原因。
- Web MVP 导入后单独展示读取错误列表，和普通跳过详情分开。
- Web MVP 支持删除项目空间，并同步删除该项目空间下的文档记录。
- Web MVP 删除项目空间前会弹出浏览器二次确认。
- Web MVP 支持修改项目空间名称，不影响绑定目录和已导入文档。
- Web MVP 为文件列表、检索结果、来源、跳过详情和文件预览增加空状态提示。
- Web MVP 会记住最近选中的项目空间，刷新页面后自动恢复。
- 补齐 Web MVP 接口契约：`docs/design/api-spec.md` 已记录本地 `/api/*` 端点、字段和错误响应。
- 新增 `docs/release/WEB_MVP_READINESS_2026-05-20.md`，记录本地 Web MVP 可交付范围、非承诺范围和浏览器验收清单。
- 新增 `tests/test_webapp/`，覆盖目录导入、检索排序与 API 问答流程。
- 新增 `AGENT.md`，记录 Web 栈边界、文件拆分规则和验证命令。
- 旧 PySide6 桌面端代码暂时保留为 legacy，未做批量删除。

## 2026-05-18

- 发布前收口（B-53）：完成阶段10验收文档，明确本次能力边界、异常提示覆盖、体验压测结果与后续排期。
- 新增掌握评估能力差距报告能力：完成每次评估后的掌握概览、薄弱知识点、建议阅读文件、建议追问与下一步学习顺序汇总。
- `KnowledgeMasteryUseCase` 增加 `generate_ability_gap_report`，`AssessmentController` 在评估结束生成报告并在页面展示。
- `AssessmentView` 新增能力差距报告展示区域。
- 新增能力追问闭环：评估结果页支持按差距清单选择题目“继续追问”，并在题目级别触发重答流程。
- 新增错题追踪能力：`KnowledgeMasteryUseCase` 内部记录错题尝试（题目 ID、知识点、答案、状态、时间），下一轮评估支持错题优先复测。
- 补齐评估回归用例：新增优先复测边界、错题清理边界与追问按钮交互测试，覆盖 `tests/test_application/test_knowledge_mastery_usecases.py` 与 `tests/test_desktop/test_project_knowledge_ui.py`。
- 补齐 `.env` 配置写回行为：`save_setting()` 按行更新 `.env`，保留用户注释和空行，避免配置文件重排。

## 2026-05-16

- 将项目正式定位更新为“知识岛 / Knowledge Island”。
- 新增 Project、Tag、DocumentTag、Source 领域模型。
- 扩展 Document / Chunk，预留 Markdown / plain text / HTML 阅读与 heading-path chunk 字段。
- 扩展 SQLite schema，新增 projects、tags、document_tags、sources，并为 documents/chunks 追加知识岛字段。
- 将默认本地知识库目录和 AppData 名称从 CareerAssistant 调整为 KnowledgeIsland。
- 容器组装层接入 Source/Tag 存储，实现 `IngestWorkspaceUseCase` 运行时 checksum 去重回路。
- 新增 Markdown 标准化与安全 HTML 渲染，导入时生成 normalized Markdown、plain text 和受控 HTML。
- 扩展文档导入格式：支持 `pdf` / `docx` 文本提取，解析依赖缺失时跳过该文件并不阻断其他文件入库。
- 将桌面端用户可见的“工作区”文案迁移为“项目空间”，代码和数据库仍保留 Workspace 兼容层。
- 新增 Knowledge Mastery MVP 模型：`MasteryStatus / SkillArea / KnowledgePoint / Evidence / MasteryRecord`，并落库 `skill_areas / knowledge_points / evidences / mastery_records`。
- 新增轻量知识图谱 MVP：`GraphNode / GraphEdge` 持久化、图仓库端口、应用用例（含邻居检索与置信度筛选）以及 SQLite schema。
- 过度分块保护：设置 `MIN_SECTION_LENGTH=50`，合并超短 Markdown section 后再切分，减少碎片化 chunk。
