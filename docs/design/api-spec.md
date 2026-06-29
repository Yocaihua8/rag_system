# 接口与契约说明

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-06-29
> Scope：本地 Web MVP HTTP API + legacy 进程内接口

## 1. 本地 Web MVP HTTP API

当前默认入口为本地 Web MVP：`app.py` -> `webapp.server.run_server()` -> Uvicorn/FastAPI。HTTP 服务默认监听 `http://127.0.0.1:8765`，仅用于本机浏览器访问，不作为远程多用户 API 承诺。FastAPI 自动文档可在本地 `/docs` 查看，OpenAPI 3.0 schema 可在 `/openapi.json` 查看，但正式契约仍以本文档为准。

B-140 起支持可选认证层。默认认证关闭，现有本地访问方式不变；设置 `RAG_AUTH_ENABLED=1` 后，除 `/api/health`、`/api/auth/token`、`/` 与静态资源外，所有 `/api/*`、`/docs`、`/redoc`、`/openapi.json` 都需要携带有效凭证。凭证支持 `X-API-Key: <key>` 或 `Authorization: Bearer <jwt>`。缺少凭证返回 `401 {"error":"authentication required"}`，凭证错误或过期返回 `401 {"error":"invalid credentials"}`。

B-136 起，`/openapi.json` 使用 `webapp/openapi_schema.py` 中维护的显式 Web MVP API operation 列表生成，避免 Swagger UI 只显示 `/api/{path}` 兼容分发路由。`/docs` 和 `/redoc` 保留 FastAPI 默认 UI，只读取同一个运行时 schema。当前 OpenAPI request/response schema 以通用 JSON object 表达复杂负载，字段级正式契约仍以本文档各小节为准。新增、删除或修改 API 时，需要同时更新 `webapp/openapi_schema.py` 和本文档端点速览。

端点速览：

- `GET /api/health`
- `POST /api/auth/token`
- `POST /api/admin/rebuild-index`
- `GET /api/ollama/status`
- `POST /api/ollama/pull`
- `GET /api/projects`
- `GET /api/projects/summary`
- `POST /api/projects`
- `POST /api/projects/rename`
- `POST /api/projects/delete`
- `GET /api/export/project`
- `POST /api/export/project/restore`
- `POST /api/export/result`
- `GET /api/documents`
- `GET /api/document`
- `POST /api/documents/delete`
- `GET /api/document-collections`
- `POST /api/document-collections`
- `POST /api/document-collections/update`
- `POST /api/document-collections/delete`
- `POST /api/document-collections/items/add`
- `POST /api/document-collections/items/remove`
- `GET /api/projects/retrieval-settings`
- `POST /api/projects/retrieval-settings`
- `GET /api/prompt-presets`
- `POST /api/prompt-presets`
- `POST /api/prompt-presets/update`
- `POST /api/prompt-presets/delete`
- `POST /api/prompt-presets/default`
- `GET /api/model-profiles`
- `POST /api/model-profiles`
- `POST /api/model-profiles/update`
- `POST /api/model-profiles/delete`
- `POST /api/model-profiles/default`
- `POST /api/model-profiles/test`
- `GET /api/import/preview`
- `POST /api/import`
- `POST /api/import/upload`
- `POST /api/import/note`
- `POST /api/import/url`
- `POST /api/import/notion-zip`
- `POST /api/import/obsidian-vault`
- `POST /api/import/github-repo`
- `GET /api/import/batches`
- `GET /api/import/batches/detail`
- `POST /api/search`
- `POST /api/search/debug`
- `GET /api/retrieval/reviews`
- `POST /api/retrieval/reviews`
- `GET /api/retrieval/reviews/detail`
- `POST /api/retrieval/reviews/delete`
- `POST /api/answer`
- `POST /api/answer/compare`
- `GET /api/answer/stream`
- `POST /api/answer/feedback`
- `GET /api/chat/sessions`
- `POST /api/chat/sessions`
- `POST /api/chat/sessions/rename`
- `POST /api/chat/sessions/delete`
- `GET /api/chat/messages`
- `POST /api/chat/messages/delete`
- `POST /api/chat/messages/clear`
- `GET /api/agent/tools`
- `POST /api/agent/tools/run`
- `GET /api/agent/tools/runs`
- `GET /api/agent/tools/runs/detail`
- `GET /api/settings/llm`
- `POST /api/settings/llm`
- `POST /api/settings/llm/test`
- `GET /api/assessment/library`
- `POST /api/assessment/start`
- `POST /api/assessment/answer`

### 1.1 健康检查

| 方法 | 路径 | 用途 | 成功响应 |
|------|------|------|----------|
| GET | `/api/health` | 确认本地服务可访问 | `{"status":"ok"}` |

### 1.1.1 认证 Token

| 方法 | 路径 | 请求 | 成功响应 | 错误 |
|------|------|------|----------|------|
| POST | `/api/auth/token` | Header `X-API-Key: <key>` | `{"access_token":"...","token_type":"bearer","expires_in":3600}` | `401 authentication required`、`401 invalid credentials` |

`/api/auth/token` 仅在认证启用时有实际用途。客户端提交正确 `X-API-Key` 后，服务端用 `RAG_AUTH_JWT_SECRET` 签发 HMAC-SHA256 Bearer JWT；默认有效期 3600 秒，可通过 `RAG_AUTH_JWT_TTL_SECONDS` 调整，最小 60 秒。响应不包含 `RAG_AUTH_API_KEY` 或 `RAG_AUTH_JWT_SECRET`。JWT 不写入数据库，也不提供服务端撤销列表。

### 1.1.2 管理维护接口

| 方法 | 路径 | 请求 | 成功响应 | 错误 |
|------|------|------|----------|------|
| POST | `/api/admin/rebuild-index` | 可选 `project_id` | `{"rebuilt":true,"project_ids":[...],"summary":{"projects":1,"documents":1,"chunks":1,"vectors":1}}` | `404 project not found` |

`/api/admin/rebuild-index` 是本地维护入口，供 `ops/scripts/rebuild_index.sh` 调用。请求携带 `project_id` 时仅重建该项目；未携带时重建全部项目。后端基于 SQLite `documents.content` 重新生成 `document_chunks` 与 `chunk_vectors`，启用 Qdrant local mode 时同步删除旧 point 并写入新 point；不重新扫描文件系统、不创建导入批次、不修改 SQLite schema。认证规则与其他 `/api/*` 相同：默认关闭；启用 `RAG_AUTH_ENABLED=1` 后需要 `X-API-Key` 或 Bearer JWT。

