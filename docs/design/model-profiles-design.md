# Web 模型 Profile 多配置设计

> 状态：Design
> Owner：RAG 团队
> Last Updated：2026-05-24
> Scope：B-111，仅设计多 provider / 多模型配置的数据结构、接口和安全边界；本文件不代表已建表或已实现 UI。

## 1. 背景

当前 Web MVP 的模型设置仍是全局单配置：`GET/POST /api/settings/llm` 读取或写入 `provider / api_base / model / api_key`，底层由配置层合并 OS 环境变量、Windows 持久环境变量、appdata `.env`、项目 `.env` 和默认值。该方案适合首次使用，但当用户需要在 DeepSeek、OpenAI-compatible、本地 Ollama 或不同模型之间切换时，只能反复覆盖同一组配置。

B-110 已把 Prompt 预设和模型配置分离：Prompt 控制回答风格和结构，不保存 API Key、不改变 provider。B-111 的目标是在不破坏现有单配置行为的前提下，先设计“模型 Profile”多配置能力，为 B-112 实现做约束。

## 2. 设计目标

- 支持保存多个模型 Profile，例如“DeepSeek 默认”“OpenAI 轻量模型”“本地 Ollama”。
- 支持选择一个全局默认 Profile，供 `/api/answer` 和设置页连接测试使用。
- Profile 保存 provider、API Base、模型名、温度、最大输出 tokens 等非敏感配置。
- 不在 SQLite、导出文件、前端响应或日志中保存 API Key 明文。
- 兼容当前单配置：未创建 Profile 时继续使用现有 `load_settings()` 行为。
- 为后续 Embedding Profile 留出口，但 B-112 第一片只建议覆盖 LLM Profile。

## 3. 非目标

- 不做团队级共享、云同步、插件市场或第三方 Profile 导入。
- 不把 Prompt 预设和模型 Profile 合并；Prompt 仍由 `prompt_presets` 管理。
- 不让 Profile 改变检索参数；检索参数继续由项目级检索默认值负责。
- 不在 B-111 建表、改接口实现或改变当前 `.env` 写入逻辑。
- 不把 API Key 明文存入 `model_profiles` 表；如必须保存 Key，只允许沿用当前 appdata `.env` 或后续受控凭证引用方案。

## 4. 数据模型建议

B-112 可新增 `model_profiles` 表：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | TEXT PRIMARY KEY | Profile ID |
| `name` | TEXT NOT NULL | 用户可读名称 |
| `provider` | TEXT NOT NULL | `api / ollama`；后续可扩展 |
| `api_base` | TEXT NOT NULL DEFAULT '' | OpenAI-compatible API Base；Ollama 可为空或保存 host |
| `model` | TEXT NOT NULL | 聊天模型名 |
| `temperature` | REAL NOT NULL DEFAULT 0.7 | 生成温度 |
| `max_tokens` | INTEGER NOT NULL DEFAULT 2048 | 最大输出 tokens |
| `api_key_ref` | TEXT NOT NULL DEFAULT '' | 凭证引用，不保存明文 |
| `is_default` | INTEGER NOT NULL DEFAULT 0 | 是否全局默认 |
| `created_at` | TEXT NOT NULL | 创建时间 |
| `updated_at` | TEXT NOT NULL | 更新时间 |

约束建议：

- 同一时间最多一个 `is_default=1`；SQLite 可由事务更新保证，不强依赖复杂 partial index。
- `name` 建议在本地唯一，第一片可后端校验空值，暂不做复杂重名限制。
- `api_key_ref` 只允许保存引用名，例如 `env:RAG_LLM_API_KEY`、`env:DEEPSEEK_API_KEY`、`saved:RAG_LLM_API_KEY`；不能保存 Key 值本身。
- 删除默认 Profile 时应清空默认或自动回退到现有 `load_settings()`，不要静默选择另一个 Profile。

后续如要支持 Embedding Profile，建议独立设计 `embedding_profiles` 或在 `model_profiles` 增加 `kind=llm|embedding` 前先评估字段差异。第一片不要把聊天模型和 embedding 模型塞进同一表，避免 Key、端点和测试语义混乱。

## 5. API 设计建议

B-112 第一片建议新增以下接口：

