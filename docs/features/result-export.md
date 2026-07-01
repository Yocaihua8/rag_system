# 结果导出

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-06-29
> Scope：B-07 生成结果导出为 Markdown / PDF
> Related：docs/design/api-spec.md, docs/BACKLOG.md

## 1. 功能定位

B-07 面向本地 Knowledge Island Web MVP 的问答结果归档场景，支持将已生成的回答结果导出到本地 `data/outputs/` 目录。

## 2. 已实现范围

- 支持 Markdown 与 PDF 两种导出格式。
- 导出内容来自已生成的问答消息，包含问题、回答和引用来源。
- 导出接口写入本地输出目录，并返回文件名、路径、格式、MIME 类型和文件大小。
- 默认输出目录为 `data/outputs/`；测试或本地自定义部署可通过 `KI_OUTPUT_DIR` 或 `RAG_OUTPUT_DIR` 覆盖。
- 请求必须提供 `project_id`、`message_id` 和 `format`；消息必须属于当前项目，跨项目消息按不存在处理。
- Markdown 文件使用 UTF-8 文本；PDF 文件使用同一内容生成轻量文本 PDF，不依赖大型 PDF 渲染库。

## 3. 用户可见行为

- 成功调用 `POST /api/export/result` 后，后端在本机输出目录生成 `.md` 或 `.pdf` 文件。
- 成功响应返回 `format`、`filename`、`path`、`mime_type` 和 `bytes`，不直接返回文件内容。
- `format` 只允许 `markdown` 或 `pdf`，其他值返回 `400 format must be markdown or pdf`。
- 缺少 `project_id` 或 `message_id` 返回 400；项目不存在返回 404；消息不存在或不属于当前项目返回 `404 chat message not found`。

## 4. 架构落点

- `backend/routes/export.py` 承载 `POST /api/export/result` 参数校验、项目存在性校验和消息归属校验。
- `backend/domain/result_export.py` 负责 Markdown / PDF 内容生成、输出目录解析、文件写入和元数据返回。
- `backend/storage/knowledge_store.py` 不新增表结构；导出读取既有 `chat_messages` 记录。

## 5. 非目标

- 不新增数据库 schema。
- 不实现远程对象存储、邮件分享或云端同步。
- 不实现批量导出、导出历史列表或文件删除管理。
- 不引入大型 PDF 渲染依赖。
- 不新增前端导出按钮；当前交付范围为本地 API 能力。
