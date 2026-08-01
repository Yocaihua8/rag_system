# 问答结果导出

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：把一条已生成的问答结果写为本地 Markdown 或 PDF
> Related：`retrieval-and-question-answering.md`、`../design/api-spec.md`、`../guides/runbook.md`

## 1. 当前能力

- `POST /api/export/result` 接受 `project_id`、`message_id` 和 `format`。
- 格式只允许 `markdown` 或 `pdf`；内容包含问题、回答和引用来源。
- 默认写入 `data/outputs/`，可用 `KI_OUTPUT_DIR` 或 `RAG_OUTPUT_DIR` 覆盖。
- 响应返回格式、文件名、本机路径、MIME 类型和字节数，不直接返回文件内容。
- 消息必须属于当前项目；跨项目消息按不存在处理。

## 2. 可达边界

后端导出 API 已实现，但当前 Vue 主界面没有导出按钮，因此属于“API 可用、主界面不可达”的兼容能力。

## 3. 限制

- 当前没有批量导出、导出历史、文件下载端点、删除管理或云端分享。
- PDF 为同内容的轻量文本 PDF，不依赖大型渲染组件。
- 结果导出目录与 v2 数据库目录不同；备份 `runtime/v2/` 不自动包含 `data/outputs/`。
