# Web 文档集合分组模型设计

> 状态：Design
> Owner：RAG 团队
> Last Updated：2026-05-25
> Scope：B-113/B-114，设计文档集合/分组与现有项目文档列表、检索过滤的关系；B-114 已落地资料库集合管理第一片，问答/检索按集合过滤仍为后续范围。

## 1. 背景

当前 Web MVP 已支持项目空间、文档导入、文档列表、chunk/vector 检索、检索诊断、问答和备份恢复。随着一个项目空间内资料增多，用户需要把相关文档按主题、阶段或资料类型进行轻量归组，避免资料库列表过长时只能依赖路径过滤。

文档集合应是应用内的管理视图，不等同于磁盘目录。把文档加入集合不应移动源文件、不应复制文档正文、不应重建 chunk/vector，也不应影响现有导入、删除和恢复边界。

B-113 的目标是先明确集合模型和后续检索过滤关系。B-114 第一片已落地集合 CRUD、文档加入/移出集合和资料库列表过滤；问答、检索诊断和 Agent 来源检索按集合过滤仍保留为后续任务。

## 2. 设计目标

- 支持每个项目空间拥有多个文档集合。
- 支持把同一项目内的文档加入一个或多个集合。
- 支持后续资料库按集合过滤文档列表。
- 为后续问答、检索诊断和 Agent 来源检索按集合过滤预留边界。
- 不复制文档正文、chunk 或 vector，只保存集合元数据和文档关联关系。
- 删除集合不删除文档；删除文档时清理集合关联。
- 保持当前未分组文档、目录导入、单文件上传、文本笔记和 URL 摘录行为兼容。

## 3. 非目标

- B-113 不建表、不改接口、不改前端、不改变现有检索行为。
- 不做跨项目集合；集合只能引用同一项目空间内的文档。
- 不做团队权限、共享集合或多用户访问控制。
- 不做无限层级文件夹；第一片只设计一层轻量集合。
- 不把集合替代 tag、来源类型或磁盘目录。
- 不因加入集合而重新分块、重新嵌入或复制文档内容。
- 不在第一片实现拖拽排序、批量移动、集合模板或自动分类。

## 4. 数据模型建议

后续 B-114 可新增 `document_collections` 表：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | TEXT PRIMARY KEY | 集合 ID |
| `project_id` | TEXT NOT NULL | 所属项目空间 |
| `name` | TEXT NOT NULL | 集合名称，例如“接口文档”“需求资料” |
| `description` | TEXT NOT NULL DEFAULT '' | 可选说明 |
| `color` | TEXT NOT NULL DEFAULT '' | 可选展示色，不参与业务判断 |
| `created_at` | TEXT NOT NULL | 创建时间 |
| `updated_at` | TEXT NOT NULL | 更新时间 |

后续可新增 `document_collection_items` 表：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | TEXT PRIMARY KEY | 关联记录 ID |
| `project_id` | TEXT NOT NULL | 冗余项目 ID，便于隔离校验 |
| `collection_id` | TEXT NOT NULL | 集合 ID |
| `document_id` | TEXT NOT NULL | 文档 ID |
| `created_at` | TEXT NOT NULL | 加入时间 |

约束建议：

- `document_collections.project_id` 外键指向 `projects.id`，删除项目时级联清理。
- `document_collection_items.collection_id` 外键指向 `document_collections.id`，删除集合时级联清理关联。
- `document_collection_items.document_id` 外键指向 `documents.id`，删除文档时级联清理关联。
- `document_collection_items.project_id` 必须与集合和文档所属项目一致。
- 同一集合内同一文档只允许出现一次，建议约束 `UNIQUE(collection_id, document_id)`。
- 集合名称建议在同一项目内唯一，避免资料库过滤入口出现重名。

## 5. API 设计建议

B-114 第一片建议新增集合管理接口：

| 方法 | 路径 | 请求 | 成功响应 | 说明 |
|------|------|------|----------|------|
| GET | `/api/document-collections?project_id=...` | query `project_id` | `{"collections":[...]}` | 列出当前项目集合和文档数量 |
| POST | `/api/document-collections` | `project_id`、`name`、`description`、`color` | `{"collection":...}` | 新增集合 |
| POST | `/api/document-collections/update` | `collection_id`、字段 | `{"collection":...}` | 更新集合名称、说明或展示色 |
| POST | `/api/document-collections/delete` | `collection_id` | `{"deleted":true,"collections":[...]}` | 删除集合，不删除文档 |
| POST | `/api/document-collections/items/add` | `collection_id`、`document_ids` | `{"collection":...}` | 把文档加入集合 |
| POST | `/api/document-collections/items/remove` | `collection_id`、`document_ids` | `{"collection":...}` | 从集合移除文档 |

