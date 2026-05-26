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
- B-141B 提供 Vue API client、共享状态模型和四个基础视图壳，不替换完整业务 UI。
- B-141C 在 Vue 资料库视图中提供项目空间列表、当前项目选择、最近项目恢复和新建项目空间。
- B-141D 在 Vue 工作台中提供非流式问答入口，复用既有 `POST /api/answer`，展示回答、来源和来源质量摘要。
- B-141E 在 Vue 资料库视图中提供当前项目文档列表和单文档正文预览，复用既有 `GET /api/documents` 与 `GET /api/document` 契约。
- 在迁移完成前，`webapp/static/` 保留为 legacy fallback。

## 3. 工程目录

| 路径 | 用途 |
|------|------|
| `frontend/` | Vue 3 + Vite 前端源码 |
| `frontend/src/` | Vue 入口、组件、前端 API 客户端和样式 |
| `frontend/src/api/client.js` | Vue 前端 API helper，封装 `apiGet` / `apiPost` 与错误归一化 |
| `frontend/src/api/projects.js` | Vue 项目空间 API helper，封装项目列表、创建、选择和最近项目恢复 |
| `frontend/src/api/answer.js` | Vue 工作台非流式问答 API helper，调用既有 `/api/answer` |
| `frontend/src/api/documents.js` | Vue 资料库文档 API helper，调用既有 `/api/documents` 和 `/api/document` |
| `frontend/src/state/app-state.js` | Vue 迁移期共享状态模型和基础视图切换 |
| `frontend/src/components/` | 迁移期布局组件，例如 `AppShell.vue`、`ProjectSpacePanel.vue`、`QuestionPanel.vue`、`AnswerPanel.vue`、`DocumentListPanel.vue`、`DocumentPreviewPanel.vue` |
| `frontend/src/views/` | 工作台、资料库、评估、设置等页面组件 |
| `webapp/static_dist/` | Vite 生产构建输出，由 FastAPI 托管 |
| `webapp/static/` | 迁移期间的 legacy 原生前端 fallback |

## 4. 非目标

- 不在 B-141A/B-141B/B-141C/B-141D/B-141E 迁移完整业务页面。
- B-141C 不迁移导入、重命名、删除、文档列表、问答、评估或设置完整流程。
- B-141D 不迁移 SSE 流式输出、取消、聊天会话/历史、回答反馈、Agent 工具或检索调试。
- B-141E 不迁移文件导入、目录同步、上传、笔记、URL 摘录、删除文档、文档集合增删改或导入批次历史。
- 不删除 legacy `webapp/static/`。
- 不修改 SQLite schema。
- 不改变 Agent 工具权限边界。
- 不新增前端登录页；认证启用后的凭证 UI 后续另拆。

## 5. 架构落点

Vue 3 + Vite 只替代展示层工程组织。后端仍由 `webapp/server.py` 提供 FastAPI 服务，`webapp/api.py` 和 `webapp/routes/*` 保持 API 契约，业务层和数据层不因 B-141 调整。

B-141B 起，Vue 侧采用轻量 Composition API 结构：API helper 负责请求和错误归一化，共享状态模块保存当前项目、会话、文档、评估、工具、检索等迁移期字段，`AppShell` 管理四个主视图导航。该状态模型只是前端 UI 状态，不新增后端数据规则。

B-141C 起，Vue 资料库视图先迁移项目空间薄片：`projects.js` 只调用既有 `GET /api/projects` 和 `POST /api/projects`，`ProjectSpacePanel` 只展示和提交项目空间状态，不承载导入、文档集合、问答或设置业务规则。

B-141D 起，Vue 工作台先迁移非流式问答薄片：`answer.js` 只调用既有 `POST /api/answer`，`QuestionPanel` 负责问题输入与提交状态，`AnswerPanel` 负责回答、来源和来源质量展示。后端 API、SQLite schema、SSE 流式问答、聊天会话、回答反馈、Agent 工具和检索调试不在本片调整。

B-141E 起，Vue 资料库继续迁移只读文档浏览薄片：`documents.js` 只调用既有 `GET /api/documents` 与 `GET /api/document`，`DocumentListPanel` 负责文档列表、空态和读取状态，`DocumentPreviewPanel` 负责单文档正文预览。文档列表仍不依赖列表响应中的 `content` 字段；正文只来自单文档预览接口。后端 API、SQLite schema、导入、删除、集合管理和批次历史不在本片调整。

## 6. 验收标准

- `frontend/` 存在最小 Vue 3 + Vite 工程。
- Vue 前端存在 `apiGet` / `apiPost`、共享状态模型、工作台 / 资料库 / 评估 / 设置四个基础视图、资料库项目空间选择/创建薄片、资料库文档列表/预览薄片，以及工作台非流式问答入口。
- Vue 工作台可在已选择项目空间时提交问题到既有 `/api/answer`，并展示回答、来源、模型模式和来源质量摘要。
- Vue 资料库可在已选择项目空间时读取文档列表，并通过单文档预览接口展示正文。
- `npm run build` 可生成 `webapp/static_dist/`。
- FastAPI 优先服务 `webapp/static_dist/`；构建产物不存在时回退 `webapp/static/`。
- Web MVP 后端测试保持通过。
- 文档说明清楚当前是工程化骨架阶段，不宣称完整 Vue UI 已迁移完成。
