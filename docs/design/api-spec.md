# 接口与契约说明

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-20
> Scope：本地 Web MVP HTTP API + legacy 进程内接口

## 1. 本地 Web MVP HTTP API

当前默认入口为本地 Web MVP：`app.py` -> `webapp.server.run_server()`。HTTP 服务默认监听 `http://127.0.0.1:8765`，仅用于本机浏览器访问，不作为远程多用户 API 承诺。

端点速览：

- `GET /api/health`
- `GET /api/projects`
- `POST /api/projects`
- `POST /api/projects/rename`
- `POST /api/projects/delete`
- `GET /api/documents`
- `GET /api/document`
- `POST /api/documents/delete`
- `POST /api/import`
- `POST /api/search`
- `POST /api/answer`

### 1.1 健康检查

| 方法 | 路径 | 用途 | 成功响应 |
|------|------|------|----------|
| GET | `/api/health` | 确认本地服务可访问 | `{"status":"ok"}` |

### 1.2 项目空间

| 方法 | 路径 | 请求 | 成功响应 | 错误 |
|------|------|------|----------|------|
| GET | `/api/projects` | N/A | `{"projects":[...]}` | N/A |
| POST | `/api/projects` | `name`、`path` | `201 {"project":...}` | `400 path must be an existing directory` |
| POST | `/api/projects/rename` | `project_id`、`name` | `{"project":...}` | `400 name is required`、`404 project not found` |
| POST | `/api/projects/delete` | `project_id` | `{"deleted":true}` | `404 project not found` |

项目对象字段：

| 字段 | 说明 |
|------|------|
| `id` | 项目空间 ID |
| `name` | 项目空间名称 |
| `root_path` | 绑定的本地目录 |
| `root_exists` | 绑定目录是否仍然存在 |
| `created_at` | 创建时间 |

### 1.3 文档与导入

| 方法 | 路径 | 请求 | 成功响应 | 错误 |
|------|------|------|----------|------|
| GET | `/api/documents?project_id=...` | query `project_id` | `{"documents":[...]}` | `400 project_id is required` |
| GET | `/api/document?document_id=...` | query `document_id` | `{"document":...}` | `400 document_id is required`、`404 document not found` |
| POST | `/api/documents/delete` | `document_id` | `{"deleted":true,"documents":[...]}` | `404 document not found` |
| POST | `/api/import` | `project_id` | `{"result":...,"documents":[...]}` | `404 project not found`、`400 project root path does not exist` |

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

### 1.4 检索与问答

| 方法 | 路径 | 请求 | 成功响应 |
|------|------|------|----------|
| POST | `/api/search` | `project_id`、`query` | `{"hits":[...]}` |
| POST | `/api/answer` | `project_id`、`question` | `{"answer":"...","sources":[...]}` |

当前 Web MVP 使用 SQLite 中的文本内容做关键词排序，不依赖 Ollama、向量库或云端 API。问答结果由本地命中片段组合生成，并展示来源文件与片段；无命中时不伪造来源。

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
