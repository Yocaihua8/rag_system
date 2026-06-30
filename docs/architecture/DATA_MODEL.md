# 知识岛数据模型（历史参考，已被取代）

> 状态：Superseded（已被取代，仅供历史参考）
> 取代文档：`docs/design/database-design.md`（SQLite 当前表结构与迁移规范）
> 保留原因：本文档为旧架构阶段的数据模型快照（2026-05-16），"第一片已开始落地"等措辞属当时进度，**不代表当前 schema**；当前以 `docs/design/database-design.md` 为准。
> 日期：2026-05-16
> 范围：当前文件记录已实现和已预留的核心模型，不把后续规划描述成已完成能力。

## 1. 当前落地范围

本轮已落地知识岛的基础数据模型与 SQLite schema：

- Project
- Document
- Chunk
- Tag
- DocumentTag
- Source
- GraphNode
- GraphEdge
- SkillArea
- KnowledgePoint
- Evidence
- MasteryRecord

现有应用流程仍保留 `Workspace`，用于兼容当前 PySide6 UI、导入流程、检索流程和已有数据库。后续迁移应把 `Workspace` 的用户语义逐步收敛为 `Project`，不能一次性删除旧字段。

## 2. Project

项目空间，用于承载某个本地项目、资料集合或长期知识主题。

| 字段 | 说明 |
|------|------|
| `id` | 主键 |
| `name` | 项目空间名称 |
| `description` | 描述 |
| `root_path` | 本地根路径，可为空 |
| `created_at` | 创建时间 |
| `updated_at` | 更新时间 |

## 3. Document

文档或笔记，是知识岛的核心知识资产。

| 字段 | 说明 |
|------|------|
| `id` | 主键 |
| `project_id` | 所属项目空间 |
| `title` | 标题 |
| `source_type` | 来源类型，如 markdown、txt、code、pdf、docx、ocr |
| `source_path` | 本地来源路径 |
| `raw_content` | 原始内容 |
| `normalized_markdown` | 标准化 Markdown，作为 AI 读取和切片主来源 |
| `plain_text` | 纯文本，作为搜索和 embedding 主输入 |
| `rendered_html` | 自动渲染后的阅读 HTML |
| `created_at` | 创建时间 |
| `updated_at` | 更新时间 |

### Markdown 标准化与安全渲染

当前导入 `.md / .markdown` 文件时会生成三份派生内容：

- `normalized_markdown`：统一换行、去除 BOM 和行尾空白，移除非代码块中的 `script/style` 内容与外部 HTML 标签，保留可阅读文本。
- `plain_text`：从标准化 Markdown 派生，去除标题符号、列表符号、链接语法和常见强调符号，作为搜索和 embedding 的主输入。
- `rendered_html`：由受控 Markdown 子集生成，只输出应用自己创建的 `h1-h6 / p / ul / li / pre / code` 标签；用户内容全部 HTML 转义，避免 script 注入和事件属性执行。

当前实现不是完整 Markdown 引擎；表格、任务列表、脚注、HTML 扩展语法仍属于后续增强范围。

兼容字段：

- `workspace_id`
- `content`
- `domain`
- `tags`

这些字段仍服务于现有导入、检索和 UI。后续迁移时需要先改应用服务和存储，再删除旧语义。

## 4. Chunk

文档切片，是检索和引用的最小单元。

| 字段 | 说明 |
|------|------|
| `id` | 主键 |
| `document_id` | 所属文档 |
| `project_id` | 所属项目空间 |
| `chunk_index` | 文档内序号 |
| `heading_path` | 标题层级路径 |
| `chunk_markdown` | 切片 Markdown |
| `chunk_plain_text` | 切片纯文本 |
| `token_count` | 估算 token 数 |
| `embedding_id` | 向量索引 ID |
| `created_at` | 创建时间 |
| `updated_at` | 更新时间 |

兼容字段：

- `workspace_id`
- `domain`
- `tags`
- `content`
- `order`

## 5. Tag / DocumentTag

`Tag` 用于给文档打标签，`DocumentTag` 表达文档与标签的多对多关系。

| 模型 | 字段 |
|------|------|
| `Tag` | `id / name / color / created_at / updated_at` |
| `DocumentTag` | `document_id / tag_id` |

## 6. Source

`Source` 记录导入来源和 checksum，用于来源追踪与重复文件识别。

| 字段 | 说明 |
|------|------|
| `id` | 主键 |
| `document_id` | 所属文档 |
| `source_type` | 来源类型 |
| `source_path` | 本地路径 |
| `imported_at` | 导入时间 |
| `checksum` | 文件内容 checksum |

## 7. SkillArea / KnowledgePoint / Evidence / MasteryRecord

用于掌握评估的基础分层模型，当前版本已完成 schema 与领域模型定义。

| 模型 | 字段 |
|------|------|
| `SkillArea` | `id / workspace_id / name / description / created_at / updated_at` |
| `KnowledgePoint` | `id / workspace_id / skill_area_id / name / summary / confidence / created_at / updated_at` |
| `Evidence` | `id / workspace_id / knowledge_point_id / source_path / snippet / confidence / created_at` |
| `MasteryRecord` | `id / workspace_id / knowledge_point_id / status / evidence_id / confidence / note / created_at / updated_at` |

`MasteryRecord.status` 三态：`claimed`、`evidence_found`、`verified`。

## 8. GraphNode / GraphEdge

知识图谱最小结构，面向“节点 + 关系 + 置信度 + 来源”。

| 模型 | 字段 |
|------|------|
| `GraphNode` | `id / workspace_id / name / label / node_type / source_ref / confidence / created_at / updated_at` |
| `GraphEdge` | `id / workspace_id / source_node_id / target_node_id / relationship / confidence / source_path / source_snippet / created_at / updated_at` |

关系检索当前仅支持：

- 按源节点查询一跳边
- 关系置信度阈值筛选
- 按节点类型筛选

## 9. 尚未落地

以下内容属于后续切片，当前不能在 UI 或文档中描述为已完成：

- PDF / Word 解析
- 图片 OCR
- Concept / Technology / Problem / Solution / Decision / Prompt / Summary
- KnowledgeGap / LearningRecommendation / ReviewTask
- GraphRAG 风格关系检索
