# 安全与合规规范

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：网络、认证、凭证、数据、插件与供应链边界
> Related：`../../SECURITY.md`、`../design/permission-matrix.md`、`../adr/ADR-004-api-key-reference.md`、`../adr/ADR-005-remote-auth.md`、`../adr/ADR-011-interactive-learning-sql-sandbox.md`

## 1. 网络与认证

- FastAPI 默认监听 `127.0.0.1:8765`；前端端口与 API 端口独立。
- 认证默认关闭。远程访问、Docker 端口映射或反向代理会扩大攻击面，必须另行配置认证、TLS 和网络控制。
- CORS 使用精确 Origin，不接受 `*`，不启用 cookie credentials；CORS 不是身份认证。
- 当前 Vue helper 和原生 EventSource 未接认证凭证，启用后端认证会使浏览器主流程不可用；修复接线前不要把它当作 Vue 登录方案。
- `/api/health` 只证明进程活性，不证明 Provider、数据库恢复或完整业务就绪。

## 2. 凭证

- Key、Token、密码只放操作系统环境或未提交的 `backend/.env`、`ops/docker/.env`。
- Model Profile 只持久化 `env:*`/`saved:*` 引用，普通响应不得返回 Key 明文。
- 兼容接口 `POST /api/settings/llm` 会把用户输入 Key 写入用户应用数据目录的 `.env`；应限制该文件权限并避免纳入备份/日志。
- `VITE_API_BASE_URL` 会进入公开前端构建，禁止包含凭证。
- Obsidian 服务端只保存插件令牌哈希；插件为了离线恢复会在 Vault 的插件 `data.json` 中保存明文令牌，需依赖本机文件权限。
- 日志、测试输出、Issue、PR 和截图不得暴露凭证或真实敏感项目内容。

## 3. 权限边界

- Agent 业务工具白名单只有 `project_overview` 和 `search_sources`，不执行 shell 或业务写操作；每次调用仍会写审计记录，因此“工具只读”不等于数据库完全无写入。
- 当前 API Key/JWT 是单实例共享认证，不代表用户、团队、租户或 RBAC。
- 资源操作按 `project_id` 校验；HTTP 适配层不得绕过存储/领域边界直接操作 SQLite。
- Obsidian 发布必须经过预览、确认、路径、管理标记、revision 和 hash 校验，冲突不覆盖。
- Tauri CSP 不得放宽任意 `connect-src`，sidecar 继续绑定 loopback。
- 公开网页抓取必须保留协议、DNS/IP、重定向、robots 和正文大小限制，不能通过配置绕过内网访问保护。

## 4. 数据

- v2 启动拒绝把未标记的非空旧数据库当作 v2 写入。
- `runtime/`（包括 `runtime/v2/outputs/`）、用户 `.env`、导入资料和容器 volume 不属于源码清理范围。
- 删除或恢复前验证绝对目标、运行进程、备份可读性和兼容性；默认不执行递归删除或删除 Docker volume。

## 5. SQL 练习隔离

- 只有当前知识点真实来源中可解析的简单 SQLite `CREATE TABLE` 证据可触发 SQL 练习。来源 DDL 只转成受校验的表、列、关系和合成行，不直接执行。
- fixture 在持久化时保存完整性 hash。评分模块只接受结构化 fixture 和学习者 SQL，不接受 `KnowledgeStore`、正式数据库连接或数据库路径。
- 每次评分创建独立临时 SQLite 文件，完成 fixture 建库后关闭写连接，再通过 `mode=ro` URI 重开；同时启用 `query_only`、关闭可信 Schema，并拒绝扩展加载。
- 只允许一条 `SELECT` 或非递归 `WITH ... SELECT`。词法检查、SQLite authorizer、表/列/函数白名单和必要语义检查共同拒绝多语句、DML、DDL、`PRAGMA`、`ATTACH/DETACH`、递归 CTE、虚表、Schema 读取和危险函数。
- 单次默认上限为：SQL 10000 字符、1 秒、1000000 VM steps、200 行、32 列、256 KiB 结果、8 张 fixture 表和 1000 条 seed row；fixture 不能自行提高这些绝对上限。
- 评分只信任确定性执行结果和必要语义检查。模型不得推翻结论；语法、安全、超时、结果大小或语义错误都必须返回失败，不能转成已掌握。
- 安全测试必须使用仓库正式运行目录之外的临时 SQLite，并以哨兵或 SHA-256 验证 `runtime/v2/app.db` 未被打开或改写；不得为了测试复用已启动的正式服务。

## 6. 供应链审计

```powershell
npm audit --audit-level=high
.\.venv\Scripts\pip-audit.exe -r backend/requirements/base.txt --progress-spinner off
npm --prefix integrations/obsidian-plugin audit --audit-level=high
```

根 npm 审计覆盖 frontend 与 src-tauri workspace；插件独立审计。Python 生产依赖使用 `base.txt`。只引用本次实际结果。

## 7. 安全变更联动

认证、CORS、权限、Agent 白名单、数据代际、SQL 沙箱、插件令牌、发布写入或外部网络策略变化时，同步 [`../design/permission-matrix.md`](../design/permission-matrix.md)、[`../design/api-spec.md`](../design/api-spec.md)、本文件、根 `SECURITY.md`、必要 ADR、测试和 `CHANGELOG.md`。