### 1.1.3 Ollama 首次运行检测

| 方法 | 路径 | 请求 | 成功响应 | 错误 |
|------|------|------|----------|------|
| GET | `/api/ollama/status` | N/A | `{"available":true,"host":"http://localhost:11434","models":["qwen2.5:7b"],"recommended_models":[...]}` | N/A；Ollama 不可达时返回 `200 {"available":false,"models":[],"error":"..."}` |
| POST | `/api/ollama/pull` | `model`，仅允许推荐模型白名单 | SSE `progress` / `done` / `error` 事件 | `400 model is required`、`400 model is not in the recommended first-run list` |

`/api/ollama/status` 只探测本机 Ollama `/api/tags`，不写数据库，不阻断 Web MVP 启动。第一版推荐模型白名单为 `qwen2.5:3b`、`qwen2.5:7b`、`deepseek-r1:8b`。`/api/ollama/pull` 通过 Ollama `/api/pull` 拉取模型，并以 `text/event-stream` 返回：

```text
event: progress
data: {"status":"pulling layer","model":"qwen2.5:3b","completed":25,"total":100,"progress":0.25}

event: done
data: {"status":"done","model":"qwen2.5:3b"}
```

### 1.2 项目空间

| 方法 | 路径 | 请求 | 成功响应 | 错误 |
|------|------|------|----------|------|
| GET | `/api/projects` | N/A | `{"projects":[...]}` | N/A |
| GET | `/api/projects/summary?project_id=...` | query `project_id` | `{"summary":...}` | `400 project_id is required`、`404 project not found` |
| GET | `/api/projects/retrieval-settings?project_id=...` | query `project_id` | `{"settings":...}` | `400 project_id is required`、`404 project not found` |
| GET | `/api/prompt-presets?project_id=...` | query `project_id` | `{"presets":[...],"default_preset_id":"...","templates":[...]}` | `400 project_id is required`、`404 project not found` |
| POST | `/api/projects` | `name`、`path` | `201 {"project":...}` | `400 path must be an existing directory` |
| POST | `/api/projects/retrieval-settings` | `project_id`、`top_k`、`min_score`、`use_keyword`、`use_vector` | `{"settings":...}` | `400 project_id is required`、`404 project not found` |
| POST | `/api/prompt-presets` | `project_id`、`name`、`description`、`system_prompt`、`answer_format` | `{"preset":...}` | `400 project_id is required`、`400 name is required`、`400 system_prompt is required`、`404 project not found` |
| POST | `/api/prompt-presets/update` | `preset_id`、`name`、`description`、`system_prompt`、`answer_format` | `{"preset":...}` | `400 preset_id is required`、`404 prompt preset not found` |
| POST | `/api/prompt-presets/delete` | `preset_id` | `{"deleted":true,"presets":[...]}` | `400 preset_id is required`、`404 prompt preset not found` |
| POST | `/api/prompt-presets/default` | `project_id`、`preset_id`（可空） | `{"default_preset_id":"..."}` | `400 project_id is required`、`404 project not found`、`404 prompt preset not found` |
| GET | `/api/model-profiles` | N/A | `{"profiles":[...],"default_profile_id":"..."}` | N/A |
| POST | `/api/model-profiles` | `name/provider/api_base/model/temperature/max_tokens/api_key_ref` | `{"profile":...}` | `400 name is required`、`400 provider is required`、`400 model is required`、`400 api_key_ref is invalid` |
| POST | `/api/model-profiles/update` | `profile_id` 和 Profile 字段 | `{"profile":...}` | `400 profile_id is required`、`404 model profile not found` |
| POST | `/api/model-profiles/delete` | `profile_id` | `{"deleted":true,"profiles":[...]}` | `400 profile_id is required`、`404 model profile not found` |
| POST | `/api/model-profiles/default` | `profile_id`（可空） | `{"default_profile_id":"..."}` | `404 model profile not found` |
| POST | `/api/model-profiles/test` | `profile_id` | `{"ok":true,"provider":"...","message":"..."}` | `400 profile_id is required`、`400 LLM provider is not configured`、`404 model profile not found` |
| POST | `/api/projects/rename` | `project_id`、`name` | `{"project":...}` | `400 name is required`、`404 project not found` |
| POST | `/api/projects/delete` | `project_id` | `{"deleted":true}` | `404 project not found` |
| GET | `/api/export/project?project_id=...` | query `project_id` | `{"export":...}` | `400 project_id is required`、`404 project not found` |
| POST | `/api/export/project/restore` | `export`、`name`（可选） | `{"project":...,"restored":{"documents":1,"chunks":1,"vectors":1,"chat_sessions":1,"chat_messages":1}}` | `400 export is required`、`400 export project is required`、`400 unsupported export version` |
| POST | `/api/export/result` | `project_id`、`message_id`、`format`、`title`（可选） | `{"export":{"format":"markdown","filename":"...","path":"...","mime_type":"...","bytes":123}}` | `400 project_id is required`、`400 message_id is required`、`400 format must be markdown or pdf`、`404 project not found`、`404 chat message not found` |

项目对象字段：

| 字段 | 说明 |
|------|------|
| `id` | 项目空间 ID |
| `name` | 项目空间名称 |
| `root_path` | 绑定的本地目录 |
| `root_exists` | 绑定目录是否仍然存在 |
| `created_at` | 创建时间 |

项目健康概览 `summary` 字段：

| 字段 | 说明 |
|------|------|
| `project_id` | 当前项目空间 ID |
| `project_name` | 当前项目空间名称 |
| `document_count` | 当前项目文档数 |
| `chunk_count` | 当前项目分块数 |
| `vector_count` | 当前项目向量记录数 |
| `chat_message_count` | 当前项目聊天消息数 |
| `agent_tool_run_count` | 当前项目 Agent 工具运行审计数 |
| `retrieval_review_count` | 当前项目检索复盘记录数 |
| `assessment_question_count` | 当前项目已生成评估题目数 |
| `assessment_result_count` | 当前项目已保存评估结果数 |
| `last_activity_at` | 当前项目最近活动时间，取项目创建、文档更新、向量更新、聊天、工具运行、检索复盘、评估题目和评估结果中的最新时间 |

