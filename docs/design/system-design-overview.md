# 系统设计总览

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-28
> Scope：Knowledge Island Web MVP 系统级设计
> Related：docs/design/architecture-overview.md, docs/design/database-design.md, docs/requirements/functional-modules.md

## 1. 设计目标

- 以少量明确依赖实现本地 RAG 问答闭环（FastAPI + Uvicorn + SQLite）
- 支持可选的云端 LLM / Embedding，降级为本地 fallback 时不中断核心功能
- 保持 API 透明可测，前后端通过 REST JSON 解耦
- 在单进程内完成所有处理，不引入消息队列或微服务复杂度

## 2. 系统边界

- **系统输入**：用户通过浏览器交互（创建项目、导入文件、提问、评估）
- **系统输出**：知识库索引、RAG 问答结果（含来源）、掌握度评估结果
- **外部依赖**：可选 LLM API（DeepSeek / OpenAI-compatible / Ollama）、可选 Embedding API
- **非目标范围**：多用户、远程访问、网页爬取、图像识别、语音处理

## 3. 逻辑组成

| 组成部分 | 职责 | 输入 | 输出 |
|----------|------|------|------|
| HTTP Server（backend/webapp/server.py）| FastAPI app、请求路由、SSE 与静态文件服务 | HTTP 请求 | HTTP 响应 |
| API Handler（backend/webapp/api.py + backend/webapp/routes/*）| 兼容入口、领域路由、参数校验与用例编排 | 路由请求 | JSON 响应 |
| 知识导入（backend/webapp/ingestion.py 等）| 文件处理、分块、向量化 | 文件/文本/URL | 文档 + chunk + vector |
| 检索引擎（backend/webapp/search.py）| 关键词 + 向量混合检索 | 查询词 + 参数 | Ranked chunks |
| 问答引擎（backend/webapp/answers.py）| LLM 调用或本地 fallback | 查询词 + chunks | 回答 + 来源列表 |
| 存储层（backend/webapp/storage.py）| SQLite 读写与 Schema 初始化 | 数据结构 | 持久化数据 |
| Embedding（backend/webapp/embeddings.py）| 向量化（API 或本地 hash）| 文本 | float 向量 |
| LLM 客户端（backend/webapp/llm.py）| OpenAI-compatible Chat Completions | Prompt | 回答文本 |
| 模型 Profile（backend/webapp/model_profiles.py）| Profile CRUD 与 Key 引用管理 | Profile 配置 | 有效配置 |
| Agent 工具（backend/webapp/agent_tools.py）| 只读工具执行与审计 | 工具名 + 参数 | 工具结果 + 审计记录 |
| Vue 前端（frontend/ → backend/webapp/static_dist/）| 浏览器 UI 与用户交互 | 用户操作 | API 调用 + 页面状态 |

## 4. 核心流程

### 4.1 知识导入流程

1. 用户在资料库页选择导入方式（目录同步 / 文件上传 / 笔记 / URL 摘录）
2. API 接收请求，执行导入处理管线
3. 按文件类型抽取文本（TXT / Markdown / DOCX / 可选 PDF）
4. 文本分块（语义感知分块，Markdown 结构优先，短节合并保护）
5. 向量化（调用 Embedding API 或本地 hash fallback，失败不中断）
6. 增量写入 `documents` / `document_chunks` / `chunk_vectors`
7. 写入 `import_batches` / `import_batch_items` 批次记录
8. 返回导入统计（新增 / 更新 / 跳过 / 失败数）

### 4.2 RAG 问答流程

1. 用户在工作台输入问题，选择当前会话
2. 前端默认通过 `GET /api/answer/stream` 建立 EventSource；`POST /api/answer` 保留为非流式 JSON 兼容接口
3. 执行关键词检索（内置 BM25 + regex / 中文 bigram 分词）
4. 执行向量检索（SQLite 全扫描余弦相似度）
5. 合并并排序，取 top_k chunk
6. （可选）合并工具来源 chunk（若传入有效 `tool_run_id`）
7. 读取项目默认 Prompt 预设，组装 system prompt
8. 读取最近 3 轮聊天历史作为上下文
9. 调用 OpenAI-compatible 流式 LLM API，向前端推送 SSE `token` 事件；无流式模型或失败时 fallback 到本地 chunk 聚合并分段推送
10. 保存问答记录，发送 SSE `done` 事件，负载包含完整回答 + 来源列表 + 可观察性元数据

### 4.3 掌握度评估流程

1. 用户在评估页选择项目并触发评估
2. `POST /api/assessment/start` 从项目文档规则化生成概念理解、流程说明、代码定位三类评估题
3. 用户逐题回答，`POST /api/assessment/answer` 按题目 ID 读取服务端保存的参考要点，对照来源评估掌握等级
4. 记录等级与错题，下一轮优先复测错题
5. 输出差距报告

## 5. 非功能设计

### 5.1 性能

- SQLite 向量全扫描在 ≤ 5000 chunks 时检索响应 < 2 秒
- 文件导入增量模式：按文件 checksum 跳过未变更文件
- 单文件 > 1 MB 时跳过，防止阻塞导入流程
- Embedding 批量请求，减少 API 调用次数

### 5.2 安全

- API Key 只保存引用（`env:` / `saved:`），不持久化明文
- Agent 工具仅开放只读操作，工具白名单硬编码在 `agent_tools.py`
- 不支持任意命令执行或文件写入
- 服务只监听 127.0.0.1，不对外暴露网络端口

### 5.3 可维护性

- 核心逻辑按职责分文件（ingestion / search / answers / storage / embeddings / llm）
- 可选依赖（如 `pymupdf`）通过隔离入口引入，失败不影响主流程
- API 接口变更通过 `docs/design/api-spec.md` 和 `docs/design/api-changes.md` 追踪
- 61 个 API 端点原本集中在 `api.py`；B-131 已完成领域拆分蓝图，B-138 已把普通 REST 路由迁入 `backend/webapp/routes/*`，当前 `api.py` 剩余 `path ==` 分支为 0，仅保留 `dispatch()`、`answer_stream_events()` 和兼容导出入口

### 5.4 可扩展性

- Embedding 层：`RAG_EMBED_PROVIDER` 环境变量切换提供商
- LLM 层：`RAG_LLM_PROVIDER` 切换 ollama / api 模式
- 模型 Profile 支持多配置，为未来模型路由预留接口
- 向量存储层计划迁移至专用 vector store（Qdrant，B-134，P3）

## 6. 待补充设计

- Reranker 重排序接入设计（B-125，P2）
- 专用向量库迁移方案（Qdrant，B-134，P3）
