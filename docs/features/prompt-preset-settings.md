# Prompt 预设

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：项目级回答指令与输出格式预设
> Related：`retrieval-and-question-answering.md`、`model-profile-settings.md`、`../design/api-spec.md`

## 1. 用户目标

用户为每个项目保存回答风格或任务边界，并选择一个默认 Prompt 预设用于后续问答。

## 2. 当前可达

- 设置页支持列出、创建、修改、删除预设，以及设置或清空项目默认预设。
- 预设包含名称、系统指令和回答格式；未选择默认预设时沿用系统默认回答逻辑。
- 问答组合当前项目的默认预设、最近会话、检索来源和本轮问题。

## 3. 约束

- Prompt 不能扩大 Agent 工具白名单，不能触发 shell，也不能绕过来源与项目隔离。
- Prompt 预设不改变 `top_k`、最低分、关键词/向量开关等检索参数。
- 默认值按项目保存，不随单个会话自动切换。
- 当前无富文本变量编辑器、版本历史、导入导出或 Prompt 市场。