`GET/POST /api/projects/retrieval-settings` 用于读取和保存项目级检索默认值。字段包括 `top_k`、`min_score`、`use_keyword`、`use_vector`，保存到当前项目记录中。`top_k` 会限制在 1-20，`min_score` 最小为 0；布尔字段按 `true/false` 保存。问答和检索诊断共用这组默认值：`/api/answer` 会直接使用当前项目默认值，`/api/search/debug` 在请求未显式传入参数时使用当前项目默认值；如果诊断请求显式传入参数，则以本次请求参数为准。该接口不创建检索复盘、不执行检索、不调用模型。

`/api/prompt-presets` 用于管理当前项目空间的 Prompt 预设。预设字段包括 `id/project_id/name/description/system_prompt/answer_format/created_at/updated_at`；默认预设 ID 保存到当前项目的 `default_prompt_preset_id`。第一片内置 `项目问答`、`代码解释`、`学习复盘` 三个本地模板，模板只用于前端复制，不会自动写入数据库。Prompt 预设只影响真实 LLM 的回答风格和结构，不改变检索参数、不自动运行工具、不保存 API Key 或模型凭证。设置默认预设时会校验预设必须属于当前项目，跨项目 preset 返回 `404 prompt preset not found`。`system_prompt` 和 `answer_format` 会被放在固定来源约束之后；固定约束仍要求只基于来源片段回答、资料不足时说明缺口，用户 Prompt 不能覆盖该边界。

`/api/model-profiles` 用于管理本地 Web MVP 的模型 Profile。Profile 字段包括 `id/name/provider/api_base/model/temperature/max_tokens/api_key_ref/has_api_key/api_key_source/is_default/created_at/updated_at`。`provider` 允许 `api` 或 `ollama`；Ollama Profile 不需要 API Key。`api_key_ref` 只允许为空、`env:RAG_LLM_API_KEY`、`env:DEEPSEEK_API_KEY` 或 `saved:RAG_LLM_API_KEY`，不保存 API Key 明文、不回显掩码 Key，也不把用户输入的 Key 值写入 SQLite。设置默认 Profile 后，`/api/answer` 会优先使用该 Profile 的非敏感配置和可解析 Key；没有默认 Profile 时继续使用现有 `load_settings()` 单配置行为。测试 Profile 只测试指定配置，不覆盖 `.env`，失败时不自动切换默认 Profile。

项目备份导出 `/api/export/project` 为只读接口，不新增数据库表、不写文件、不读取磁盘源文件。成功响应结构：

```json
{
  "export": {
    "version": 1,
    "project": {},
    "documents": [
      {
        "id": "document-id",
        "relative_path": "README.md",
        "source_path": "E:/Code/project/README.md",
        "checksum": "sha256",
        "updated_at": "2026-05-25T00:00:00+00:00",
        "content": "# 文档正文",
        "chunks": [
          {
            "id": "chunk-id",
            "chunk_index": 0,
            "content": "# 文档正文",
            "token_count": 12,
            "created_at": "2026-05-25T00:00:00+00:00",
            "vector": {
              "values": {"1": 0.5},
              "provider": "local",
              "model": "hashing-96",
              "updated_at": "2026-05-25T00:00:00+00:00"
            }
          }
        ]
      }
    ],
    "chat_sessions": [],
    "chat_messages": [],
    "settings_summary": {
      "provider": "api",
      "api_base": "https://api.deepseek.com/v1",
      "model": "deepseek-chat",
      "key_configured": true
    }
  }
}
```

`documents` 导出当前 SQLite 中的文档正文 `content`、`document_chunks` 快照和 `chunk_vectors` 快照，恢复后无需重新导入即可执行检索和问答。该接口只读取本地数据库，不重新读取原磁盘文件；因此导出内容以当前入库状态为准。启用 Qdrant 时，导出仍以 SQLite `chunk_vectors` 兼容副本为准，不直接读取 Qdrant 本地索引。`chat_sessions` 和 `chat_messages` 导出本地会话与聊天记录快照。`settings_summary` 只能包含 `provider`、`api_base`、`model`、`key_configured` 这类摘要；不导出 API Key 明文、掩码或 `api_key_source`。

项目备份恢复 `/api/export/project/restore` 用于把同版本 `version=1` 备份恢复为新项目空间。恢复项目的 `root_path` 写为 `browser-upload:<项目名>`，不会覆盖原项目，也不会读取或写入原磁盘路径。恢复会写入文档正文、chunk 和 vector，并把聊天来源中的 `document_id` / `chunk_id` 映射到恢复后的新记录 ID；启用 Qdrant 时，恢复写入的 chunk vector 会同步 upsert 到 Qdrant。本接口响应中的 `restored` 返回 `documents`、`chunks`、`vectors`、`chat_sessions` 和 `chat_messages` 数量。恢复接口不恢复 API Key、不恢复 `settings_summary` 为真实配置，也不把 `key_configured` 当成凭证来源。

结果导出 `POST /api/export/result` 用于把当前项目内已生成的单条 `chat_messages` 问答结果写入本地输出目录，默认目录为 `data/outputs/`，可通过 `KI_OUTPUT_DIR` 或 `RAG_OUTPUT_DIR` 覆盖。请求中的 `format` 只允许 `markdown` 或 `pdf`；`message_id` 必须存在且属于请求的 `project_id`，跨项目消息按 `404 chat message not found` 处理。Markdown 文件包含标题、项目名、消息 ID、导出时间、问题、回答和来源列表；PDF 文件使用同一内容生成轻量文本 PDF，不新增大型 PDF 渲染依赖。接口只写导出文件，不新增数据库表、不修改聊天记录、不读取磁盘源文件，也不返回文件内容。

成功响应示例：

```json
{
  "export": {
    "format": "markdown",
    "filename": "result-20260629-120000-abcd1234.md",
    "path": "data/outputs/result-20260629-120000-abcd1234.md",
    "mime_type": "text/markdown; charset=utf-8",
    "bytes": 1024
  }
}
```

### 1.3 文档与导入

