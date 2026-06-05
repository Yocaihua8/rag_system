# api.py 路由拆分蓝图

> 状态：Implemented
> Owner：RAG 团队
> Last Updated：2026-05-28
> Scope：B-131 / B-138，规划并实施 `backend/knowledge_island/api.py` 按领域拆分的迁移边界
> Related：docs/design/architecture-overview.md, docs/design/api-spec.md, docs/guides/testing.md

## 1. 目标

B-131 形成蓝图时，`backend/knowledge_island/api.py` 同时承担 61 个 `/api/*` 路由分发、参数校验、响应封装和部分跨模块 helper。B-138 已按领域完成迁移：普通 REST 路由已迁入 `backend/knowledge_island/routes/*`，`backend/knowledge_island/api.py` 当前只保留 `dispatch()`、`answer_stream_events()` 和兼容导出入口，剩余 `path ==` 路由分支为 0。外部 HTTP 契约、`backend.knowledge_island.api.dispatch()` 入口和 SSE 入口保持不变。

B-138 拆分阶段仍保留本地 Web MVP 的轻量边界：不引入 FastAPI / Flask，不新增运行时依赖，不改变 `backend.knowledge_island.server` 到 API 层的调用方式。B-139 之后运行时已切换为 FastAPI + Uvicorn，但本蓝图记录的 `backend.knowledge_island.api.dispatch()` 与 `backend/knowledge_island/routes/*` 兼容分发边界继续保留。

## 2. 非目标

- 不改变任何 URL、HTTP method、请求字段或响应字段。
- 不修改 SQLite schema，不移动 `KnowledgeStore` 职责。
- 不把业务规则下沉到前端 JS。
- 不引入自动路由框架、中间件栈或异步服务模型。
- 不在同一次拆分中重写回答生成、导入、检索或评估业务逻辑。

## 3. 当前路由分组

| 领域 | 当前端点 |
|------|----------|
| health | `GET /api/health` |
| projects | `GET /api/projects`、`POST /api/projects`、`POST /api/projects/rename`、`POST /api/projects/delete`、`GET /api/projects/summary`、`GET/POST /api/projects/retrieval-settings` |
| settings | `GET/POST /api/settings/llm`、`POST /api/settings/llm/test`、`GET/POST /api/model-profiles`、`POST /api/model-profiles/update`、`POST /api/model-profiles/delete`、`POST /api/model-profiles/default`、`POST /api/model-profiles/test`、`GET/POST /api/prompt-presets`、`POST /api/prompt-presets/update`、`POST /api/prompt-presets/delete`、`POST /api/prompt-presets/default` |
| documents | `GET /api/documents`、`GET /api/document`、`POST /api/documents/delete`、`GET/POST /api/document-collections`、`POST /api/document-collections/update`、`POST /api/document-collections/delete`、`POST /api/document-collections/items/add`、`POST /api/document-collections/items/remove` |
| imports | `GET /api/import/preview`、`POST /api/import`、`POST /api/import/upload`、`POST /api/import/note`、`POST /api/import/url`、`GET /api/import/batches`、`GET /api/import/batches/detail` |
| search | `POST /api/search`、`POST /api/search/debug`、`GET/POST /api/retrieval/reviews`、`GET /api/retrieval/reviews/detail`、`POST /api/retrieval/reviews/delete` |
| chat | `GET /api/chat/sessions`、`POST /api/chat/sessions`、`POST /api/chat/sessions/rename`、`POST /api/chat/sessions/delete`、`GET /api/chat/messages`、`POST /api/chat/messages/delete`、`POST /api/chat/messages/clear` |
| answers | `POST /api/answer`、`GET /api/answer/stream`（由 `server.py` 调用 `answer_stream_events`）、`POST /api/answer/feedback` |
| agent | `GET /api/agent/tools`、`POST /api/agent/tools/run`、`GET /api/agent/tools/runs`、`GET /api/agent/tools/runs/detail` |
| assessment | `POST /api/assessment/start`、`POST /api/assessment/answer` |
| export | `GET /api/export/project`、`POST /api/export/project/restore` |

## 4. 目标结构

