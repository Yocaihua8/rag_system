# Web 多会话聊天模型设计

> 状态：Design
> Owner：RAG 团队
> Last Updated：2026-05-23
> Scope：B-107，仅设计 `chat_sessions` 与现有 `chat_messages` 的兼容关系；本文件不代表已建表或已实现 UI。

## 1. 背景

当前 Web MVP 的聊天记录以 `chat_messages` 按项目保存。每次 `/api/answer` 成功后写入一条消息，前端通过 `/api/chat/messages?project_id=...` 读取当前项目最近对话，真实 LLM 回答会取同项目最近 3 轮作为上下文。

这个结构能支撑单一项目问答流，但不适合长期使用后的主题分流。例如同一个项目中，用户可能分别讨论“架构说明”“接口排查”“学习复盘”。如果所有消息都混在一个列表里，后续上下文会互相干扰，也不利于按主题回看。

B-107 的目标是先设计多会话模型，不直接建表。实际落地应由 B-108 执行。

## 2. 设计目标

- 支持一个项目空间下有多个聊天会话。
- 保留现有 `chat_messages` 数据，不强制迁移历史消息。
- 允许没有 `session_id` 的旧消息继续显示在“默认会话”。
- `/api/answer` 后续可以按当前会话取最近 3 轮上下文，而不是按整个项目取最近 3 轮。
- 删除会话只影响会话和会话内消息，不删除文档、检索复盘、工具运行、回答反馈或项目级检索设置。
- 第一片实现保持本地个人应用边界，不引入多用户、权限、分享或云同步。

## 3. 非目标

- 不设计团队协作、多用户权限或共享会话。
- 不设计跨项目会话。
- 不改变当前 RAG 检索、embedding、LLM provider 或工具调用权限边界。
- 不把会话做成 Agent 记忆系统；会话只约束最近上下文读取范围。
- 不在 B-107 阶段建表、迁移数据或改接口。

## 4. 数据模型建议

后续 B-108 可新增 `chat_sessions` 表：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | TEXT PRIMARY KEY | 会话 ID |
| `project_id` | TEXT NOT NULL | 所属项目空间 |
| `title` | TEXT NOT NULL | 会话标题，默认可由首个问题截断生成 |
| `created_at` | TEXT NOT NULL | 创建时间 |
| `updated_at` | TEXT NOT NULL | 最近消息或改名时间 |

后续可在 `chat_messages` 增加可空字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `session_id` | TEXT NULL | 所属聊天会话；旧消息为空 |

兼容策略：

- `session_id IS NULL` 的旧消息归入“默认会话”。
- 新建项目可以自动创建一个默认会话，也可以在首次提问时懒创建。
- 删除项目时继续通过外键级联清理会话和消息。
- 删除会话时删除该会话下的消息；`answer_feedback` 通过 `message_id` 级联清理。
- 旧的 `GET /api/chat/messages?project_id=...` 可保留兼容行为，默认读取默认会话或未指定会话的消息。

## 5. API 设计建议

B-108 第一片建议新增以下接口：

| 方法 | 路径 | 请求 | 成功响应 | 说明 |
|------|------|------|----------|------|
| GET | `/api/chat/sessions?project_id=...` | query `project_id` | `{"sessions":[...]}` | 列出当前项目会话 |
| POST | `/api/chat/sessions` | `project_id`、`title`（可选） | `{"session":...}` | 新建会话 |
| POST | `/api/chat/sessions/rename` | `session_id`、`title` | `{"session":...}` | 会话改名 |
| POST | `/api/chat/sessions/delete` | `session_id` | `{"deleted":true,"sessions":[...]}` | 删除会话及会话消息 |
| GET | `/api/chat/messages?project_id=...&session_id=...` | query | `{"messages":[...]}` | 读取指定会话消息 |
| POST | `/api/answer` | `project_id`、`question`、`session_id`（可选） | 现有响应 + `message.session_id` | 保存回答到指定会话 |

错误边界：

- 缺少 `project_id` 返回 `400 project_id is required`。
- 会话不存在或不属于当前项目返回 `404 chat session not found`。
- `title` 为空时可由后端生成默认标题；显式改名时空标题返回 `400 title is required`。

## 6. 前端交互建议

B-108 第一片建议只做工作台内的轻量会话栏：

- 最近对话上方增加会话选择。
- 支持“新建会话”“改名”“删除”。
- 切换会话后刷新最近对话列表，并清空当前回答反馈状态。
- 提问时带上当前 `session_id`。
- 如果当前项目没有会话，前端显示“默认会话”，并允许直接提问。

不建议第一片做复杂左侧聊天管理器、搜索会话、归档、置顶或跨项目移动，这些会扩大范围。

## 7. 上下文策略

当前真实 LLM 回答会读取同项目最近 3 轮。多会话后改为：

- 有 `session_id`：读取该会话最近 3 轮。
- 没有 `session_id`：读取旧默认流最近 3 轮。
- 工具来源回填 `tool_run_id` 仍然按现有校验：必须同项目、成功、`search_sources`。
- 项目级检索默认值继续按项目生效，不随会话变化。

这样能减少主题串扰，同时不把会话扩展成长期记忆。

## 8. 迁移策略

建议 B-108 采用非破坏迁移：

1. 新增 `chat_sessions` 表。
2. 对 `chat_messages` 增加可空 `session_id` 字段。
3. 不批量改写旧消息。
4. API 读取时把旧消息视为默认会话内容。
5. 用户新建会话后，新消息才写入明确 `session_id`。

这个策略避免大量历史数据迁移，也降低现有聊天记录删除、导出和回答反馈逻辑的破坏风险。

## 9. 测试建议

B-108 实现时至少覆盖：

- 新建、列出、改名、删除会话。
- 会话必须属于当前项目，跨项目访问返回 404。
- `/api/answer` 带 `session_id` 时消息写入对应会话。
- LLM 上下文只读取当前会话最近 3 轮。
- 旧 `session_id IS NULL` 消息仍可读取。
- 删除会话清理该会话消息和对应回答反馈，但不删除文档、检索复盘、工具运行。
- 前端切换会话后刷新消息列表，提问携带当前 `session_id`。

## 10. 风险

- 如果直接把旧 `GET /api/chat/messages` 改成必须传 `session_id`，会破坏现有页面和测试。
- 如果删除会话不处理 `answer_feedback`，会留下孤立反馈；应依赖 `message_id` 外键级联。
- 如果上下文仍按项目读取最近 3 轮，多会话只会变成 UI 分组，不能解决主题串扰。
- 如果第一片加入会话搜索、归档、置顶等能力，会扩大实现面，建议拆到后续 backlog。