| 方法 | 路径 | 请求 | 成功响应 | 错误 |
|------|------|------|----------|------|
| GET | `/api/documents?project_id=...` | query `project_id` | `{"documents":[...]}` | `400 project_id is required` |
| GET | `/api/documents?project_id=...&collection_id=...` | query `collection_id` 可为空；`collection_id=unassigned` 表示未分组 | `{"documents":[...]}` | `400 project_id is required`、`404 document collection not found` |
| GET | `/api/document?document_id=...` | query `document_id` | `{"document":...}` | `400 document_id is required`、`404 document not found` |
| POST | `/api/documents/delete` | `document_id` | `{"deleted":true,"documents":[...]}` | `404 document not found` |
| GET | `/api/document-collections?project_id=...` | query `project_id` | `{"collections":[...]}` | `400 project_id is required`、`404 project not found` |
| POST | `/api/document-collections` | `project_id`、`name`、`description`、`color` | `{"collection":...}` | `400 project_id is required`、`400 name is required`、`404 project not found` |
| POST | `/api/document-collections/update` | `collection_id`、`name`、`description`、`color` | `{"collection":...}` | `400 collection_id is required`、`400 name is required`、`404 document collection not found` |
| POST | `/api/document-collections/delete` | `collection_id` | `{"deleted":true,"collections":[...]}` | `400 collection_id is required`、`404 document collection not found` |
| POST | `/api/document-collections/items/add` | `collection_id`、`document_ids` | `{"collection":...}` | `400 collection_id is required`、`400 document_ids is required`、`404 document collection not found`、`404 document not found` |
| POST | `/api/document-collections/items/remove` | `collection_id`、`document_ids` | `{"collection":...}` | `400 collection_id is required`、`400 document_ids is required`、`404 document collection not found` |
| GET | `/api/import/preview?project_id=...` | query `project_id` | `{"preview":...}` | `400 project_id is required`、`404 project not found`、`400 project root path does not exist` |
| POST | `/api/import` | `project_id` | `{"result":...,"batch":...,"documents":[...]}` | `404 project not found`、`400 project root path does not exist` |
| POST | `/api/import/upload` | `project_id`（可选）、`project_name`（新建时使用）、`source_type`（可选，`browser_folder_upload / file_upload`）、`files:[{relative_path,content}]` 或 `files:[{relative_path,content_base64,size}]` | `{"project":...,"result":...,"batch":...,"documents":[...]}` | `400 files is required`、`404 project not found` |
| POST | `/api/import/note` | `project_id`、`title`、`content` | `{"result":...,"batch":...,"document":...,"documents":[...]}` | `400 title is required`、`400 content is required`、`400 content is too large`、`404 project not found` |
| POST | `/api/import/url` | `project_id`、`url`、`title`、`content` | `{"result":...,"batch":...,"document":...,"documents":[...]}` | `400 url is required`、`400 url must start with http:// or https://`、`400 title is required`、`400 content is required`、`404 project not found` |
| POST | `/api/import/notion-zip` | `project_id`、`filename`、`content_base64` | `{"result":...,"batch":...,"documents":[...]}` | `400 filename is required`、`400 filename must end with .zip`、`400 content_base64 is required`、`400 content_base64 is invalid`、`400 invalid notion zip`、`404 project not found` |
| POST | `/api/import/obsidian-vault` | `project_id`、`vault_path` | `{"result":...,"batch":...,"documents":[...]}` | `400 vault_path is required`、`400 obsidian vault path does not exist`、`404 project not found` |
| POST | `/api/import/github-repo` | `repo_url`、`branch`（可选）、`project_name`（可选） | `{"project":...,"result":...,"batch":...,"documents":[...]}` | `400 repo_url is required`、`400 github repository url is invalid`、`400 git executable not found`、`400 git clone failed: ...`、`400 git clone timed out` |
| GET | `/api/import/batches?project_id=...` | query `project_id` | `{"batches":[...]}` | `400 project_id is required`、`404 project not found` |
| GET | `/api/import/batches/detail?batch_id=...` | query `batch_id` | `{"batch":...,"items":[...]}` | `400 batch_id is required`、`404 import batch not found` |

`/api/import/preview` 用于导入前预检本地项目目录，只读返回预计可导入文件数、跳过数和跳过原因；不会写入 `documents`、不会生成 chunk/vector，也不会删除已有记录。预检复用当前目录忽略规则、支持后缀规则和 `note:` 虚拟来源保护。

`/api/import/upload` 用于浏览器文件夹导入和文件上传导入。浏览器文件夹导入通过 `webkitdirectory` 获取用户授权文件夹内的文件和相对路径；文件上传导入使用普通 `multiple` 文件选择，单文件没有 `webkitRelativePath` 时以前端文件名作为 `relative_path`。两种入口都会把允许的文本内容或 DOCX/PDF 二进制 base64 上传给本地服务处理；后端不会尝试读取 Windows 原始路径。未传 `project_id` 时，接口会创建 `browser-upload:<project_name>` 项目空间；该类项目的 `root_exists` 固定为 `true`。前端文件上传入口有当前项目空间时会传入 `project_id`，把文件导入当前项目；没有项目空间时创建 `browser-upload` 项目。

`/api/import/note` 用于导入资料库页手写文本笔记。后端按 `title` 生成稳定虚拟来源 `note:<project_id>/<hash>`，文档相对路径写为 `notes/<safe-title>-<hash>.txt`；`safe-title` 会清洗特殊字符并截断长度。同一项目空间内相同标题会更新原笔记，不创建重复文档。目录同步和浏览器文件夹导入只清理真实文件来源，不会删除 `note:` 或 `url:` 虚拟来源；如果真实文件或上传文件撞到已存在笔记的相对路径，会跳过该真实文件并返回 `reserved note path`。

`/api/import/url` 用于保存 URL 摘录占位来源。第一版只保存用户提交的 `url/title/content`，不会自动抓取网页、不会联网，也不会解析远端页面。后端把 URL 和标题写入文档正文，来源路径标记为 `url:` 虚拟来源，文档相对路径写为 `urls/<url-hash>.txt`；同一 URL 再次导入会更新原记录。目录同步和浏览器文件夹导入会保留 `url:` 虚拟来源，不会把它当成缺失的真实文件删除。

`/api/import/notion-zip` 用于导入 Notion 导出的 Markdown zip 包。后端只读取 zip 内 Markdown / 文本类文件，跳过附件、图片、二进制、不支持后缀、过大文件和非法相对路径；入库文档 `relative_path` 统一加 `notion/` 前缀，`source_path` 标记为 `notion-zip:<filename>#<relative_path>` 虚拟来源。该接口不调用 Notion API、不联网、不保存第三方 token，也不会做删除清理。

