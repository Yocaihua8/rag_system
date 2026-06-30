# Web 导入批次历史设计

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-06-29
> Scope：B-115 设计 + B-116 第一片实现边界；当前已落地导入批次表、只读历史接口和资料库页最近批次展示。

## 1. 背景

当前 Web MVP 已支持多种资料导入入口：本地项目目录同步、浏览器文件夹上传、单文件上传、文本笔记和 URL 摘录。导入完成后，前端会展示本轮新增、更新、未变更、删除、跳过和读取失败数量，也会展示跳过详情与错误明细。

这些信息曾经只存在于本轮响应和页面状态中。用户刷新页面、切换项目或隔天回看时，无法知道最近导入过什么、哪些文件被跳过、哪些读取失败、目录同步删除了哪些记录。B-115 已先设计“导入批次历史”模型，B-116 第一片已按该设计落地保存与展示闭环。

导入批次历史是审计与复盘信息，不是备份、回滚或全文快照。

## 2. 设计目标

- 记录每次导入动作的批次摘要。
- 支持按项目空间查看最近导入批次。
- 支持查看单个批次的跳过明细和错误明细。
- 覆盖目录同步、浏览器文件夹上传、单文件上传、文本笔记和 URL 摘录。
- 记录导入来源类型、触发入口、统计汇总、开始/结束时间和状态。
- 不保存文档正文，不复制 chunk/vector，不保存 API Key 或模型配置。
- 不提供回滚能力；后续如果要做回滚，需要另起设计。

## 3. 非目标

- 第一片不记录尚未解析出有效 `project_id` 的校验失败请求。
- 不做导入回滚，不恢复被删除的文档记录。
- 不保存被导入文件的完整正文或二进制内容。
- 不保存浏览器上传文件的原始本机绝对路径。
- 不把导入批次当成备份导出格式。
- 不做跨项目批次聚合、全局审计后台或多用户权限。
- 不新增外部依赖或持久化后台任务队列；B-08 仅提供进程内项目级串行保护。

## 4. 批次来源类型

建议用 `source_type` 区分导入入口：

| source_type | 来源 | 当前接口 | 说明 |
|-------------|------|----------|------|
| `directory_sync` | 同步当前项目目录 | `POST /api/import` | 会扫描项目绑定目录，可能产生删除记录 |
| `browser_folder_upload` | 浏览器文件夹导入 | `POST /api/import/upload` | 前端通过 `webkitdirectory` 上传相对路径 |
| `file_upload` | 单文件/多文件上传 | `POST /api/import/upload` | 前端普通 `multiple` 文件选择 |
| `text_note` | 文本笔记 | `POST /api/import/note` | 写入 `note:` 虚拟来源 |
| `url_excerpt` | URL 摘录 | `POST /api/import/url` | 写入 `url:` 虚拟来源，不自动抓取网页 |

`POST /api/import/upload` 当前同时服务浏览器文件夹和普通文件上传。B-116 可由前端显式传入 `source_type`，或由上传文件是否带目录相对路径推断；推荐前端显式传入，避免后端用路径形态猜测用户意图。

## 5. 数据模型

B-116 已新增 `import_batches` 表：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | TEXT PRIMARY KEY | 批次 ID |
| `project_id` | TEXT NOT NULL | 所属项目空间 |
| `source_type` | TEXT NOT NULL | 导入来源类型 |
| `status` | TEXT NOT NULL | `success / partial / failed` |
| `started_at` | TEXT NOT NULL | 批次开始时间 |
| `finished_at` | TEXT NOT NULL | 批次结束时间 |
| `summary_json` | TEXT NOT NULL | 统计摘要 JSON |
| `message` | TEXT NOT NULL DEFAULT '' | 可选摘要说明 |
| `created_at` | TEXT NOT NULL | 记录创建时间 |

`summary_json` 建议保存：

| 字段 | 说明 |
|------|------|
| `imported` | 本轮成功入库或确认的文件数 |
| `created` | 新增文件数 |
| `updated` | 内容变更后更新的文件数 |
| `unchanged` | 内容未变更文件数 |
| `deleted` | 源目录已删除而被清理的记录数 |
| `skipped` | 跳过文件数 |
| `errors` | 读取失败或导入异常数量 |

B-116 已新增 `import_batch_items` 表：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | TEXT PRIMARY KEY | 明细 ID |
| `batch_id` | TEXT NOT NULL | 所属批次 |
| `project_id` | TEXT NOT NULL | 冗余项目 ID，便于隔离校验 |
| `kind` | TEXT NOT NULL | `created / updated / unchanged / deleted / skipped / error` |
| `relative_path` | TEXT NOT NULL DEFAULT '' | 相对路径或虚拟来源路径 |
| `document_id` | TEXT NOT NULL DEFAULT '' | 可选文档 ID |
| `reason` | TEXT NOT NULL DEFAULT '' | 跳过或失败原因 |
| `created_at` | TEXT NOT NULL | 记录创建时间 |