```text
backend/knowledge_island/
├── api.py                  # 兼容入口：解析 raw_path，调用 route registry
├── api_support.py          # 共享请求解析、类型转换、检索设置与来源质量 helper
├── answer_api.py           # POST /api/answer 与 SSE 共用的回答上下文组装 helper
└── routes/
    ├── __init__.py         # 路由注册表与 dispatch_to_routes()
    ├── health.py           # 已迁移 GET /api/health
    ├── projects.py         # 已迁移 projects 全组
    ├── settings.py         # 已迁移 settings / model-profiles / prompt-presets 全组
    ├── documents.py        # 已迁移 documents / document-collections 全组
    ├── imports.py          # 已迁移 imports / import batches 全组
    ├── search.py           # 已迁移 search / retrieval reviews 全组
    ├── chat.py             # 已迁移 chat sessions / messages 全组
    ├── answers.py          # 已迁移 POST /api/answer 与 answer feedback
    ├── agent.py            # 已迁移 agent tools metadata / run / run history 全组
    ├── assessment.py       # 已迁移 assessment 全组
    └── export.py           # 已迁移 project export / restore 全组
```

`backend/knowledge_island/api.py` 继续暴露：

- `dispatch(store, method, raw_path, payload=None, llm_client=None) -> ApiResponse`
- `answer_stream_events(store, query, llm_client=None)`
- `test_llm_settings_with_client(client)`

路由模块只接收已经解析后的 `method/path/query/payload` 和依赖对象，不直接处理 HTTP socket，也不直接操作 SQLite 连接。

## 5. 迁移顺序

1. 新增 `api_support.py` 和 `routes/__init__.py`，但先让 `dispatch()` 仍走旧逻辑，验证无行为变化。
2. 迁移只读且低耦合路由：`health`、`projects summary`、`agent tools metadata`。
3. 迁移设置类路由：`settings`、`model-profiles`、`prompt-presets`，保留 API Key 不回显约束。
4. 迁移文档和导入路由：`documents`、`document-collections`、`imports`、`import batches`。
5. 迁移检索、聊天和回答路由：`search`、`retrieval reviews`、`chat`、`answers`；`answer_stream_events()` 必须保持 `server.py` 兼容。
6. 迁移评估和备份路由：`assessment`、`export`。
7. 删除旧 `dispatch()` 中已迁移的分支，保留 404 fallback，并运行全量 Web + legacy 回归。

执行时已按上述顺序分组迁移，每组先补拆分测试，再迁移生产代码并运行对应契约测试。

## 6. 行为不变约束

- `docs/design/api-spec.md` 中的端点、字段和错误文案是拆分验收基线。
- `tests/backend/test_api.py` 不应为拆分而改变断言语义；只允许在必要时调整 import 路径。
- 所有路由仍返回 `ApiResponse`，不直接返回 dict 或 HTTP 状态元组。
- 所有数据库访问仍经 `KnowledgeStore` 方法完成。
- `llm_client` 测试注入路径必须保持可用，特别是 `/api/answer`、`/api/answer/stream` 和 model profile 测试。
- `server.py` 不应知道具体领域路由模块，只依赖 `backend.knowledge_island.api` 的兼容入口。

## 7. 测试要求

拆分实现任务至少运行：

```powershell
.venv\Scripts\python.exe -m pytest tests\backend tests\frontend -q
.venv\Scripts\python.exe -m pytest tests\test_application tests\test_domain tests\test_adapters -q
git diff --check
```

每迁移一个领域模块，优先运行对应的 `tests/backend/test_api.py` 局部用例；全部迁移完成后再运行上面的全量命令。

## 8. 风险与回滚

| 风险 | 影响 | 控制方式 |
|------|------|----------|
| helper 迁移后不同路由错误文案不一致 | 前端错误提示和测试断言变化 | 先抽 `api_support.py`，再迁移路由；保留现有 helper 名称和返回结构 |
| `answer_stream_events()` 与 `server.py` 解耦不完整 | 流式问答中断 | `answers.py` 路由模块迁移放在后半段，单独保留流式测试 |
| 单次迁移过多端点 | 难以定位回归 | 每次只迁移一个领域模块，依赖全量测试兜底 |
| route registry 顺序错误 | 端点落到 404 fallback | registry 使用显式 `(method, path)` 匹配，不使用前缀模糊匹配 |