`/api/import/obsidian-vault` 用于导入本机 Obsidian vault 目录。后端递归读取 Markdown / 文本类文件，跳过 `.obsidian`、`.trash` 以及通用忽略目录；入库文档 `relative_path` 统一加 `obsidian/` 前缀，`source_path` 标记为 `obsidian-vault:<vault-root>#<relative_path>` 虚拟来源。第一版不会解析 wikilink/backlink，也不会做删除清理。

`/api/import/github-repo` 用于通过本机 `git clone --depth 1` 导入 GitHub 仓库。后端只接受 `https://github.com/<owner>/<repo>`、`https://github.com/<owner>/<repo>.git` 和 `git@github.com:<owner>/<repo>.git` 形式的 GitHub 仓库 URL；请求中不允许携带用户名、密码或 token。clone 目录位于 Web MVP 受控运行时目录 `runtime/webapp/github-repos/` 下，接口会创建新的项目空间并复用目录导入规则读取 Markdown、代码和其他已支持文件类型，自动跳过 `.git`、`node_modules`、`.venv`、`dist` 等忽略目录。第一版不接入 GitHub API、不保存凭据、不提供增量同步或定时拉取；私有仓库只在本机 git 已具备访问权限时可由底层 clone 命令处理。

导入批次历史由 `import_batches` 和 `import_batch_items` 保存。`source_type` 支持 `directory_sync / browser_folder_upload / file_upload / text_note / url_excerpt / notion_zip / obsidian_vault / github_repo`；`status` 支持 `success / partial / failed`。当前第一片在成功完成的导入响应中追加 `batch` 摘要，并支持按项目读取最近批次、按 `batch_id` 读取详情。批次字段包含 `id/project_id/source_type/status/started_at/finished_at/summary/message/created_at`；批次 `summary` 包含 `imported/created/updated/unchanged/deleted/skipped/errors` 计数，详情 `items` 展示 `kind/relative_path/document_id/reason`，前端只展示跳过和读取失败明细。导入批次历史不会保存文档正文、上传原始内容、chunk/vector、API Key 或模型配置；第一片不做回滚、不删除批次、不重试历史批次。`/api/import/preview` 是只读预检，不创建导入批次。

B-08 后，`/api/import*` 响应契约保持同步兼容，不新增 job 状态接口或持久化队列表。FastAPI `/api/*` 兼容分发在线程池中执行同步业务逻辑；写入型导入入口在进程内按 `project_id` 串行，同一项目的并发导入请求会等待前一个导入完成，不同项目可重叠执行。

Web MVP 当前支持文本类文件和 DOCX 正文抽取。安装可选 `pymupdf` 后可抽取 PDF 正文；没有可选解析器时返回跳过原因 `pdf extraction requires optional parser`，不会阻断其他文件入库。PDF 未提取到文本时返回 `no extractable text`，常见于扫描件或图片型 PDF。

导入结果字段：

| 字段 | 说明 |
|------|------|
| `imported` | 本轮成功入库或确认的文件数 |
| `created` | 新增文件数 |
| `updated` | 内容变更后更新的文件数 |
| `unchanged` | 内容未变更文件数 |
| `deleted` | 源目录已删除而被清理的记录数 |
| `skipped` | 跳过文件数，含读取失败 |
| `skipped_details` | 普通跳过明细，例如超过 1MB |
| `errors` | 读取失败等错误明细 |

文档列表响应默认不返回正文内容；只有 `/api/document` 的单文档预览响应包含 `content`。

文档集合用于资料库页轻量分组。集合字段包括 `id/project_id/name/description/color/document_count/created_at/updated_at`；集合只保存元数据和文档关联，不复制文档正文、chunk 或 vector。`GET /api/documents` 可通过 `collection_id` 过滤指定集合，也可通过 `collection_id=unassigned` 返回当前项目未加入任何集合的文档。删除集合不删除文档，只删除 `document_collection_items` 关联。跨项目加入集合必须拒绝：如果文档不存在或不属于集合所在项目，接口返回 `404 document not found`，避免泄露其他项目文档。

### 1.4 检索与问答

| 方法 | 路径 | 请求 | 成功响应 |
|------|------|------|----------|
| POST | `/api/search` | `project_id`、`query` | `{"hits":[...]}` |
| POST | `/api/search/debug` | `project_id`、`query`、`top_k`、`min_score`、`use_keyword`、`use_vector` | `{"hits":[...],"debug":...}` |
| GET | `/api/retrieval/reviews?project_id=...` | query `project_id` | `{"reviews":[...]}` |
| POST | `/api/retrieval/reviews` | `project_id`、`query`、`note`、`top_k`、`min_score`、`use_keyword`、`use_vector` | `{"review":...}` |
| GET | `/api/retrieval/reviews/detail?review_id=...` | query `review_id` | `{"review":...}` | `400 review_id is required`、`404 retrieval review not found` |
| POST | `/api/retrieval/reviews/delete` | `review_id` | `{"deleted":true,"reviews":[...]}` | `400 review_id is required`、`404 retrieval review not found` |
| POST | `/api/answer` | `project_id`、`question`、`session_id`（可选）、`tool_run_id`（可选）、`parent_message_id`（可选） | `{"answer":"...","sources":[...],"mode":"local|api|fallback","provider":"local|deepseek|api|ollama","source_quality":...,"pipeline_trace":...,"observability":...,"message":...,"tool_suggestion":...,"tool_context":...}` |
| POST | `/api/answer/compare` | `project_id`、`question`、`profile_ids`（必须 2 个不同 Model Profile ID）、`tool_run_id`（可选）、`parent_message_id`（可选） | `{"question":"...","results":[...],"sources":[...],"source_quality":...,"pipeline_trace":...,"observability":{"retrieval":...,"model_comparison":...},"tool_context":...}` | `400 profile_ids must contain exactly 2 model profile ids`、`400 profile_ids must contain 2 different model profile ids`、`404 model profile not found` |
| GET | `/api/answer/stream?project_id=...&question=...` | query `project_id`、`question`、`session_id`（可选）、`tool_run_id`（可选）、`parent_message_id`（可选） | SSE `token` / `done` / `answer_error` 事件；`done` 负载与 `/api/answer` 成功响应一致 |
| POST | `/api/answer/feedback` | `project_id`、`message_id`、`rating`、`note`（可选） | `{"feedback":...}` | `400 project_id is required`、`400 message_id is required`、`400 rating is invalid`、`404 project not found`、`404 chat message not found` |
| GET | `/api/chat/sessions?project_id=...` | query `project_id` | `{"sessions":[...]}` | `400 project_id is required`、`404 project not found` |
| POST | `/api/chat/sessions` | `project_id`、`title`（可选） | `{"session":...}` | `400 project_id is required`、`404 project not found` |
| POST | `/api/chat/sessions/rename` | `session_id`、`title` | `{"session":...}` | `400 session_id is required`、`400 title is required`、`404 chat session not found` |
| POST | `/api/chat/sessions/delete` | `session_id` | `{"deleted":true,"sessions":[...]}` | `400 session_id is required`、`404 chat session not found` |
| GET | `/api/chat/messages?project_id=...` | query `project_id` | `{"messages":[...]}` |
| POST | `/api/chat/messages/delete` | `message_id` | `{"deleted":true,"messages":[...]}` | `400 message_id is required`、`404 chat message not found` |
| POST | `/api/chat/messages/clear` | `project_id` | `{"deleted":数量,"messages":[]}` | `400 project_id is required`、`404 project not found` |