| 方法 | 路径 | 请求 | 成功响应 | 说明 |
|------|------|------|----------|------|
| GET | `/api/model-profiles` | N/A | `{"profiles":[...],"default_profile_id":"..."}` | 列出本地 LLM Profile |
| POST | `/api/model-profiles` | `name/provider/api_base/model/temperature/max_tokens/api_key_ref` | `{"profile":...}` | 新增 Profile |
| POST | `/api/model-profiles/update` | `profile_id` 和字段 | `{"profile":...}` | 更新 Profile |
| POST | `/api/model-profiles/delete` | `profile_id` | `{"deleted":true,"profiles":[...]}` | 删除 Profile |
| POST | `/api/model-profiles/default` | `profile_id`（可空） | `{"default_profile_id":"..."}` | 设置或清空默认 Profile |
| POST | `/api/model-profiles/test` | `profile_id` | `{"ok":true,"provider":"...","message":"..."}` | 测试指定 Profile |

错误边界：

- 缺少 `profile_id` 返回 `400 profile_id is required`。
- Profile 不存在返回 `404 model profile not found`。
- `name`、`provider` 或 `model` 为空返回明确 `400`。
- `provider=api` 且没有可解析的 API Key 引用时，测试接口返回 `400 LLM provider is not configured`。
- 响应中只返回 `has_api_key`、`api_key_ref`、`api_key_source` 这类状态，不返回 Key 明文或掩码。

## 6. 配置解析策略

建议 B-112 保持三层兼容：

1. 如果存在默认 Model Profile，则 `/api/answer` 和连接测试优先使用该 Profile 的非敏感配置，并通过 `api_key_ref` 解析 Key。
2. 如果没有默认 Profile，则继续使用当前 `load_settings()` 单配置行为。
3. 如果 Profile 测试失败，不自动覆盖旧配置、不自动切换默认 Profile，只返回错误。

`api_key_ref` 解析建议：

| 引用格式 | 说明 |
|----------|------|
| `env:RAG_LLM_API_KEY` | 从 OS 环境变量 / Windows 持久环境变量读取 |
| `env:DEEPSEEK_API_KEY` | 兼容已有 DeepSeek Key 别名 |
| `saved:RAG_LLM_API_KEY` | 沿用当前 appdata `.env` 中保存的 Key |
| 空字符串 | 没有 Key；Ollama 或本地 provider 可允许为空 |

第一片不要设计任意环境变量名输入；前端可以提供有限选项，避免用户误把 Key 值填进引用字段。

## 7. 前端交互建议

B-112 第一片建议仍放在设置页的“模型设置”附近：

- 保留当前单配置表单作为兼容区，或在没有 Profile 时显示当前配置摘要。
- 新增“模型 Profile”列表，展示名称、provider、API Base、模型名、Key 状态、是否默认。
- 支持新增、编辑、删除、设为默认、清空默认、测试连接。
- API Key 输入仍使用当前模式：只允许写入受控保存位置，不回显明文；Profile 只保存引用。
- 提问区或问答观测中可展示当前使用的 Profile 名称，第一片可只在设置页展示。

第一片不建议做 Profile 导入导出、批量测试、模型测速、价格统计、token 用量统计或 provider 市场。

## 8. 与现有能力的关系

- 与 B-110 Prompt 预设：Prompt 负责回答风格，Model Profile 负责模型连接，两者互不包含。
- 与 B-105 项目级检索默认值：Profile 不改变 `top_k/min_score/use_keyword/use_vector`。
- 与 B-108 多会话：默认 Profile 先按全局保存，不随会话切换；后续可设计项目级或会话级覆盖。
- 与备份导出：可导出 Profile 非敏感元数据和 `api_key_ref`，不能导出 API Key 明文或掩码。
- 与 Docker：Docker 仍优先支持环境变量注入；Profile 只引用这些环境变量，不要求容器内新增密钥存储。

## 9. 测试建议

B-112 实现时至少覆盖：

- Profile 新增、列表、更新、删除。
- 默认 Profile 设置和清空。
- 默认 Profile 存在时 `/api/answer` 使用 Profile 的 provider/base/model。
- 没有默认 Profile 时保持当前 `load_settings()` 行为。
- `api_key_ref` 只解析允许的引用，不把 Key 明文写入 SQLite、响应、导出或测试断言快照。
- 连接测试可测试指定 Profile，失败不改变默认配置。
- 前端能创建、编辑、删除、设为默认、测试连接，并不回显 API Key。
- 文档契约覆盖接口、数据库字段和 Key 安全边界。

## 10. 风险

- 如果 Profile 表保存 API Key 明文，会破坏当前安全边界，也会影响备份导出。
- 如果默认 Profile 直接覆盖 appdata `.env`，会导致“测试一个配置”变成全局改配置，回滚困难。
- 如果把 LLM Profile 与 Embedding Profile 过早合并，字段和测试语义会变复杂。
- 如果把 Profile 默认值做成项目级或会话级第一片，会和现有 Prompt、多会话、检索设置同时耦合，建议后续再拆分设计。
