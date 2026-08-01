# 对话分支与历史消息编辑重发

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：从历史问题创建新分支并保留原消息
> Related：`retrieval-and-question-answering.md`、`../design/api-spec.md`、`../design/database-design.md`

## 1. 当前可达

- 用户可从教练工作台的历史消息发起“编辑重发”。
- 前端预填原问题，确认后通过普通或 SSE 问答链路提交新问题。
- 系统保留原消息和回答，新消息记录 `parent_message_id`；同一父消息下按创建顺序分配 `branch_index`。
- 成功后刷新当前会话，原分支不会被覆盖或删除。

## 2. 校验

- `POST /api/answer` 和 `GET /api/answer/stream` 接受可选 `parent_message_id`。
- 父消息必须属于当前项目和当前会话；不存在或跨边界时返回 `404 parent chat message not found`，不写入新消息。
- 未传父消息时保持普通问答行为，分支字段使用兼容默认值。
- SSE `done` 负载与非流式回答一样包含最终消息分支字段。

## 3. 边界

当前不删除、折叠或合并分支，不提供跨设备会话同步，也不把问答规则放在前端。