当前 Web MVP 导入时会把文档拆成 SQLite `document_chunks`，并为每个 chunk 写入 `chunk_vectors`。配置 `RAG_EMBED_PROVIDER=api` 且存在 `RAG_EMBED_API_KEY` 时，向 OpenAI-compatible `/embeddings` 写入真实 embedding；未配置、请求失败或服务不支持时回退本地 hashing 向量。配置 `RAG_VECTOR_STORE_PROVIDER=qdrant` 且 `qdrant-client` 可用时，导入、更新、删除和备份恢复会把 chunk vector 同步到 Qdrant local collection；检索时 vector 候选由 Qdrant 返回，避免查询时全量遍历 SQLite `chunk_vectors`。未启用 Qdrant、Qdrant 依赖缺失或查询失败时，搜索回退到 SQLite `chunk_vectors` + cosine similarity。检索按 chunk 片段做 BM25 keyword + vector 混合召回，不再把整篇文档作为最小召回单位；`keyword_score` 表示内置 BM25 关键词分数，不再是 regex 词频累加。B-126 起，如果当前数据库已存在 legacy `graph_nodes` / `graph_edges` 表，检索会从已有 keyword 命中或向量候选对应的 graph node 出发，读取一跳相邻节点并把可映射的 `source_ref` chunk 并入候选池；表不存在、没有 seed 节点或无法映射来源时保持原有检索结果。`hits` / `sources` 中每条结果包含 `path`、`document_id`、`snippet`、`score`、`retrieval`、`keyword_score`、`vector_score`、`vector_provider`、`vector_model`、`rerank_score`、`graph_score`、`graph_depth`，命中 chunk 时还包含 `chunk_id`、`chunk_index`。`vector_provider` / `vector_model` 表示 embedding 来源，不表示 Qdrant 本身。`graph_score` 当前取 graph edge `confidence`，非图谱候选为 `0.0`；`graph_depth` 当前只支持一跳，图谱候选为 `1`，非图谱候选为 `null`。`retrieval` 为 `graph` 表示该来源仅由图谱扩展召回；同一 chunk 同时有 keyword/vector 和图谱分数时会追加 `+graph`。`rerank_score` 仅在设置 `RAG_RERANKER_ENABLED=true` 且本地 `sentence-transformers` 可用时写入 Cross-Encoder 精排分；默认关闭或依赖缺失时为 `null`，并保持原 BM25 + 向量排序；启用 reranker 时会接收 graph 扩展后的候选池。`/api/search/debug` 用于本地调试检索质量，可临时调整 `top_k`、`min_score`、`use_keyword` 和 `use_vector`，并返回文档数、分块数、向量可用状态、来源质量和上下文预览；这些参数不持久化。问答在配置 `RAG_LLM_PROVIDER=ollama` 且本地 Ollama 可达时，优先请求 Ollama `/api/chat`；配置 `RAG_LLM_PROVIDER=api` 且存在 `RAG_LLM_API_KEY` / DeepSeek Key 别名时，优先请求 OpenAI-compatible Chat Completions；`/api/answer/stream` 会使用上游流式响应并以 `text/event-stream` 推送 `token` 事件，完成时发送 `done` 事件和完整回答负载。未配置流式能力、未配置模型、Ollama 不可达或请求失败时仍会回退到本地命中片段组合回答，并通过同一 SSE 通道分段渲染。无命中时不伪造来源，并返回可选 `tool_suggestion`，建议用户手动运行只读 `search_sources` 扩大来源检索；该建议不自动执行工具，只有用户点击前端按钮后才会通过 `/api/agent/tools/run` 写入 `agent_tool_runs`。每次 `/api/answer` 或 `/api/answer/stream` 成功完成时，会把本轮 `question/answer/mode/provider/warning/sources/session_id/parent_message_id/branch_index` 写入 `chat_messages`；Vue B-142 工作台通过 `/api/chat/messages` 加载当前会话消息，通过 `/api/chat/sessions*` 管理当前项目会话。真实 LLM 请求会把当前聊天会话最近 3 轮 `question/answer` 作为“最近对话”写入 prompt；没有 `session_id` 时使用默认会话，也就是旧的 `session_id IS NULL` 消息。如果当前项目配置了默认 Prompt 预设，真实 LLM prompt 会在固定来源约束之后追加该预设的 `system_prompt`，并把 `answer_format` 作为回答格式要求；未选择预设时保持原有 prompt 行为。这是局部上下文增强，不是完整 Agent 记忆，也不会绕过来源片段约束。

`/api/answer/compare` 用于在同一问题、同一检索结果、同一 Prompt 预设和同一工具来源上下文下，对 2 个不同 Model Profile 生成并排回答。`profile_ids` 必须是两个不同且已存在的 Profile ID；响应 `results` 数组保留请求顺序，每项包含 `profile_id`、`profile_name`、`profile_provider`、`model`、`answer`、`mode`、`provider`，模型失败回退时包含 `warning`。该接口不写入 `chat_messages`，不返回 `message` 字段，也不触发回答反馈；它只用于临时比较模型回答质量。`sources`、`source_quality`、`pipeline_trace` 和 `observability.retrieval` 是两次回答共用的同一份检索上下文；`observability.model_comparison` 返回 `profile_count`、`profile_ids` 和 `models`。接口不会回显 API Key、掩码 Key 或可解析 Key 来源。

