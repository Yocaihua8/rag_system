# Notion / Obsidian 本地导出同步

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-06-28
> Related：docs/design/api-spec.md, docs/features/project-space-ingestion.md, docs/BACKLOG.md B-137

## 1. 目标

B-137 为知识工作者提供两个本地优先导入入口：

- Notion 导出的 Markdown zip 包。
- Obsidian vault 本地目录。

两类来源都复用现有 Web MVP 文档摄入、分块、向量化、导入批次和资料库刷新流程。第一版只处理用户本地提供的文件，不调用 Notion API，不联网，不保存第三方 token。

## 2. 范围

### 2.1 Notion Markdown zip

- 用户上传 Notion 导出的 `.zip` 文件。
- 后端只读取 zip 内的 Markdown / 文本类文件。
- 跳过附件、图片、二进制和不支持后缀。
- 保留 zip 内相对路径作为文档 `relative_path`，并统一加 `notion/` 前缀。
- 文档 `source_path` 使用虚拟来源前缀 `notion-zip:`，避免后续目录同步误删。
- 导入结果写入 `import_batches`，`source_type=notion_zip`。

### 2.2 Obsidian vault

- 用户选择 Obsidian vault 目录。
- 后端递归读取 vault 下 Markdown / 文本类文件。
- 跳过 `.obsidian`、`.trash`、`.git`、`node_modules` 等系统或缓存目录。
- 保留 vault 内相对路径，并统一加 `obsidian/` 前缀。
- 文档 `source_path` 使用虚拟来源前缀 `obsidian-vault:`，并带上 vault 根目录和相对路径，避免后续目录同步误删。
- 第一版 Obsidian 导入不会做删除清理；用户删除 vault 文件后再次导入，不会自动删除已入库记录。
- 导入结果写入 `import_batches`，`source_type=obsidian_vault`。

## 3. 接口边界

### 3.1 Notion zip 导入

`POST /api/import/notion-zip`

请求字段：

- `project_id`：必填，当前项目空间。
- `filename`：必填，上传文件名，必须为 `.zip`。
- `content_base64`：必填，zip 文件 base64 内容。

响应字段：

- `result`：复用 `ImportResult.to_dict()`。
- `batch`：导入批次摘要。
- `documents`：当前项目文档列表。

### 3.2 Obsidian vault 导入

`POST /api/import/obsidian-vault`

请求字段：

- `project_id`：必填，当前项目空间。
- `vault_path`：必填，本机 vault 目录路径。

响应字段：

- `result`：复用 `ImportResult.to_dict()`。
- `batch`：导入批次摘要。
- `documents`：当前项目文档列表。

## 4. 非目标

- 不接入 Notion API。
- 不自动解析 Notion 数据库结构或块级属性。
- 不解析 Obsidian wikilink / backlink 为知识图谱。
- 不引入异步任务队列。
- 不修改 SQLite schema。
- 不上传或保存第三方凭证。

## 5. 验收标准

- Notion zip 中的 Markdown 文件可以导入并可搜索。
- Obsidian vault 中的 Markdown 文件可以导入并可搜索。
- 不支持文件会被跳过并体现在导入结果中。
- 导入批次能区分 `notion_zip` 和 `obsidian_vault`。
- Vue 资料库导入面板提供两个入口，并复用现有刷新流程。
