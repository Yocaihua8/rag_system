# B-136 OpenAPI / Swagger 接口文档 Plan

> 状态：Active
> 创建时间：2026-06-29
> 创建方：Codex
> 关联 BACKLOG：B-136
> 关联功能文档：docs/features/openapi-swagger-docs.md
> 关联设计文档：docs/design/api-spec.md

## 1. 目标

执行 B-136：为当前 Web MVP API 提供 OpenAPI 3.0 schema，让 `/openapi.json` 和 Swagger UI 能展示当前接口清单。因 B-135 同次执行会新增 `/api/answer/compare`，本 plan 的最终 schema 需包含该端点。

## 2. 前置条件

- 已阅读 `AGENTS.md`
- 已阅读 `docs/design/api-spec.md`
- 已通过 ctx7 查询 FastAPI OpenAPI / Swagger UI 当前用法
- 已检查 `webapp/server.py` 当前 FastAPI app、认证中间件和兼容 `/api/{path:path}` 分发方式
- B-135 已完成或至少已稳定新增 `/api/answer/compare` 契约

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。
未完成项不得删除。

- [x] 任务 1：写 B-136 红灯测试，覆盖 `/openapi.json` 的 OpenAPI 版本、显式 API paths、Swagger UI、认证保护和 compare 端点
- [x] 任务 2：实现运行时 OpenAPI schema，补齐兼容分发 API 的 path/summary/request/response 元数据，不改业务路由
- [ ] 任务 3：同步 `docs/features/openapi-swagger-docs.md` 与 `docs/design/api-spec.md`
- [ ] 任务 4：运行 B-136 验证清单，关闭 BACKLOG 状态并删除本 plan

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `webapp/server.py` | 挂载自定义 OpenAPI schema |
| 代码 | `webapp/openapi_schema.py` | 新增 Web MVP API schema 定义 |
| 测试 | `tests/test_webapp/test_fastapi_server.py` | 新增 OpenAPI/Swagger 测试 |
| 测试 | `tests/test_webapp/test_auth_middleware.py` | 补充 OpenAPI 认证保护断言（如需要） |
| 文档 | `docs/features/openapi-swagger-docs.md` | 新增/完善功能说明 |
| 文档 | `docs/design/api-spec.md` | 同步 OpenAPI/Swagger 入口与端点覆盖 |
| 文档 | `docs/BACKLOG.md` | B-136 状态流转与 plan 路径 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| `docs/plans/B-135-multi-model-comparison.md` | 同次执行新增 `/api/answer/compare`；B-136 schema 需要包含最终接口清单 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| `docs/plans/B-145-tauri-windows-packaging.md` | 仅 `docs/BACKLOG.md` 元数据同文件重叠；B-145 不修改 FastAPI OpenAPI schema | 分区：本 plan 不碰 Tauri、sidecar、打包脚本 |
| `docs/plans/B-135-multi-model-comparison.md` | 共享 `docs/design/api-spec.md` 和 `docs/BACKLOG.md`，且 B-136 需要覆盖 B-135 新端点 | 合并执行顺序：先完成 B-135，再执行 B-136；文档更新以最终接口为准 |
| `docs/superpowers/plans/2026-05-11-project-knowledge-base-ui-skeleton.md` | 旧 PySide6 UI skeleton 计划，不涉及 FastAPI OpenAPI schema | N/A |
| `docs/superpowers/plans/2026-05-11-project-knowledge-points.md` | 旧 `src/` knowledge point 计划，不涉及 FastAPI OpenAPI schema | N/A |
| `docs/superpowers/plans/2026-05-16-knowledge-island-core-models.md` | 旧 `src/` core model 计划，不涉及 FastAPI OpenAPI schema | N/A |

## 6. 完成标准

- [ ] 功能行为符合 `docs/features/openapi-swagger-docs.md` 的边界
- [ ] `/openapi.json` 返回 OpenAPI 3.0 schema，并包含当前 Web MVP API paths
- [ ] `/docs` 可加载 Swagger UI，认证开启时仍受保护
- [ ] B-136 新增测试通过
- [ ] 相关文档已同步（见下方"回流清单"）
- [ ] BACKLOG 条目 `B-136` 状态已更新为 `done`

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| OpenAPI / Swagger 入口、认证边界和覆盖范围 | `docs/features/openapi-swagger-docs.md` | [ ] |
| `/openapi.json`、`/docs`、`/redoc` 正式接口说明 | `docs/design/api-spec.md` | [ ] |

## 8. 执行记录

- 2026-06-29：创建 plan。ctx7 FastAPI 文档确认可通过 `app.openapi = custom_openapi` 和 `fastapi.openapi.utils.get_openapi()` 自定义 schema；本任务保留 FastAPI 默认 docs 路由。
- 2026-06-29：任务 1 红灯测试已运行：`E:\Code\knowledage_island\.venv\Scripts\python.exe -m pytest tests\test_webapp\test_fastapi_server.py -q -k "openapi or swagger"` 结果 1 failed / 1 passed，失败原因为 `/openapi.json` 只有 5 个操作且缺少显式 Web MVP paths；`E:\Code\knowledage_island\.venv\Scripts\python.exe -m pytest tests\test_webapp\test_auth_middleware.py -q -k "protects_fastapi_docs"` 结果 1 failed，失败原因为授权后的 schema 缺少 `/api/answer/compare`。
- 2026-06-29：任务 2 新增 `webapp/openapi_schema.py` 并在 `webapp/server.py` 安装 custom OpenAPI schema，过滤兼容 catch-all 的 schema 生成警告；验证命令：`E:\Code\knowledage_island\.venv\Scripts\python.exe -m pytest tests\test_webapp\test_fastapi_server.py -q -k "openapi or swagger"` 为 2 passed，`E:\Code\knowledage_island\.venv\Scripts\python.exe -m pytest tests\test_webapp\test_auth_middleware.py -q -k "protects_fastapi_docs"` 为 1 passed。

## 9. 状态快照

- **最后更新**：2026-06-29
- **进度**：已完成 1 / 4 项（见 § 3 勾选状态）
- **最新 commit**：`c4254bb` — test: 增加 OpenAPI 文档红灯测试
- **代码状态**：`fix/B-135-b136-model-compare-openapi` 分支；B-136 红灯测试已提交，失败点为运行时 schema 缺少显式 API paths
- **下一步**：任务 2：实现运行时 OpenAPI schema
- **续任务须知**：B-136 不改业务分发行为，只补 OpenAPI schema；认证开启时 `/docs`、`/redoc`、`/openapi.json` 仍需凭证。