`chat_sessions` 用于当前项目内的多会话聊天。没有 `session_id` 的旧消息继续归入“默认会话”。`GET /api/chat/messages` 不传 `session_id` 时读取默认会话消息；传入 `session_id` 时会校验会话必须属于当前项目，否则返回 `404 chat session not found`。删除会话会删除该会话下的聊天消息，并通过 `message_id` 外键清理对应回答反馈；不会删除文档、检索复盘、工具运行或项目级检索设置。

`parent_message_id` 用于 B-128 历史消息编辑重发。客户端传入该字段时，服务端会校验父消息必须属于同一 `project_id` 和同一 `session_id`；不存在、跨项目或跨会话时返回 `404 parent chat message not found`，且不写入新消息。校验通过后，新消息的 `parent_message_id` 指向被编辑消息，`branch_index` 为同一父消息下的递增序号；未传 `parent_message_id` 的普通问答保持 `parent_message_id=""`、`branch_index=0`。`message.to_dict()` 响应会返回 `parent_message_id` 和 `branch_index`。

`observability` 用于展示本轮问答的可观察性元数据，不持久化为新的数据库表。当前 `/api/answer` 使用项目级检索默认值，未保存时默认为 `top_k=5`、`min_score=0.0`、`use_keyword=true`、`use_vector=true`。响应结构包含 `retrieval.top_k`、`retrieval.min_score`、`retrieval.use_keyword`、`retrieval.use_vector`、`retrieval.hit_count`、`model.mode`、`model.provider` 和 `elapsed_ms`。`retrieval.hit_count` 统计本轮回答最终可用来源数量，包含显式 `tool_run_id` 带入且通过校验的来源片段；前端 `sources` 仍只展示前 5 条。`model.mode` 与顶层 `mode` 一致，`model.provider` 与顶层 `provider` 一致。`elapsed_ms` 覆盖本轮问答处理耗时，用于本地调试，不是性能 SLA。

`pipeline_trace` 用于暴露本轮检索管线的轻量状态，不持久化为新的数据库表。当前字段为 `reranker_used`，当最终可用来源中至少一条包含 `rerank_score` 时为 `true`，否则为 `false`。

聊天记录删除接口只影响本地 `chat_messages` 表。删除单条时按 `message_id` 定位原消息并返回同项目剩余消息；清空时只删除当前 `project_id` 下的消息，不删除文档、检索复盘、工具运行记录或模型设置。前端必须在删除单条或清空前使用二次确认。

`/api/answer/feedback` 用于保存用户对某条回答的本地质量反馈，不调用外部服务，也不自动调整检索或模型参数。`rating` 只允许以下枚举：

| rating | 前端文案 | 说明 |
|--------|----------|------|
| `useful` | 有用 | 回答对当前问题有帮助 |
| `not_useful` | 无用 | 回答没有解决问题 |
| `source_wrong` | 来源不准 | 回答引用或依赖的来源不准确 |
| `need_more_context` | 需要更多上下文 | 回答需要更多项目资料或上下文 |

反馈必须绑定已存在的 `chat_messages.id`，且消息必须属于当前项目；跨项目消息按 `404 chat message not found` 处理，避免泄露其他项目记录是否存在。

`/api/retrieval/reviews` 用于保存一次检索复盘快照。后端会按提交的 `query/top_k/min_score/use_keyword/use_vector` 重新执行检索，不信任前端传回的命中结果；保存内容包括 `parameters`、`hits`、`source_quality`、`note` 和 `created_at`。`GET /api/retrieval/reviews/detail` 只读返回单条复盘完整快照，便于前端展示查询参数、命中来源和人工备注；详情读取失败只影响详情区域，不阻塞列表。`POST /api/retrieval/reviews/delete` 只影响 `retrieval_reviews`，不会删除文档、聊天、工具运行记录，也不会自动调整检索参数；删除成功至少包含 `{"deleted":true}`，当前实现还会附带当前项目剩余 `reviews`。换句话说，删除只影响 retrieval_reviews。该接口用于人工复盘检索质量，不自动调整检索权重、不自动执行 Agent 工具，也不是评测集或 Reranker。

`source_quality` 是来源充分度提示，不是事实正确性评分：

| 字段 | 说明 |
|------|------|
| `level` | `good / weak / none` |
| `label` | 用户可读标签，例如“来源较充分” |
| `reason` | 为什么给出该提示 |
| `hit_count` | 本轮可用来源数量 |
| `max_score` | 本轮最高来源分数 |

`tool_suggestion` 字段仅在来源不足时返回，结构如下：

```json
{
  "tool": "search_sources",
  "arguments": {"query": "用户原问题"},
  "reason": "当前回答没有可用来源，可先用只读来源检索工具扩大召回。"
}
```

`tool_run_id` 用于显式回填用户刚运行过的 `search_sources` 来源结果。后端只接受同项目、成功状态、工具名为 `search_sources` 的运行记录；通过校验后会把该工具结果里的来源片段合并入本轮回答来源，并返回：

```json
{
  "tool_context": {
    "tool_run_id": "工具运行 ID",
    "query": "工具检索词",
    "hit_count": 1
  }
}
```

这不是自动 Agent 编排；前端只有在用户运行只读来源检索工具后，才会把该工具运行 ID 作为下一轮问答上下文发送。

聊天消息字段：

| 字段 | 说明 |
|------|------|
| `id` | 消息 ID |
| `project_id` | 所属项目空间 |
| `question` | 用户问题 |
| `answer` | 本轮回答文本 |
| `mode` | `local / api / fallback` |
| `provider` | `local / deepseek / api / ollama` 等来源 |
| `warning` | 模型失败回退等警告，可能为空 |
| `sources` | 本轮回答使用的来源片段数组 |
| `created_at` | 记录时间 |

### 1.5 Agent 只读工具

| 方法 | 路径 | 请求 | 成功响应 | 错误 |
|------|------|------|----------|------|
| GET | `/api/agent/tools` | N/A | `{"tools":[...]}` | N/A |
| POST | `/api/agent/tools/run` | `project_id`、`tool`、`arguments` | `{"result":...,"run":...}` | `404 project not found`、`400 unknown or disabled tool` |
| GET | `/api/agent/tools/runs?project_id=...` | query `project_id` | `{"runs":[...]}` | `400 project_id is required`、`404 project not found` |
| GET | `/api/agent/tools/runs/detail?run_id=...` | query `run_id` | `{"run":...}` | `400 run_id is required`、`404 tool run not found` |