约束建议：

- `import_batches.project_id` 外键指向 `projects.id`，删除项目时级联清理批次。
- `import_batch_items.batch_id` 外键指向 `import_batches.id`，删除批次时级联清理明细。
- `import_batch_items.document_id` 不建议强外键约束到 `documents.id`，因为历史批次需要在文档后续被删除后仍可读。
- 批次和明细都必须通过 `project_id` 做访问隔离。

## 6. 状态规则

批次状态建议：

| status | 含义 |
|--------|------|
| `success` | 导入流程完成，且没有读取失败或导入异常 |
| `partial` | 导入流程完成，但存在跳过或读取失败 |
| `failed` | 导入流程在项目校验、目录访问、payload 校验或处理阶段失败 |

边界建议：

- `skipped > 0` 不一定是失败；例如格式不支持或超过大小限制，是受控跳过。
- `errors` 表示读取失败或解析失败，应在批次详情中单独展示。
- `failed` 批次后续可以保存，用于解释为什么没有产生文档变更；第一片暂不记录未解析出有效项目的校验失败请求，避免保存无归属或敏感 payload。

## 7. API 设计建议

B-116 第一片已新增只读历史接口：

| 方法 | 路径 | 请求 | 成功响应 | 说明 |
|------|------|------|----------|------|
| GET | `/api/import/batches?project_id=...` | query `project_id` | `{"batches":[...]}` | 列出当前项目最近导入批次 |
| GET | `/api/import/batches/detail?batch_id=...` | query `batch_id` | `{"batch":...,"items":[...]}` | 查看单个批次和明细 |

导入接口可在成功响应中追加 `batch` 摘要：

| 当前接口 | 建议新增响应字段 |
|----------|------------------|
| `POST /api/import` | `batch` |
| `POST /api/import/upload` | `batch` |
| `POST /api/import/note` | `batch` |
| `POST /api/import/url` | `batch` |

错误边界：

- 缺少 `project_id` 返回 `400 project_id is required`。
- 项目不存在返回 `404 project not found`。
- 缺少 `batch_id` 返回 `400 batch_id is required`。
- 批次不存在返回 `404 import batch not found`。

## 8. 前端交互建议

B-116 第一片已放在资料库页，位置靠近“导入状态”：

- 展示当前项目最近导入批次列表。
- 每条批次显示来源类型、时间、状态、统计摘要。
- 支持点击“查看详情”展开或读取单条详情。
- 详情展示跳过明细和错误明细，沿用当前“未导入 / 读取失败”的用户语言。
- 不提供“回滚”“重新导入本批次”“删除批次”按钮。

第一片不建议做分页、筛选器、导出批次日志、批次对比或自动重试。

## 9. 与现有能力的关系

- 与导入预检：预检是只读估算，不应创建导入批次。
- 与导入结果展示：批次历史保存导入后结果，页面仍可继续展示本轮结果。
- 与文档集合：批次历史不自动把文档加入集合，也不记录集合快照。
- 与备份导出：批次历史可后续选择是否导出，但第一版不进入备份格式。
- 与检索复盘：检索复盘记录查询质量，导入批次记录资料变更，两者不合并。
- 与 URL 摘录：批次记录 URL 摘录的虚拟来源路径，不自动抓取网页。
- 与 B-08 并发索引：导入批次历史仍只记录完成后的审计摘要，不作为排队任务表。同一项目的写入型导入由进程内项目锁串行，不同项目可以并发执行；第一片不新增 `queued/running` 持久化状态。

## 10. 测试建议

B-116 第一片已覆盖：

- 目录同步成功后创建导入批次。
- 浏览器上传和单文件上传能区分 `source_type`。
- 文本笔记和 URL 摘录导入创建批次。
- B-08 补充覆盖同一项目目录同步串行、不同项目目录同步可重叠，以及 `/api/*` 同步分发进入线程池。
- 批次摘要包含新增、更新、未变更、删除、跳过和错误数量。
- 批次详情包含跳过明细和错误明细。
- 导入预检不创建批次。
- 删除项目空间级联清理批次。
- 前端静态测试覆盖批次列表、详情入口和无回滚按钮。
- 文档契约覆盖新接口、表字段和“不保存正文”的边界。

## 11. 风险

- 如果保存文档正文或上传原始内容，容易突破当前备份导出的安全边界。
- 如果第一片加入回滚，会引入文档版本、chunk/vector 恢复和集合关系恢复问题，范围过大。
- 如果把跳过当成失败，会误导用户；跳过和读取失败必须分开显示。
- 如果不保留失败批次，用户无法回看导入为什么没有发生。
- 如果强外键绑定历史明细到当前文档，后续删除文档会破坏历史可读性。
