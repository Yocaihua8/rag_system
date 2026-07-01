# ADR-004 API Key 只保存引用，不持久化明文

> 状态：Accepted
> Date：2026-05-26
> Owner：RAG 团队
> Related：`../design/architecture-overview.md §7`、`../features/authentication.md`、`ADR-005-remote-auth.md`

## 1. 背景

Web MVP 需要在模型 Profile（`model_profiles` 表）中记录 LLM API Key，以便用户配置多个 LLM 服务（DeepSeek、OpenAI-compatible API、Ollama）。

直接将 API Key 明文存入 SQLite 数据库存在以下风险：

1. **数据库文件泄露**：`runtime/app.db` 是普通文件，若用户误分享、备份上传或操作系统漏洞导致文件泄露，明文 Key 立即失效并造成计费损失
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
| `"saved:RAG_LLM_API_KEY"` | 本地 settings 文件中保存的 `llm_api_key` 字段 |

**API 响应从不返回 Key 明文**：Profile 响应只包含 `has_api_key: bool` 和 `api_key_source: str`（`"environment"` / `"saved"` / `""`），告知前端当前 Key 是否可用及来源类型，不回显具体值。

## 3. 决策原因

1. **最小化明文暴露面**：Key 明文只在运行时内存中存在（`resolve_api_key_ref()` 调用点），不落盘、不进响应、不进日志
2. **单点维护**：用户修改 Key 只需更新环境变量或 settings 文件，所有引用该 Key 的 Profile 自动生效，无需逐条更新
3. **引用白名单防注入**：`ALLOWED_API_KEY_REFS` 硬编码，非白名单值被 `model_profile_validation_error()` 在写入前拒绝，不存在通过 API 注入任意表达式（如 `env:PATH`、`file:/etc/passwd`）的路径
4. **与数据库设计正交**：`api_key_ref` 是普通 `TEXT` 字段，不需要 SQLite 加密扩展；Key 安全由应用层保证，不依赖存储层特性
5. **兼容 Docker 部署**：Docker Compose 通过 `environment:` 注入 Key，与 `env:*` 引用天然对齐；无需在 compose.yaml 中暴露 Key 到 volume 文件

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

- 数据库文件不含敏感凭据，可相对安全地分享或上传备份（注意：仍包含知识库内容）
- API 响应不回显 Key，前端无法意外缓存或记录明文
- 多 Profile 共享同一 Key 时，Key 更新一次全局生效

### 5.2 负面影响

- **用户体验**：Key 只能通过环境变量或 settings 文件配置，不能直接在 UI 中输入并持久化到数据库；当前 `"saved:RAG_LLM_API_KEY"` 路径将 Key 写入本地 settings 文件（非数据库），位置相对不透明
- **引用白名单限制扩展**：新增 Key 来源（如第三方 Vault、OS Keychain）需修改 `ALLOWED_API_KEY_REFS` 和 `resolve_api_key_ref()` 源码

### 5.3 对现有系统的改动点

| 模块 | 内容 |
|------|------|
| `backend/domain/model_profiles.py` | `ALLOWED_API_KEY_REFS` 白名单；`resolve_api_key_ref()` 运行时解析；`model_profile_payload()` 只返回 `has_api_key / api_key_source` |
| `backend/domain/models.py` | `ModelProfile.api_key_ref` 字段（`TEXT`，默认 `""`）|
| `backend/storage/knowledge_store.py` | `model_profiles` 表 `api_key_ref TEXT NOT NULL DEFAULT ''`；写入前通过 `model_profile_validation_error()` 校验引用合法性 |
| `frontend/src/api/settings.js` | Profile 响应只读取 `has_api_key / api_key_source`，不渲染 Key 明文输入框回填值 |

## 6. 后续动作

### 6.1 已完成

- `backend/domain/model_profiles.py`：`ALLOWED_API_KEY_REFS` + `resolve_api_key_ref()` + `model_profile_payload()`
- `backend/storage/knowledge_store.py`：`model_profiles` 表 schema 含 `api_key_ref` 字段
- B-140（ADR-005）：认证中间件的 API Key（保护 `/api/*` 端点的服务级 Key）遵循同样的"不持久化明文"约束

### 6.2 未来扩展条件

新增 Key 来源需同时修改：
1. `ALLOWED_API_KEY_REFS`（白名单追加）
2. `resolve_api_key_ref()`（解析逻辑）
3. 对应文档（`.env.example`、`docs/guides/setup.md`）

### 6.3 回滚策略

N/A —— 引用模式是向前兼容设计；若需支持明文存储（不推荐），可扩展 `resolve_api_key_ref()` 处理裸字符串，但需同步评估安全影响。
