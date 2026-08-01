# ADR-006 前端框架选型（Vue 3 + Vite）

> 状态：Accepted
> Date：2026-05-26
> Owner：RAG 团队
> Scope：Web 表现层框架、构建工具与迁移边界
> Related：[架构总览](../design/architecture-overview.md)、[UI 线框](../design/ui-wireframes.md)、[页面模块契约](../design/page-module-contract.md)、[组件契约](../design/component-api-contract.md)、[搭建指南](../guides/setup.md)、[测试指南](../guides/testing.md)、[ADR-010](ADR-010-runtime-separation.md)
> 部分取代：[ADR-010](ADR-010-runtime-separation.md) 已取代本决策中的 FastAPI 静态托管和同源 `/api` 请求边界

## 1. 背景

Knowledge Island 当时的 Web MVP 前端位于 legacy static，由单个 HTML、CSS 和多份原生 JavaScript 文件组成。随着项目空间、资料库、问答、评估、模型 Profile、Prompt 预设、Agent 工具、检索复盘等能力持续增加，`app.js` 和 `ui.js` 已明显变大，继续以原生脚本堆叠功能会提高回归风险。B-143 已删除 legacy static；B-168 后当前 Vue/Vite 生产构建产物位于 `frontend/dist/`。

B-139 已将后端迁移为 FastAPI + Uvicorn，B-140 已补充可选认证中间件。B-141 的目标是在不改 API 契约、不改数据库 schema 的前提下，引入独立前端工程，为组件化 UI 和更稳定的前端测试打基础。B-168 随后完成运行时分离；本 ADR 继续决定 Vue 3 + Vite 选型，而“构建到后端静态目录、由 FastAPI 托管、通过同源 `/api` 访问”的原实现边界已由 ADR-010 取代。

## 2. 决策结论

采用 **Vue 3 + Vite** 作为 Web 前端工程化方案。

- 新建 `frontend/` 作为前端源码根目录。
- 使用 Vue 3 单文件组件组织页面、状态和 UI 片段。
- 使用 Vite 作为开发服务器与生产构建工具。
- 前端通过 `VITE_API_BASE_URL` 访问独立 FastAPI 服务。
- Vite 构建产物只输出到 `frontend/dist/`，不由 FastAPI 托管；完整运行时边界见 ADR-010。
- legacy static 在迁移期间保留为 fallback，不在 B-141A 删除；B-143 后已删除。

## 3. 历史迁移边界

Vue 迁移曾按 B-141 分阶段执行；下表是决策实施历史，不是当前运行方式：

| 阶段 | 目标 | 是否迁移完整业务 UI |
|------|------|---------------------|
| B-141A | 建立 Vue + Vite 工程骨架、后端服务构建产物、验证构建链 | 否 |
| B-141B | 迁移 API 客户端、状态模型和基础布局 | 否，保持行为兼容 |
| B-141C | 逐页迁移工作台、资料库、评估、设置等业务界面 | 是，按页面分片 |

B-141A 当时不删除 legacy static，不重写业务交互，不改变 `/api/*` 路径、字段或错误格式；legacy static 已由 B-143 删除。当前生产构建与请求边界以 ADR-010 为准。

## 4. 备选方案

### 4.1 继续 Vanilla JS

- 优点：零构建链，当前 `python -m backend` 最简单。
- 缺点：文件已变大，UI 状态和事件绑定继续增长会影响可维护性。
- 未采用原因：不适合继续承载多页面工作台和后续客户端扩展。

### 4.2 React + Vite

- 优点：生态大，组件与测试工具丰富。
- 缺点：当前项目没有 React 资产；团队文档已将 ADR-006 标记为 Vue 3 + Vite。
- 未采用原因：Vue 3 的模板语法更贴近当前 HTML 迁移方式，渐进迁移成本更低。

### 4.3 Vue 3 + Vite

- 优点：组件化、开发服务器快、生产构建简单；可先搭骨架，再逐页迁移。
- 缺点：引入 Node/npm 构建链，需要更新 Docker、测试和发布流程。
- 采用原因：符合 B-141 的前后端分离目标，且能按阶段低风险迁移。

## 5. 影响

| 模块 | 影响 |
|------|------|
| `frontend/` | 新增 Vue 3 + Vite 前端源码、构建配置和 npm 脚本 |
| `backend/api/server.py` | B-168 后只提供 API/SSE，不再托管前端 |
| `frontend/Dockerfile` | 独立构建并由 Nginx 服务前端产物 |
| `tests/repository` | 验证 workspace、构建产物和运行时边界 |
| 文档 | 更新架构、setup、testing 和 CHANGELOG |

## 6. 约束

- 不改 SQLite schema。
- 不改现有 `/api/*` 契约。
- 不在前端硬编码 API Key、JWT、Token 或数据库路径。
- 不把后端业务规则搬到前端；前端只做状态、展示和 API 调用。
- 历史迁移期不在 B-141A 删除 legacy static；该临时约束已随 B-143 完成而结束。

## 7. 回滚策略

- 删除 `frontend/`、`package.json`、`package-lock.json` 和 Vite 构建相关提交。
- 若回滚 B-168，需同时恢复旧静态托管和同源请求；该方案仅能通过 Git 历史恢复，不提供兼容壳。
- 因不涉及数据库迁移，不需要数据回滚。

## 8. 验证方式

- `npm install` 或 `npm ci` 能安装前端依赖。
- `npm run frontend:build` 能生成 `frontend/dist/` Vue/Vite 生产构建产物。
- `python -m backend` 启动 API，根路由返回 404。
- `tests/integration` 与 `tests/repository` 后端/结构回归保持通过。
- 新增前端构建测试验证 `package.json`、Vite 配置和构建产物入口。
