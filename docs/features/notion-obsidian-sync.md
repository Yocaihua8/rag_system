# Notion / Obsidian 本地导入与 Obsidian 插件桥

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-07-30
> Scope：Notion ZIP/Obsidian Vault 一次性导入与 desktop-only 插件增量同步、受控发布
> Related：docs/design/api-spec.md, docs/design/database-design.md, docs/features/project-space-ingestion.md, docs/features/project-knowledge-coach.md, docs/BACKLOG.md B-137 / B-163

## 1. 目标

B-137 为知识工作者提供两个本地优先的一次性导入入口：

- Notion 导出的 Markdown zip 包。
- Obsidian vault 本地目录。

两类来源都复用现有 Web MVP 文档摄入、分块、向量化、导入批次和资料库刷新流程。该入口只处理用户本地提供的文件，不调用 Notion API，不联网，不保存第三方 token。

B-163 在不改变上述兼容接口的前提下新增 Obsidian 桌面插件桥：插件把 Vault Markdown 事件同步到本地服务，并在用户确认后执行系统管理 Markdown 的受控写回。后端不直接扫描或写入 Vault；插件桥不支持移动端或社区市场发布。

## 2. 一次性导入范围（B-137）

### 2.1 Notion Markdown zip

- 用户上传 Notion 导出的 `.zip` 文件。
- 后端只读取 zip 内的 Markdown / 文本类文件。
- 跳过附件、图片、二进制和不支持后缀。
- 保留 zip 内相对路径作为文档 `relative_path`，并统一加 `notion/` 前缀。
- 文档 `source_path` 使用虚拟来源前缀 `notion-zip:`，避免后续目录同步误删。
- 导入结果写入 `import_batches`，`source_type=notion_zip`。

### 2.2 Obsidian vault 一次性只读导入

- 用户选择 Obsidian vault 目录。
- 后端递归读取 vault 下 Markdown / 文本类文件。
- 跳过 `.obsidian`、`.trash`、`.git`、`node_modules` 等系统或缓存目录。
- 保留 vault 内相对路径，并统一加 `obsidian/` 前缀。
- 文档 `source_path` 使用虚拟来源前缀 `obsidian-vault:`，并带上 vault 根目录和相对路径，避免后续目录同步误删。
- `/api/import/obsidian-vault` 保持一次性只读导入语义，不提供插件事件、删除清理或文件系统写回；用户删除 vault 文件后再次导入，不会自动删除已入库记录。
- 导入结果写入 `import_batches`，`source_type=obsidian_vault`。

## 3. 一次性导入接口

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

### 3.2 Obsidian vault 一次性只读导入

`POST /api/import/obsidian-vault`

请求字段：

- `project_id`：必填，当前项目空间。
- `vault_path`：必填，本机 vault 目录路径。

响应字段：

- `result`：复用 `ImportResult.to_dict()`。
- `batch`：导入批次摘要。
- `documents`：当前项目文档列表。

## 4. Obsidian 桌面插件桥（B-163 已实现）

### 4.1 配对与连接

- 每个项目最多一个 `active` 连接。
- Web 端创建的一次性配对码默认五分钟过期；插件提交配对码、Vault 身份和输出目录后，换取仅用于 Obsidian 插件路由的可撤销 Bearer 令牌。
- 服务端只持久化配对码与令牌的 SHA-256 哈希；明文只在创建或换取时返回一次，不进入普通连接响应。
- 默认输出目录为 `Knowledge Island/<项目名>/`，配对时可以修改。所有路径都在服务端和插件侧规范化，绝对路径、路径穿越、非 Markdown 目标或越界路径会被拒绝。

### 4.2 Vault 事件同步

- 插件监听 Markdown 的新增、修改、重命名和删除，并批量发送统一的 `upsert / rename / delete` 事件。
- 每个事件带连接内稳定的 `event_id`；服务端以 `(connection_id, event_id)` 幂等保存并重放原结果，不重复导入、重命名或删除。
- `upsert` 可以携带正文、内容哈希、Frontmatter、标签及已解析/未解析 Wikilink 计数；`rename` 保留既有文档身份；`delete` 删除相应索引并把依赖分析标记为 `stale`。
- 插件离线时事件保存在本地队列，恢复连接后重放。
- 配置的系统输出目录完全排除在反向摄入之外，避免生成内容触发反馈循环。

### 4.3 受控发布

发布严格分为三个授权阶段：

1. Web 端生成内容与目标路径预览，保存不可变发布修订。
2. 用户显式确认后，发布进入 `queued`，等待插件领取。
3. 插件校验并写入 Vault，再回传 `applied / conflict / failed` 结果。

可发布产物为：

- `项目理解.md`
- `知识覆盖与技能差距.md`
- `学习计划.md`
- `评估记录/<时间>.md`

每份可更新文件必须包含 `knowledge_island_managed`、稳定 ID、项目 ID、产物类型和修订号。插件在覆盖前校验目标路径、系统标记、身份与 `expected_vault_hash`；无标记同名文件、身份不符、外部编辑造成哈希变化或路径越界一律返回 `conflict`，首版不自动合并。写入使用 Vault 原子处理和 Frontmatter API；用户删除生成文件后不会自动重建。

服务端保留不可变发布修订和执行结果。回滚以历史发布为来源创建新的发布修订，再次走预览、确认和插件执行流程，不修改历史记录。

### 4.4 插件桥接口

- `POST /api/obsidian/pairing/start`
- `POST /api/obsidian/pairing/complete`
- `GET /api/obsidian/connections`
- `POST /api/obsidian/connections/revoke`
- `POST /api/obsidian/sync/events`
- `POST /api/obsidian/publications/preview`
- `POST /api/obsidian/publications/confirm`
- `POST /api/obsidian/publications/result`
- `GET /api/obsidian/publications/pending`

其中配对完成、事件同步、待执行发布和结果回传由配对码或插件 Bearer 令牌鉴权；连接查看、主应用撤销以及发布预览/确认仍使用应用自身认证边界。插件也可用 Bearer 令牌撤销自身连接，但不能撤销其他连接。完整字段和错误契约见 `docs/design/api-spec.md`。

## 5. 非目标

- 不接入 Notion API。
- 不自动解析 Notion 数据库结构或块级属性。
- 不把 Obsidian wikilink / backlink 自动扩张为知识图谱。
- 不引入异步任务队列。
- 不上传或明文保存第三方凭证。
- 不由后端直接写入 Vault。
- 不做移动端插件、社区市场发布、自动冲突合并或未确认写回。

## 6. 验收标准

- Notion zip 中的 Markdown 文件可以导入并可搜索。
- Obsidian vault 中的 Markdown 文件可以导入并可搜索。
- 不支持文件会被跳过并体现在导入结果中。
- 导入批次能区分 `notion_zip` 和 `obsidian_vault`。
- Vue 资料库导入面板提供两个入口，并复用现有刷新流程。
- 插件配对只返回一次明文令牌，每项目最多一个活动连接，无效或已撤销令牌不能继续访问插件路由。
- 重复事件、离线重放、重命名、删除和输出目录排除均有确定结果。
- 发布需经过预览、确认和插件执行；无标记文件、哈希变化和路径越界会停止覆盖。
- 发布修订不可变，可从历史发布创建新的回滚修订。