当前只开放只读白名单工具，不开放 shell、任意命令执行、任意文件写入或外部自动化。第一片工具：

| 工具 | 类型 | 说明 |
|------|------|------|
| `project_overview` | 只读 | 返回当前项目名称、根目录、文档数、分块数、向量数和聊天记录数 |
| `search_sources` | 只读 | 使用现有 RAG 检索返回当前项目来源片段，参数为 `{"query":"..."}`，最多返回 5 条命中 |

`GET /api/agent/tools` 返回只读工具白名单元数据。为兼容既有前端，工具对象继续保留 `name`、`description`、`title`、`read_only` 和旧版 `arguments` 字段；B-96 起新增以下字段，不新增数据库表：

| 字段 | 说明 |
|------|------|
| `name` | 工具唯一名称，例如 `project_overview`、`search_sources` |
| `label` | 用户可读工具名称，例如“项目概览”“检索来源” |
| `description` | 工具能力说明，供前端列表和后续工具面板展示 |
| `parameters_schema` | 参数 JSON Schema，包含 `type`、`properties`、`required` 和 `additionalProperties` |
| `result_summary` | 工具成功运行后会返回哪些摘要信息 |
| `use_cases` | 适用场景列表，仅描述当前只读白名单工具的使用边界 |

`project_overview` 的 `parameters_schema` 为无参数对象，`properties` 为空且 `additionalProperties` 为 `false`。`search_sources` 的 `parameters_schema.required` 为 `["query"]`，`query` 是非空字符串，用于检索当前项目资料。

每次工具运行都会写入 `agent_tool_runs` 审计记录，包括工具名、参数、结果、状态、错误和时间。未知工具也会在项目存在时记录失败审计。工具运行历史通过 `GET /api/agent/tools/runs` 只读返回，按最近运行优先排序，前端用于展示当前项目工具审计列表。单条工具运行详情通过 `GET /api/agent/tools/runs/detail?run_id=...` 只读返回，响应为 `{"run":...}`，字段沿用工具运行记录字段，不开放 shell、不写文件、不新增数据库表。

工具运行记录字段：

| 字段 | 说明 |
|------|------|
| `id` | 工具运行 ID |
| `project_id` | 所属项目空间 |
| `tool_name` | 工具名 |
| `arguments` | 本次运行参数 |
| `result` | 本次运行结果，失败时可为空 |
| `status` | `success / error` |
| `error` | 失败原因，可能为空 |
| `created_at` | 记录时间 |

### 1.6 模型设置

| 方法 | 路径 | 请求 | 成功响应 | 错误 |
|------|------|------|----------|------|
| GET | `/api/settings/llm` | N/A | `{"settings":{"provider":"api|ollama","api_base":"...","model":"...","has_api_key":true,"api_key_source":"environment|saved"}}` | N/A |
| POST | `/api/settings/llm` | `provider`、`api_base`、`model`、`api_key`（可空） | 同 GET | N/A |
| POST | `/api/settings/llm/test` | N/A | `{"ok":true,"provider":"deepseek","message":"..."}` | `400 LLM provider is not configured` 或连接错误 |

模型设置接口不回显 API Key 明文。`api_key` 留空时不会覆盖既有环境变量或已保存配置；保存位置沿用配置层的 appdata `.env`。

### 1.7 掌握评估

| 方法 | 路径 | 请求 | 成功响应 | 错误 |
|------|------|------|----------|------|
| GET | `/api/assessment/library?project_id=...` | query `project_id` | `{"library":{"project_id":"...","question_count":3,"result_count":2,"question_type_counts":{"concept":1},"status_counts":{"已掌握":1},"questions":[...],"recent_results":[...]}}` | `400 project_id is required`、`404 project not found` |
| POST | `/api/assessment/start` | `project_id` | `{"session":{"id":"...","project_id":"...","questions":[{"id":"...","question_type":"concept|flow|code_location","knowledge_point":"...","source_path":"...","prompt":"...","expected_points":[...]}]}}` | `404 project not found`、`400 assessment requires imported documents` |
| POST | `/api/assessment/answer` | `project_id`、`question`、`answer` | `{"result":{"result_id":"...","answer_id":"...","status":"已掌握|基本理解|需要补充|暂未掌握","score":0.0,"matched_points":[],"missing_points":[],"source_path":"..."}}` | `404 project not found`、`400 assessment question not found`、`400 answer is required` |

Web MVP 评估是最小闭环：题目从已导入文档规则化生成，当前支持 `concept`（概念理解）、`flow`（流程说明）和 `code_location`（代码定位）三类；每题保存轻量 `knowledge_point` 标签和 `source_path`。提交回答时服务端会按题目 ID 读取已保存题目，使用服务端持久化的 `expected_points` 和 `reference_snippet` 评分，不信任前端回传的参考要点；评分结果保存到 `assessment_results`，回答保存到 `assessment_answers`。该实现不等同于 legacy 桌面端完整 Knowledge Mastery 存储模型。

`GET /api/assessment/library` 是资料库管理概览使用的只读题库接口。它按当前项目返回题库数量、评估结果数量、题型分布、掌握状态分布、最近题目快照和最近评估结果；不生成新题、不评分、不修改评估会话，也不新增数据库表。

## 2. legacy 内部接口边界（应用层）

## 2.1 摄入与标准化

- `IngestWorkspaceUseCase.execute(...)`
  - 输入：workspace/project、路径、强制重建标志、是否增量。
  - 输出：分块数、索引状态、错误统计。
  - 行为约束：单文件解析失败不应阻断整批入库。

## 2.2 问答与检索

- `QueryKnowledgeBaseUseCase.execute(...)`
  - 输入：问题文本、workspace/project、检索参数。
  - 输出：`answer / sources / scores / model`。
  - 约束：无有效命中应返回可追溯提示，不应伪造答案。

## 2.3 配置与存储

- `load_settings`、`save_llm_provider`、`save_embed_provider` 等配置用例。
- `DocumentStore` / `ChunkStore` / `TagStore` / `SourceStore` 提供标准 CRUD。

## 3. 兼容说明

- 现阶段保留 `Workspace` 兼容层及其字段，跨模块迁移时需同步更新此文件与 `requirements`。
