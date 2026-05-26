# 前端工程化

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-26
> Scope：B-141 Vue 3 + Vite 前端工程化
> Related：docs/adr/ADR-006-vue-vite-frontend.md, docs/design/architecture-overview.md, docs/guides/setup.md, docs/guides/testing.md, docs/BACKLOG.md

## 1. 功能定位

B-141 是 Web 前端技术栈迁移，不新增后端业务能力。目标是把当前 `webapp/static/` 中的原生 HTML/CSS/JS 前端逐步迁移到独立 `frontend/` 工程，使用 Vue 3 组件和 Vite 构建，降低大型单页脚本继续增长带来的维护成本。

## 2. 用户可见行为

- 默认访问地址仍为 `http://127.0.0.1:8765`。
- `/api/*` 请求路径、请求字段、响应字段和错误格式保持兼容。
- B-141A 只提供前端工程骨架和构建链，不替换完整业务 UI。
- 在迁移完成前，`webapp/static/` 保留为 legacy fallback。

## 3. 工程目录

| 路径 | 用途 |
|------|------|
| `frontend/` | Vue 3 + Vite 前端源码 |
| `frontend/src/` | Vue 入口、组件、前端 API 客户端和样式 |
| `webapp/static_dist/` | Vite 生产构建输出，由 FastAPI 托管 |
| `webapp/static/` | 迁移期间的 legacy 原生前端 fallback |

## 4. 非目标

- 不在 B-141A 迁移完整业务页面。
- 不删除 legacy `webapp/static/`。
- 不修改 SQLite schema。
- 不改变 Agent 工具权限边界。
- 不新增前端登录页；认证启用后的凭证 UI 后续另拆。

## 5. 架构落点

Vue 3 + Vite 只替代展示层工程组织。后端仍由 `webapp/server.py` 提供 FastAPI 服务，`webapp/api.py` 和 `webapp/routes/*` 保持 API 契约，业务层和数据层不因 B-141A 调整。

## 6. 验收标准

- `frontend/` 存在最小 Vue 3 + Vite 工程。
- `npm run build` 可生成 `webapp/static_dist/`。
- FastAPI 优先服务 `webapp/static_dist/`；构建产物不存在时回退 `webapp/static/`。
- Web MVP 后端测试保持通过。
- 文档说明清楚当前是工程化骨架阶段，不宣称完整 Vue UI 已迁移完成。
