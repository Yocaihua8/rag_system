# 多模型并排对比

> 状态：Draft
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

## 3. 边界

- 不新增数据库表。
- 不修改模型 Profile 的保存格式。
- 不改变现有 `/api/answer` 与 `/api/answer/stream` 行为。
- 不支持超过 2 个模型、批量评测或自动胜负评分。

## 4. 前端入口

Vue 工作台在问答区域提供并排对比入口，用户从已保存的 Model Profile 中选择两个 Profile 后提交同一问题。对比结果以两个结果列展示，每列显示 Profile 名称、模型、provider、mode、warning 和回答正文。

## 5. 接口

接口契约见 `docs/design/api-spec.md` 的 `/api/answer/compare` 小节。

