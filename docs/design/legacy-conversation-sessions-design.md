# Legacy 多轮对话设计

> 状态：Implemented
> Owner：RAG 团队
> Last Updated：2026-05-25
> Scope：B-20，记录 legacy `ConversationRecord` / `QueryKnowledgeBaseUseCase` 的会话上下文扩展；数据库字段和应用层上下文注入已落地，桌面端会话管理 UI 尚未实现。

## 1. 背景

当前 Web MVP 已经通过 `chat_sessions` 和 `chat_messages.session_id` 支持多会话聊天，真实 LLM 请求会读取当前会话最近 3 轮上下文。B-20 指向的是 legacy 应用层链路，不应重复改 Web MVP。

legacy 链路由 `ConversationRecord`、`IConversationStore`、`SqliteConversationStore` 和 `QueryKnowledgeBaseUseCase` 组成。B-20 之前每次问答只保存一条单轮记录，`QueryKnowledgeBaseUseCase._build_prompt()` 只拼接检索片段和当前问题，不读取历史问答。B-20 后，legacy 链路按 `session_id` 保存和读取最近 3 轮上下文。

## 2. 设计目标

- 在 legacy 链路中支持按会话隔离的最近上下文。
- 保留旧 `conversations` 数据，不强制迁移历史记录。
- 允许未指定 `session_id` 的旧记录继续作为默认会话读取。
- `execute()` 和 `execute_streaming()` 行为保持一致：都读取同一会话最近上下文，并把新回答保存到同一会话。
- 不影响 Web MVP 的 `chat_sessions` / `chat_messages` 实现。
- 不把 legacy 会话扩展成长期记忆、Agent 状态或跨工作区共享上下文。

## 3. 非目标

- 不新增 Web API，不修改 Web 前端。
- 不设计复杂桌面端会话管理 UI。
- 不做跨 workspace 的会话。
- 不改变检索器、embedding、LLM provider 或模型配置逻辑。
- 不自动总结历史，也不把全部历史发送给 LLM。
- 不新增桌面端会话管理 UI；当前只支持调用方通过 `QueryRequest.session_id` 传入会话。

## 4. 数据模型

`ConversationRecord` 已增加字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `session_id` | `str` | legacy 会话 ID；空字符串表示默认会话 |

兼容策略：

- `ConversationRecord.create()` 增加可选 `session_id: str = ""`。
- `to_dict()` / `from_dict()` 读写 `session_id`，读取旧字典时默认空字符串。
- `conversations` 表增加 `session_id TEXT NOT NULL DEFAULT ''`。
- 旧数据库通过 `_ensure_columns()` 补列，不批量改写旧记录。
- 旧记录的空 `session_id` 归入默认会话。

## 5. 存储接口

`IConversationStore.list_recent()` 已扩展为：

```python
def list_recent(
    self,
    workspace_id: str,
    limit: int = 20,
    session_id: str = "",
) -> list[ConversationRecord]:
    ...
```

行为约定：

- 默认 `session_id=""` 时只读取默认会话记录，兼容旧调用方。
- 指定 `session_id` 时只读取同一 workspace 下该会话记录。
- 查询结果继续按 `created_at DESC` 返回，调用方需要注入 prompt 时再按时间正序拼接。
- `delete_by_workspace()` 继续删除整个 workspace 的所有会话记录。

SQLite 实现：

- `save()` 插入 `session_id`。
- `list_recent()` 增加 `WHERE workspace_id = ? AND session_id = ?`。
- 为查询性能增加索引 `idx_conversations_workspace_session_created`，字段为 `(workspace_id, session_id, created_at)`。

## 6. 用例层

`QueryRequest` 已增加：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `session_id` | `str` | `""` | 当前 legacy 会话 ID；空值表示默认会话 |

`QueryKnowledgeBaseUseCase.execute()` 和 `execute_streaming()` 流程：

1. 按现有逻辑检索当前问题的来源片段。
2. 从 `conversation_store.list_recent(workspace_id, limit=3, session_id=request.session_id)` 读取同会话最近 3 轮。
3. 构造 prompt 时把历史问答作为“最近对话”放在参考资料之后、当前问题之前。
4. 调用 LLM。
5. 用同一个 `session_id` 保存新的 `ConversationRecord`。

上下文格式复用 Web MVP 的简洁结构：

```text
最近对话：
用户：...
助手：...

用户：...
助手：...
```

如果没有历史记录，则不输出“最近对话”段，保持当前 prompt 简洁。

## 7. 桌面端边界

第一片实现可以不新增桌面 UI。调用方可以继续不传 `session_id`，这样所有 legacy 问答仍落在默认会话。

如果后续要加桌面端会话选择，建议拆新 backlog：

- 创建/切换 legacy 会话。
- 展示当前会话历史。
- 删除或重命名会话。

这些 UI 能力不属于 B-20 最小实现。

## 8. 测试建议

当前实现已覆盖：

- `ConversationRecord.create()` 默认 `session_id=""`，显式传入时可序列化和反序列化。
- `SqliteConversationStore.save()` 能保存 `session_id`。
- `list_recent(workspace_id, session_id=...)` 只返回同一 workspace、同一 session 的记录。
- `QueryKnowledgeBaseUseCase.execute()` 只把当前 session 最近 3 轮注入 prompt。
- 不同 session 的问题不会进入彼此 prompt。
- `execute_streaming()` 和 `execute()` 使用同样的 session 读取与保存规则。
- 旧调用方不传 `session_id` 时仍能读写默认会话。
- 旧数据库初始化后会自动补 `session_id` 列。

## 9. 文档同步

B-20 实现后已同步：

- `docs/design/database-design.md`：记录 legacy `conversations.session_id` 字段和索引。
- `docs/design/architecture-overview.md`：说明 legacy `QueryKnowledgeBaseUseCase` 的上下文读取边界。
- `docs/BACKLOG.md`、`docs/DEVLOG.md`、`CHANGELOG.md`：记录实现状态。

## 10. 风险

- 如果 `list_recent()` 仍按 workspace 读取所有历史，多会话只会保存字段，不能解决上下文串扰。
- 如果默认读取所有 `session_id`，旧调用方可能把其他会话上下文带入 LLM。
- 如果一次注入过多历史，会增加 prompt 长度和模型成本；当前固定最近 3 轮。
- 如果直接复用 Web MVP 的 `chat_sessions` 表，会把 Web 本地项目聊天和 legacy workspace 问答耦合在一起，不建议这样做。
