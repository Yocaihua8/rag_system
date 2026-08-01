# 安全与合规规范

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：本地、Docker、桌面、插件、凭证与供应链边界
> Related：`../../SECURITY.md`、`../architecture/contracts/permissions.md`、`../architecture/decisions/ADR-004-api-key-reference.md`

## 1. 默认边界

- FastAPI 默认只监听 `127.0.0.1:8765`；前端端口与 API 端口独立。
- 认证默认关闭。远程访问、Docker 端口映射或反向代理会扩大攻击面，必须显式启用认证、TLS 和网络控制。
- CORS 是浏览器限制，不是身份认证。`KI_CORS_ORIGINS` 使用精确 Origin，不接受 `*`，不启用 cookie credentials。
- `/api/health` 只证明进程活性。

## 2. 凭证

- Key、Token、密码只放操作系统环境或未提交的 `backend/.env` / `ops/docker/.env`。
- 模型 Profile 只持久化 `env:*` / `saved:*` 引用，接口不得返回明文。
- `VITE_API_BASE_URL` 会进入公开前端构建，禁止包含凭证。
- 日志、测试输出、Issue、PR 和截图不得暴露凭证或真实敏感项目内容。

## 3. 权限不变量

- Agent 工具只允许硬编码只读白名单，不执行 shell 或任意写入。
- 当前 API Key/JWT 是单实例共享认证，不代表用户、团队、租户或 RBAC。
- `backend/routes/` 不直接访问 SQLite；资源按 `project_id` 校验。
- Obsidian 插件 token 只用于插件专用路由；发布必须经过预览、确认、路径/托管标记/revision/hash 校验，冲突不覆盖。
- Tauri CSP 不得放宽任意 `connect-src`；sidecar 继续绑定 loopback。

## 4. 数据

- v2 启动拒绝把未标记的非空旧数据库当作 v2 写入。
- `runtime/`、用户 `.env`、导入资料和容器 volume 不属于源码清理范围。
- 删除或恢复数据前验证绝对目标、运行进程、备份可读性和兼容性；默认不执行递归删除或 `docker compose down -v`。

## 5. 依赖审计

```powershell
npm audit --audit-level=high
.\.venv\Scripts\pip-audit.exe -r backend/requirements/dev.txt --progress-spinner off
npm --prefix integrations/obsidian-plugin audit --audit-level=high
```

根 npm 审计覆盖 frontend 与 src-tauri workspace；插件独立审计。只引用本次实际结果。

## 6. 安全变更

认证、CORS、权限、Agent 白名单、数据代际、插件令牌、发布写入或外部网络策略变化时，同步：

- `docs/architecture/contracts/permissions.md`
- `docs/architecture/backend/api.md`
- 本文件和根 `SECURITY.md`
- 必要 ADR、相关测试和 `CHANGELOG.md`
