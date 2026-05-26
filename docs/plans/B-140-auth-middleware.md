# B-140 Auth Middleware Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add optional single-user API Key + JWT authentication to the FastAPI Web MVP without changing the SQLite schema.

**Architecture:** `webapp/auth.py` owns auth settings, API Key comparison, JWT signing, and JWT validation. `webapp/server.py` applies a FastAPI middleware to protected paths and exposes `POST /api/auth/token`; existing `webapp.api.dispatch()` and all business route modules remain compatible.

**Tech Stack:** Python standard library `hmac/hashlib/base64/json/time`, FastAPI middleware and `JSONResponse`, pytest + FastAPI `TestClient`.

---

> 状态：Active
> 创建时间：2026-05-26
> 创建方：Codex
> 关联 BACKLOG：B-140
> 关联功能文档：docs/features/authentication.md
> 关联设计文档：docs/adr/ADR-005-remote-auth.md, docs/design/permission-matrix.md, docs/design/api-spec.md, docs/guides/setup.md, docs/guides/testing.md

## 1. 目标

实现 ADR-005 定义的可选认证层：默认关闭；启用后通过 `X-API-Key` 或 `Authorization: Bearer <jwt>` 访问受保护 API；`/api/health` 与静态页面保持放行；不修改数据库 schema，不新增用户系统。

## 2. 前置条件

- B-139 已完成，`webapp/server.py` 已是 FastAPI app factory。
- 已读取 FastAPI 当前文档：`Depends()` / `Security()` 可用于安全依赖，FastAPI 提供 `fastapi.security` 工具；本任务选择中间件方式以保护兼容分发入口和 `/docs`。
- 已确认 B-140 采用 API Key + 短期 JWT，不做登录页、不做 RBAC、不改数据库。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 补 ADR-005、认证功能文档、B-140 plan，并将 BACKLOG 状态更新为 `doing`
- [x] 先写 `webapp/auth.py` 红灯测试，覆盖认证配置、API Key 校验、JWT 签发与验证
- [x] 实现 `webapp/auth.py` 的最小认证工具函数并通过聚焦测试
- [x] 先写 FastAPI 中间件红灯测试，覆盖默认关闭、启用后 401、API Key 放行、JWT 放行、docs 保护
- [ ] 在 `webapp/server.py` 接入认证中间件和 `POST /api/auth/token`
- [ ] 同步权限矩阵、API 契约、setup/testing、CHANGELOG/devlog
- [ ] 运行 Web MVP 与 legacy 回归验证，修复仅由 B-140 引入的回归
- [ ] 完成回流清单，删除本 plan，并将 B-140 状态改为 `done`

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `webapp/auth.py` | 新增：认证配置、API Key 校验、JWT 签发/验证 |
| 代码 | `webapp/server.py` | 修改：认证中间件与 token 路由 |
| 测试 | `tests/test_webapp/test_auth.py` | 新增：认证工具函数测试 |
| 测试 | `tests/test_webapp/test_auth_middleware.py` | 新增：FastAPI 认证中间件测试 |
| 文档 | `docs/adr/ADR-005-remote-auth.md` | 新增：认证决策记录 |
| 文档 | `docs/features/authentication.md` | 新增：功能边界 |
| 文档 | `docs/design/permission-matrix.md` | 修改：认证启用后的权限矩阵 |
| 文档 | `docs/design/api-spec.md` | 修改：新增认证接口和错误格式 |
| 文档 | `docs/guides/setup.md`, `docs/guides/testing.md` | 修改：认证配置与验证命令 |
| 文档 | `CHANGELOG.md`, `docs/devlog/2026-05-26.md` | 修改：记录 B-140 实施结果 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | B-139 已完成并删除对应 plan；B-140 基于当前 FastAPI server 继续 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| `docs/superpowers/plans/2026-05-11-project-knowledge-base-ui-skeleton.md` | 历史 desktop/UI 文档计划，不触及认证核心文件 | 分区：B-140 只改 Web auth 和对应正式文档 |
| `docs/superpowers/plans/2026-05-11-project-knowledge-points.md` | 历史 src/application 与文档计划，不触及 `webapp/server.py` auth | 分区：B-140 不修改 legacy `src/` |
| `docs/superpowers/plans/2026-05-16-knowledge-island-core-models.md` | 历史 core model/schema 计划 | 分区：B-140 不修改数据库 schema |

## 6. 完成标准

全部勾选后方可删除本 plan 文件：

- [ ] 认证关闭时现有 API 行为不变。
- [ ] 认证启用时受保护 API 无凭证返回 401。
- [ ] 正确 `X-API-Key` 可访问受保护 API。
- [ ] 正确 Bearer JWT 可访问受保护 API。
- [ ] `/api/health` 和静态首页在认证启用时仍可访问。
- [ ] `/docs`、`/redoc`、`/openapi.json` 在认证启用时需要认证。
- [ ] `storage.py` 和数据库 schema 未因 B-140 修改。
- [ ] 测试通过（参照 `docs/guides/testing.md` 最低要求）。
- [ ] 相关文档已同步（见下方"回流清单"）。
- [ ] BACKLOG 条目 `B-140` 状态已更新为 `done`。

## 7. 回流清单

删除本文件前，确认以下内容已写入正式文档：

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 认证决策与回滚方式 | `docs/adr/ADR-005-remote-auth.md` | [x] |
| 认证功能边界和非目标 | `docs/features/authentication.md` | [x] |
| 认证启用后的权限矩阵 | `docs/design/permission-matrix.md` | [ ] |
| 认证接口、错误格式、请求头 | `docs/design/api-spec.md` | [ ] |
| 启用认证的环境变量 | `docs/guides/setup.md` | [ ] |
| B-140 验证命令 | `docs/guides/testing.md` | [ ] |
| 对外变更摘要 | `CHANGELOG.md` | [ ] |
| 实施记录 | `docs/devlog/2026-05-26.md` | [ ] |

## 8. 执行记录

- 2026-05-26 15:45：用户确认 B-140 采用“可选启用的单用户认证：API Key + 短期 JWT，不改数据库 schema，不做登录页”。
- 2026-05-26 15:45：冲突扫描发现 `docs/superpowers/plans/` 下存在历史计划文件，但核心影响范围与 B-140 不重叠；按分区处理。
- 2026-05-26：新增 `tests/test_webapp/test_auth.py` 后红灯失败于缺少 `webapp.auth`，覆盖配置、API Key 和 JWT 目标 API。
- 2026-05-26：新增 `webapp/auth.py`，使用标准库实现认证配置、API Key 常量时间比较和 HMAC-SHA256 JWT。
- 2026-05-26：新增 `tests/test_webapp/test_auth_middleware.py` 后红灯失败于 `create_app()` 尚未支持 `auth_settings`，覆盖认证中间件和 token 路由预期行为。

## 9. 状态快照

- **最后更新**：2026-05-26 15:45
- **进度**：已完成 4 / 8 项（见 § 3 勾选状态）
- **最新 commit**：`f38836e` — feat: 实现认证工具函数
- **代码状态**：分支 `fix/url-virtual-source-preserve`；存在大量既有未提交改动；B-140 将只追加相关变更
- **下一步**：在 `webapp/server.py` 接入认证中间件和 `POST /api/auth/token`
- **续任务须知**：B-140 不新增登录页、不修改数据库 schema、不实现多用户或 RBAC
