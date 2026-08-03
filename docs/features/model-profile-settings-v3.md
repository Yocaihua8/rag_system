# v3 模型配置

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-03
> Scope：平行 React 设置页中的 v3 模型 Profile 元数据管理
> Related：`../design/v3-model-profiles-contract.md`、`model-profile-settings.md`、`agent-tasks-and-runs.md`

## 1. 用户能力

用户可在 React 的“设置 → 模型”中列出、新增、编辑、启用/停用、设为默认和删除 v3 模型 Profile。Profile 显示 provider、模型、状态与受控密钥引用，不提供密钥输入框，也不使用演示 Profile 填充空列表。

## 2. 约束

- 创建、修改、设为默认和删除使用真实 v3 API 与稳定幂等键；删除先显示确认步骤。
- Profile 只保存受控 `api_key_ref`，不保存、显示或测试 API Key；本阶段不调用任何模型或外部 provider。
- v3 Profile 与 v2 的全局 LLM 设置/Profile 数据独立；设置默认值不影响现有 Vue 问答、Tauri/Docker 正式入口或 v2 `.env`。

## 3. 后续边界

连接测试、Key 录入、将默认 Profile 接入 v3 Agent Run、Prompt、检索、双模型对比、导入导出和用量统计均未实现。未开放能力继续显示为不可用，不得由 v2 接口回填。
