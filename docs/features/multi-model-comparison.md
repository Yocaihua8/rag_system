# 多模型并排对比

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-06-29
> 关联 BACKLOG：B-135

## 1. 功能目标

在同一项目空间、同一问题和同一检索上下文下，同时调用 2 个不同模型 Profile，返回可并排查看的回答结果，帮助用户比较不同模型在本地知识库问答中的质量、速度和来源遵循情况。

## 2. MVP 范围

- 只支持一次选择 2 个 Model Profile。
- 复用现有 `/api/answer` 的检索、Prompt 预设、最近对话和工具来源上下文。
- 返回两个回答结果、共用来源列表、来源质量和基础观测信息。
- 不保存为正式聊天消息，避免把一次对比写成两条主线回答。
- 不返回 API Key 明文、掩码或敏感配置。
- 前端入口位于 Vue 工作台，独立于现有流式聊天区。

## 3. 边界

- 不新增数据库表。
- 不修改模型 Profile 的保存格式。
- 不改变现有 `/api/answer` 与 `/api/answer/stream` 行为。
- 不支持超过 2 个模型、批量评测或自动胜负评分。
- 不自动写入 `chat_messages`，因此对比结果暂不参与回答反馈和会话分支。

## 4. 前端入口

Vue 工作台在问答区域提供并排对比入口，用户从已保存的 Model Profile 中选择两个 Profile 后提交同一问题。对比结果以两个结果列展示，每列显示 Profile 名称、模型、provider、mode、warning 和回答正文。

面板会复用当前项目空间、当前工具来源上下文和服务端默认 Prompt 预设。若当前项目可用 Model Profile 少于 2 个，前端提示用户先到设置页创建 Profile。

## 5. 接口

接口契约见 `docs/design/api-spec.md` 的 `/api/answer/compare` 小节。

核心响应字段：

| 字段 | 说明 |
|------|------|
| `question` | 本次对比的问题 |
| `results` | 两个 Profile 的回答数组，包含 `profile_id/profile_name/profile_provider/model/answer/mode/provider/warning` |
| `sources` | 本轮共用来源片段，最多返回前 5 条 |
| `source_quality` | 共用来源质量摘要 |
| `pipeline_trace` | 共用检索管线状态 |
| `observability.model_comparison` | Profile 数量、ID 和模型名 |

错误边界：

| 场景 | 响应 |
|------|------|
| `profile_ids` 不是两个 ID | `400 profile_ids must contain exactly 2 model profile ids` |
| 两个 Profile ID 相同 | `400 profile_ids must contain 2 different model profile ids` |
| Profile 不存在 | `404 model profile not found` |
| 工具上下文不可用 | `400 tool context is not available` |
