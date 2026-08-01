# ADR-004 模型 Profile 的 API Key 只保存引用

> 状态：Accepted
> Date：2026-05-26
> Owner：RAG 团队
> Scope：模型 Profile、SQLite 与 Profile API 中的 LLM API Key 表示方式
> Related：[权限矩阵](../design/permission-matrix.md)、[模型配置功能](../features/model-profile-settings.md)、[安全指南](../guides/security.md)、[ADR-005](ADR-005-remote-auth.md)

## 1. 背景

Web MVP 需要让模型 Profile（`model_profiles` 表）引用 LLM API Key，以便用户配置多个 LLM 服务（DeepSeek、OpenAI-compatible API、Ollama）。本决策只约束模型 Profile、SQLite 中的 `api_key_ref` 和 Profile API 响应，不代表系统内所有凭据来源都不落盘。

直接将 API Key 明文存入 SQLite 数据库存在以下风险：

1. **数据库文件泄露**：`runtime/v2/app.db` 是普通文件，若用户误分享、备份上传或操作系统漏洞导致文件泄露，明文 Key 立即失效并造成计费损失
2. **日志 / 备份中的 Key 泄露**：数据库导出、调试日志、API 响应中若携带 Key 明文，难以完全管控
3. **跨 Profile 重复存储**：多个 Profile 使用同一 Key 时，修改 Key 需更新多条记录，容易漏更新

## 2. 决策结论

模型 Profile 的 `api_key_ref` 字段只存储**引用字符串**，不存储明文 Key。引用在 `backend/domain/model_profiles.py` 的 `resolve_api_key_ref()` 函数中于**运行时解析**。

允许的引用值（`ALLOWED_API_KEY_REFS` 硬编码白名单）：

| 引用值 | 解析来源 |
|--------|----------|
| `""` | 无 Key（Ollama 本地或公开端点）|
| `"env:RAG_LLM_API_KEY"` | 环境变量 `RAG_LLM_API_KEY` |
| `"env:DEEPSEEK_API_KEY"` | 环境变量 `DEEPSEEK_API_KEY`（含别名 `DEEPSEEK_APIKEY` / `deepseekapikey`）|
| `"saved:RAG_LLM_API_KEY"` | 全局设置加载链中的 `RAG_LLM_API_KEY`；兼容保存入口写入用户应用数据 `.env` |

**Profile API 响应不返回 Key 明文**：响应保留白名单引用 `api_key_ref`，并返回 `has_api_key: bool` 和 `api_key_source: str`（`"environment"` / `"saved"` / `""`），告知前端 Key 是否可用及来源类型，不回显具体值。

### 2.1 兼容全局设置的持久化边界

`POST /api/settings/llm` 是独立于模型 Profile 的兼容全局设置入口。用户提交非空 `api_key` 时，`backend/api/settings_handlers.py` 会调用 `save_setting()`，把 `RAG_LLM_API_KEY` 的**明文**写入用户应用数据目录下的 `.env` 文件（Windows 通常为 `%APPDATA%/KnowledgeIsland/.env`；其他平台由 `backend/config/paths.py` 决定）。

因此当前安全边界是：

- `model_profiles.api_key_ref` 和 Profile API 不保存或返回明文；
- `env:*` 在运行时从操作系统环境读取；
- `saved:RAG_LLM_API_KEY` 通过全局设置加载链解析，兼容入口可能依赖用户应用数据 `.env` 中的明文；
- 全局设置 API 只返回 `has_api_key` 与 `api_key_source`，不回显明文，但本地 `.env` 仍应按敏感配置文件保护并排除版本控制、日志和普通备份共享。

ADR-005 的服务级认证 Key 使用 `RAG_AUTH_*` 环境变量，不写入 `model_profiles`，也不由本决策定义其持久化方式。

## 3. 决策原因

1. **避免凭据进入业务数据库**：Profile 只保存受控引用，数据库备份不会因模型 Profile 记录而附带 LLM Key 明文
2. **单点维护**：用户修改环境变量或兼容全局设置后，所有引用该来源的 Profile 自动生效，无需逐条更新
3. **引用白名单防注入**：`ALLOWED_API_KEY_REFS` 硬编码，非白名单值被 `model_profile_validation_error()` 在写入前拒绝，不存在通过 API 注入任意表达式（如 `env:PATH`、`file:/etc/passwd`）的路径
4. **与数据库设计正交**：`api_key_ref` 是普通 `TEXT` 字段，不需要 SQLite 加密扩展；Key 安全由应用层保证，不依赖存储层特性
5. **兼容 Docker 部署**：Docker Compose 可通过运行时环境注入 Key，与 `env:*` 引用对齐；Compose 文件不应写入真实 Key