文档列表过滤可在后续扩展现有接口：

| 方法 | 路径 | 请求 | 成功响应 | 说明 |
|------|------|------|----------|------|
| GET | `/api/documents?project_id=...&collection_id=...` | query `collection_id` 可空 | `{"documents":[...]}` | 按集合过滤资料库文档列表 |

错误边界：

- 缺少 `project_id` 返回 `400 project_id is required`。
- 项目不存在返回 `404 project not found`。
- 集合不存在或不属于当前项目返回 `404 document collection not found`。
- 文档不存在或不属于当前项目返回 `404 document not found`。
- 跨项目加入集合必须拒绝，避免集合泄漏其他项目文档。
- 空集合名称返回 `400 name is required`。

## 6. 检索过滤关系

集合不直接参与 chunk/vector 存储。后续按集合检索时，应先把 `collection_id` 转换为当前项目内的 `document_id` 集合，再复用现有检索流程。

建议分层：

1. 资料库过滤：`collection_id` 只影响文档列表展示。
2. 检索诊断过滤：`/api/search/debug` 可选接受 `collection_id`，只在集合内文档的 chunks 中检索。
3. 问答过滤：`/api/answer` 可选接受 `collection_id`，来源片段限制在集合内文档。
4. Agent 来源检索过滤：`search_sources` 工具后续可接受 `collection_id`，但仍保持只读。

边界建议：

- 空集合参与检索时返回空来源，并给出“该集合暂无可检索文档”的明确提示。
- 集合过滤不改变 `top_k`、最低分、关键词/向量开关或模型 Profile。
- 集合过滤不改变 B-105 项目级检索默认值，只作为额外范围约束。
- 搜索实现优先接收 `document_ids` 或 `collection_id` 的可选过滤条件，不应复制 chunks 或 vectors。

## 7. 前端交互建议

B-114 第一片建议放在资料库视图中，保持低复杂度：

- 文档列表上方增加集合筛选入口，包含“全部文档”和“未分组”。
- 侧边或列表区域展示当前项目集合、集合文档数量和新增入口。
- 支持新建、重命名、删除集合。
- 支持选择一个或多个文档后加入集合或从集合移除。
- 删除集合前二次确认，并明确“不删除文档”。
- 文档详情可展示所属集合名称。

第一片不建议做拖拽排序、嵌套集合、智能推荐集合、批量自动分类或复杂颜色系统。

## 8. 导入、删除与备份关系

导入关系：

- 浏览器文件夹导入、单文件上传、文本笔记和 URL 摘录仍创建普通文档。
- 新导入文档默认不自动加入集合，避免误分类。
- 后续可以在导入后提示“加入集合”，但不应改变导入接口的核心语义。

删除关系：

- 删除文档记录时，应级联清理 `document_collection_items`。
- 删除集合时，只删除集合和关联记录，不删除 `documents`、`document_chunks` 或 `chunk_vectors`。
- 目录同步删除源目录中消失的文档时，应同步清理集合关联。

备份关系：

- 后续导出可以包含集合元数据和集合-文档关联。
- 当前项目备份已包含文档正文、chunk/vector，但仍不包含集合元数据、集合-文档关联或 API Key。
- 恢复时应像 B-103 文档和聊天记录一样重新生成集合 ID，并把集合关联映射到恢复后的新文档 ID。

## 9. 测试建议

B-114 实现时至少覆盖：

- 集合新增、列表、更新、删除。
- 集合名称为空、项目不存在、集合不存在的错误响应。
- 文档加入集合、重复加入幂等或受控拒绝、从集合移除。
- 跨项目文档加入集合被拒绝。
- 删除集合不删除文档。
- 删除文档后集合关联被清理。
- 资料库按集合过滤文档列表。
- “未分组”过滤只返回没有任何集合关联的当前项目文档。
- 文档契约覆盖接口、数据库字段和“不复制正文/不保存 API Key”的边界。
- 前端静态测试覆盖集合筛选、新建、加入、移除和删除入口。

## 10. 风险

- 如果把集合误做成磁盘目录，容易引入移动文件、路径同步和导入删除冲突。
- 如果集合过滤直接复制 chunks/vectors，会增加一致性风险和存储膨胀。
- 如果不校验集合与文档的项目归属，可能出现跨项目资料泄漏。
- 如果第一片同时做嵌套集合、拖拽和智能分类，会明显扩大实现范围。
- 如果删除集合的文案不清晰，用户可能误以为文档也会被删除；前端需要明确二次确认。