如果某阶段失败，回滚该领域模块的迁移即可；由于外部入口和存储层不变，不需要数据迁移回滚。

## 9. 实施状态

| 日期 | 范围 | 状态 |
|------|------|------|
| 2026-05-26 | `backend/knowledge_island/routes/__init__.py` route registry、`backend/knowledge_island/routes/health.py`、`GET /api/health` | 已落地；`backend.knowledge_island.api.dispatch()` 先尝试 registry，未匹配时继续走旧分支 |
| 2026-05-26 | `backend/knowledge_island/api_support.py`、`backend/knowledge_island/routes/projects.py`、`GET /api/projects/summary`、`backend/knowledge_island/routes/agent.py`、`GET /api/agent/tools` | 已落地；`api.py` 中对应旧分支已删除，剩余 58 个 `path ==` 分支 |
| 2026-05-26 | `GET /api/projects`、`POST /api/projects`、`POST /api/projects/rename`、`POST /api/projects/delete`、`GET/POST /api/projects/retrieval-settings` | 已落地；projects 组全部迁入 `backend/knowledge_island/routes/projects.py`，`api.py` 剩余 52 个 `path ==` 分支 |
| 2026-05-26 | `GET/POST /api/settings/llm`、`POST /api/settings/llm/test`、model profiles 全组、prompt presets 全组 | 已落地；settings 组全部迁入 `backend/knowledge_island/routes/settings.py`，`api.py` 剩余 38 个 `path ==` 分支 |
| 2026-05-26 | `GET /api/documents`、`GET /api/document`、`POST /api/documents/delete`、document collections 全组 | 已落地；documents 组全部迁入 `backend/knowledge_island/routes/documents.py`，`api.py` 剩余 29 个 `path ==` 分支 |
| 2026-05-26 | `POST /api/import`、`GET /api/import/preview`、`POST /api/import/upload`、`POST /api/import/note`、`POST /api/import/url`、`GET /api/import/batches`、`GET /api/import/batches/detail` | 已落地；imports 组全部迁入 `backend/knowledge_island/routes/imports.py`，`api.py` 剩余 22 个 `path ==` 分支 |
| 2026-05-26 | `POST /api/search`、`POST /api/search/debug`、retrieval reviews 全组 | 已落地；search 组全部迁入 `backend/knowledge_island/routes/search.py`，`api.py` 剩余 16 个 `path ==` 分支 |
| 2026-05-26 | `GET /api/agent/tools/runs`、`GET /api/agent/tools/runs/detail`、`POST /api/agent/tools/run` | 已落地；agent 组全部迁入 `backend/knowledge_island/routes/agent.py`，`api.py` 剩余 13 个 `path ==` 分支 |
| 2026-05-26 | chat sessions / messages 全组 | 已落地；chat 组全部迁入 `backend/knowledge_island/routes/chat.py`，`api.py` 剩余 6 个 `path ==` 分支 |
| 2026-05-26 | assessment 全组 | 已落地；assessment 组全部迁入 `backend/knowledge_island/routes/assessment.py`，`api.py` 剩余 4 个 `path ==` 分支 |
| 2026-05-26 | project export / restore 全组 | 已落地；export 组全部迁入 `backend/knowledge_island/routes/export.py`，`api.py` 剩余 2 个 `path ==` 分支 |
| 2026-05-26 | `POST /api/answer`、`POST /api/answer/feedback` | 已落地；answer 组迁入 `backend/knowledge_island/routes/answers.py`，回答上下文 helper 抽到 `backend/knowledge_island/answer_api.py`，`api.py` 剩余 0 个 `path ==` 分支 |

说明：`api_support.py` 只承载跨路由复用的 query 读取、数值/布尔解析、默认检索设置、来源质量和设置测试 helper；回答链路中 `POST /api/answer` 与 SSE 共用的上下文准备逻辑单独放入 `answer_api.py`，避免 `routes/answers.py` 与 `api.py` 循环依赖。