## 4. 备选方案

### 4.1 方案 A：明文存储于 SQLite

- 优点：实现最简，无运行时解析逻辑
- 缺点：数据库文件即包含 Key 明文；备份文件需保密处理；API 响应容易意外带出 Key
- 未采用原因：与"数据库文件是普通本地文件"的事实冲突，泄露风险不可接受

### 4.2 方案 B：SQLite 加密（SQLCipher）

- 优点：数据库文件本身加密，Key 可存明文
- 缺点：引入非标准 SQLite 扩展；需管理主密钥（如何安全存储主密钥是同样的问题，问题后移而非解决）；跨平台兼容性复杂
- 未采用原因：引入依赖且未解决根本问题（主密钥的安全存储）；引用方案更简单且同样安全

### 4.3 方案 C：操作系统 Keychain / Secret Store

- 优点：使用 OS 提供的加密存储，安全性最高
- 缺点：跨平台 API 不统一（macOS Keychain、Windows DPAPI、Linux libsecret）；Docker 容器环境无 Keychain；需引入 `keyring` 等依赖
- 未采用原因：Docker 不兼容；跨平台实现复杂度高；对本地单用户场景收益不成比例

### 4.4 方案 D：对称加密存储（AES + 本地主密钥文件）

- 优点：Key 在数据库中为密文
- 缺点：主密钥文件与数据库文件通常在同一目录，同时泄露时等价于明文；密钥轮换复杂
- 未采用原因：安全性提升有限，复杂度增加明显；引用方案更简洁

## 5. 影响

### 5.1 正面影响

- 模型 Profile 不会把 LLM Key 明文写入 SQLite；数据库仍包含知识库与其他敏感业务数据，不能按公开文件处理
- Profile 与兼容全局设置 API 都不回显 Key 明文，降低浏览器缓存或日志误收集风险
- 多 Profile 共享同一 Key 时，Key 更新一次全局生效

### 5.2 负面影响

- **本地明文配置**：兼容全局设置允许用户在 UI 输入 Key，并将非空值写入用户应用数据 `.env`；它不进入 SQLite，但该文件本身必须按凭据文件保护
- **来源语义复杂**：Profile 只选择引用，`saved:RAG_LLM_API_KEY` 的实际值由全局设置加载链提供，维护者需区分 Profile 记录与全局配置文件
- **引用白名单限制扩展**：新增 Key 来源（如第三方 Vault、OS Keychain）需修改 `ALLOWED_API_KEY_REFS` 和 `resolve_api_key_ref()` 源码

### 5.3 对现有系统的改动点

| 模块 | 内容 |
|------|------|
| `backend/domain/model_profiles.py` | `ALLOWED_API_KEY_REFS` 白名单；`resolve_api_key_ref()` 运行时解析；`model_profile_payload()` 返回引用及 `has_api_key / api_key_source`，不返回明文 |
| `backend/domain/models.py` | `ModelProfile.api_key_ref` 字段（`TEXT`，默认 `""`）|
| `backend/storage/knowledge_store.py` | `model_profiles` 表 `api_key_ref TEXT NOT NULL DEFAULT ''`；写入前通过 `model_profile_validation_error()` 校验引用合法性 |
| `frontend/src/api/settings.js`、`frontend/src/views/SettingsView.vue` | 提交白名单引用并展示来源/可用状态，不回填 Key 明文 |
| `backend/api/settings_handlers.py` | 兼容全局设置保存非空 `api_key` 时调用 `save_setting()` |
| `backend/config/settings.py` | 从环境与配置文件加载全局设置，并将用户提交值写入应用数据 `.env` |

## 6. 后续动作

### 6.1 已完成

- `backend/domain/model_profiles.py`：`ALLOWED_API_KEY_REFS` + `resolve_api_key_ref()` + `model_profile_payload()`
- `backend/storage/knowledge_store.py`：`model_profiles` 表 schema 含 `api_key_ref` 字段
- ADR-005：认证中间件使用独立的 `RAG_AUTH_*` 环境变量；不复用模型 Profile 引用

### 6.2 未来扩展条件

新增 Key 来源需同时修改：
1. `ALLOWED_API_KEY_REFS`（白名单追加）
2. `resolve_api_key_ref()`（解析逻辑）
3. 对应文档（`backend/.env.example`、[`docs/guides/setup.md`](../guides/setup.md)、[`docs/guides/security.md`](../guides/security.md)）

### 6.3 回滚策略

N/A —— Profile 引用模式是向前兼容设计。若未来改变 Profile 的凭据存储方式，必须另行评估数据库备份、API 回显、日志脱敏、密钥迁移与回滚，不把裸 Key 作为普通 `api_key_ref` 接受。
