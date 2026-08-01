# 多模型并排比较

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：同一项目、问题与来源上下文下的两个 LLM Profile 回答
> Related：`model-profile-settings.md`、`retrieval-and-question-answering.md`、`../design/api-spec.md`

## 1. 当前可达

- 教练工作台高级区域挂载模型比较面板。
- 用户从已保存 Profile 中选择两个不同配置，提交同一问题。
- 两个回答共享一次检索来源和来源质量，界面并排列出 Profile、provider、模型、mode、warning 和回答正文。
- 比较结果不写入正式聊天消息，不参与回答反馈或对话分支。

## 2. 规则

- `POST /api/answer/compare` 只接受两个不同且存在的 `profile_ids`。
- 检索、Prompt 预设、最近对话和只读工具上下文沿用普通问答边界。
- 结果只返回非敏感 Profile 信息，不返回 API Key。
- 比较失败不会更改默认 Profile。

## 3. 边界

当前不支持三个以上模型、批量评测、价格/Token 统计、自动胜负评分或将比较结果保存为聊天消息。
