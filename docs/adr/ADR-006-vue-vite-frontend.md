# ADR-006 前端框架选型（Vue 3 + Vite）

> 状态：Accepted
> Date：2026-05-26
> Owner：RAG 团队
> Related：docs/features/frontend-engineering.md, docs/design/architecture-overview.md, docs/guides/setup.md, docs/guides/testing.md, docs/BACKLOG.md

## 1. 背景

Knowledge Island 在 B-141 启动前的 Web MVP 前端由单个 HTML、CSS 和多份原生 JavaScript 文件组成。随着项目空间、资料库、问答、评估、模型 Profile、Prompt 预设、Agent 工具、检索复盘等能力持续增加，原生脚本继续堆叠功能会提高回归风险。

B-139 已将后端迁移为 FastAPI + Uvicorn，B-140 已补充可选认证中间件。B-141 的目标是在不改 API 契约、不改数据库 schema 的前提下，引入独立前端工程，为后续前后端分离、组件化 UI 和更稳定的前端测试打基础。

## 2. 决策结论

采用 **Vue 3 + Vite** 作为 Web 前端工程化方案。

- 新建 `frontend/` 作为前端源码根目录。
- 使用 Vue 3 单文件组件组织页面、状态和 UI 片段。
- 使用 Vite 作为开发服务器与生产构建工具。
- 开发模式下，Vite dev server 通过 proxy 转发 `/api` 到 FastAPI。
- 生产模式下，Vite 构建产物输出到 `backend/knowledge_island/static_dist/`，由 FastAPI 静态服务托管。
- B-143/B-145 后已移除 legacy 静态前端 fallback，生产入口统一为 Vue/Vite 构建产物。

## 3. 迁移边界

B-141 分阶段执行：

| 阶段 | 目标 | 是否迁移完整业务 UI |
|------|------|---------------------|
| B-141A | 建立 Vue + Vite 工程骨架、后端服务构建产物、验证构建链 | 否 |
| B-141B | 迁移 API 客户端、状态模型和基础布局 | 否，保持行为兼容 |
| B-141C | 逐页迁移工作台、资料库、评估、设置等业务界面 | 是，按页面分片 |

B-141A 不重写业务交互，不改变 `/api/*` 路径、字段或错误格式；legacy 静态前端 fallback 已在后续 B-143 中移除。

## 4. 备选方案

### 4.1 继续 Vanilla JS

- 优点：零构建链，当前 `python app.py` 最简单。
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
| `backend/knowledge_island/server.py` | 托管 Vue/Vite 生产构建产物 |
| `Dockerfile` / 启动脚本 | 后续需安装并构建前端产物 |
| `tests/backend/` / `tests/frontend/` | 分别验证后端静态服务策略和 `frontend/` 构建产物、关键文案 |
| 文档 | 更新架构、setup、testing、CHANGELOG 和 devlog |

## 6. 约束

- 不改 SQLite schema。
- 不改现有 `/api/*` 契约。
- 不在前端硬编码 API Key、JWT、Token 或数据库路径。
- 不把后端业务规则搬到前端；前端只做状态、展示和 API 调用。
- B-141A 不删除 legacy `webapp/static/`。

## 7. 回滚策略

- 删除 `frontend/`、`package.json`、`package-lock.json` 和 Vite 构建相关提交。
- 恢复到对应提交前的静态服务策略；B-143/B-145 之后不再恢复 legacy 静态前端目录。
- 因不涉及数据库迁移，不需要数据回滚。

## 8. 验证方式

- `npm install` 或 `npm ci` 能安装前端依赖。
- `npm run build` 能生成 `backend/knowledge_island/static_dist/`。
- `python backend/app.py` 仍能访问首页。
- `tests/backend/` 与 `tests/frontend/` 后端和前端回归保持通过。
- 新增前端构建测试验证 `package.json`、Vite 配置和构建产物入口。
