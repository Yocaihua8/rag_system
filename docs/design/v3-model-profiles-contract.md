# v3 模型 Profile 合同

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-03
> Scope：v3 独立模型 Profile 的元数据管理与默认选择
> Related：`agent-runtime-and-tool-contract.md`、`permission-matrix.md`、`../features/model-profile-settings-v3.md`

## 1. HTTP 合同

| 方法 | 路径 | 成功 | 失败 |
|------|------|------|------|
| GET | `/api/v3/model-profiles` | `200`，返回全局 v3 Profile 元数据 | N/A |
| POST | `/api/v3/model-profiles` | `201`，创建 Profile | `409` 重名或幂等冲突；`422` 请求校验失败 |
| POST | `/api/v3/model-profiles/{profile_id}/update` | `200`，全量更新 Profile | `404` 不存在；`409` 重名或幂等冲突；`422` 请求校验失败 |
| POST | `/api/v3/model-profiles/{profile_id}/default` | `200`，设为唯一默认 Profile | `404` 不存在；`409` disabled Profile；`422` 缺幂等键 |
| POST | `/api/v3/model-profiles/{profile_id}/delete` | `200`，删除 Profile | `404` 不存在；`409` 幂等冲突；`422` 缺幂等键 |

所有写请求必须带稳定 `Idempotency-Key`。响应 `ModelProfileResource` 只包含名称、provider、API base、模型、temperature、max tokens、状态、默认标记、时间和 `api_key_ref`；不包含 Key 明文、掩码、可解析值或“是否存在 Key”的探测结果。

## 2. 存储与安全边界

- 只读写独立 v3 SQLite 的既有 `model_profiles` 表；不读取、迁移、回填或修改 v2 `runtime/v2/app.db`、v2 Profile 或用户 `.env`。
- `api_key_ref` 只允许空值、`env:RAG_LLM_API_KEY`、`env:DEEPSEEK_API_KEY`、`saved:RAG_LLM_API_KEY`。接口不接受 `api_key` 字段，不执行环境变量或兼容 `.env` 的解析。
- disabled Profile 不能设为默认；设定新默认值会在同一 Store 事务内取消此前默认，保证最多一个默认 Profile。
- 删除仅删除该 v3 Profile 元数据，不调用 provider、不删环境变量、不写入项目文件或外部系统。React 必须先显示确认步骤。

## 3. 当前不在范围

本切片不把 Profile 接入 Agent Run、任务、模型调用或双模型对比，也不提供连接测试、Key 录入、Profile 导入导出、费用/用量统计。它们须在独立合同、权限和测试完成后才可开放。
