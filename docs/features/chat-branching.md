# 对话分支与历史消息编辑重发

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-06-28
> Scope：B-128 对话分支与历史消息编辑重发
> Related：docs/design/new-architecture-design.md §5.5.3, docs/design/api-spec.md, docs/design/database-design.md

## 1. 功能定位

B-128 让用户可以在 Vue 工作台中编辑某条历史聊天消息并重新提问。系统保留原消息，生成一条新的聊天消息作为分支，不删除原会话记录。

本功能仍属于本地 Web MVP 的聊天体验增强，不引入远程同步、多用户协作或完整 Agent 记忆。

## 2. 用户可见行为

- 用户可在历史消息上点击“编辑重发”。
- Vue 工作台会用原问题预填编辑框；用户确认后，前端把编辑后的问题作为新问题提交。
- 提交编辑后的问题后，系统复用当前问答链路生成新回答。
- 新生成的消息记录会带上被编辑消息的 `parent_message_id`。
- 同一个父消息下的分支按创建顺序写入 `branch_index`，第一条主线/默认消息为 `0`，后续分支递增。
- 原消息、原回答和其他会话消息不会被覆盖或删除。

## 3. 非目标

- 不删除或自动折叠旧分支。
- 不实现跨设备会话同步。
- 不改变 Agent 工具权限边界。
- 不把问答业务规则写入前端。

## 4. 架构落点

- `webapp/storage.py` 负责 `chat_messages` 分支字段的持久化、迁移和读取。
- `webapp/answer_api.py` 负责校验被编辑的父消息属于当前项目和当前会话，并把分支元数据传给存储层。
- `webapp/api.py` 在 SSE 问答入口透传 query `parent_message_id`。
- `frontend/src/api/answer.js` 在非流式和 SSE 问答 helper 中透传 `parentMessageId`。
- Vue 工作台只负责展示历史消息编辑入口、提交编辑后的问题和刷新当前会话消息。

## 5. 接口与数据

- `POST /api/answer` 支持可选 `parent_message_id`。
- `GET /api/answer/stream` 支持可选 query `parent_message_id`。
- 父消息不存在、跨项目或跨会话时，返回 `404 {"error":"parent chat message not found"}`。
- 成功响应中的 `message` 包含 `parent_message_id` 和 `branch_index`。
- 旧消息和普通新问答保持 `parent_message_id=""`、`branch_index=0`。

## 6. 验收标准

- 未传 `parent_message_id` 时，现有问答和聊天历史行为保持兼容。
- 传入同项目同会话的 `parent_message_id` 时，问答成功响应中的 `message` 包含该父消息 ID 和正确 `branch_index`。
- 传入不存在、跨项目或跨会话的 `parent_message_id` 时，接口返回明确错误，不写入新消息。
- SSE 问答完成后的 `done` 负载与非流式问答保持一致，包含分支消息字段。
- Vue 工作台可以从历史消息发起编辑重发，并在成功后刷新当前会话消息。
