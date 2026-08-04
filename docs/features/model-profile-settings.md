# 模型配置

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：LLM Profile 的保存、默认选择、连接测试与凭证引用
> Related：`multi-model-comparison.md`、`prompt-preset-settings.md`、`../design/api-spec.md`、`../guides/security.md`

本规格描述当前 Vue/v2 入口的 Profile 行为。平行 React/v3 的独立 Profile 元数据管理见 `model-profile-settings-v3.md`；两者不共享 SQLite、默认值或密钥解析链。

## 1. 用户目标

用户在设置页保存多个 LLM Profile，选择默认配置并测试连接，用于普通问答和多模型对比。

## 2. 当前可达

- 设置页支持创建、修改、删除、设为默认、清空默认和测试连接。
- Profile 保存名称、provider、API base、模型和非敏感状态；默认 Profile 优先供问答使用。
- 没有默认 Profile 时，系统继续使用全局环境/本机配置兼容路径。
- 多模型对比可以显式选择两个不同 Profile，不改变全局默认值。

## 3. 凭证边界

- `model_profiles` 只保存 `env:*` 或 `saved:*` Key 引用，不保存或回显 Key 明文。
- 连接测试失败不会自动覆盖旧配置或切换默认 Profile。
- 兼容接口 `POST /api/settings/llm` 仍会把用户输入 Key 写入用户应用数据目录的 `.env`；这是与 Profile 引用不同的本机兼容路径，使用者应限制文件权限。
- 任意 Profile/API 响应不得返回 Key 明文或掩码值。

## 4. 边界

- 当前 Profile 只描述聊天 LLM，不是 Embedding Profile。
- Profile 不改变检索参数或 Prompt 预设。
- 当前没有 Profile 导入导出、价格统计、用量统计或自动测速。
