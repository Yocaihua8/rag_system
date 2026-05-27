# 前端工程化

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-27
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
- B-141F 在 Vue 资料库视图中提供文本笔记导入和 URL 摘录导入，复用既有 `POST /api/import/note` 与 `POST /api/import/url` 契约。
- B-141G 在 Vue 资料库视图中提供导入批次历史和批次详情只读展示，复用既有 `GET /api/import/batches` 与 `GET /api/import/batches/detail` 契约。
- B-141H 在 Vue 资料库视图中提供普通文件上传导入，复用既有 `POST /api/import/upload` 契约；有当前项目空间时导入当前项目，没有项目空间时由后端创建 `browser-upload` 项目。
- B-141I 在 Vue 资料库视图中提供浏览器文件夹上传导入，复用既有 `POST /api/import/upload` 契约；前端用 `webkitRelativePath` 推导项目名和文档相对路径，并发送 `source_type=browser_folder_upload`。
- B-141J 在 Vue 资料库视图中提供当前项目目录同步入口，复用既有 `POST /api/import` 契约；后端继续负责项目根目录校验、导入规则和 `directory_sync` 批次记录。
- B-141K 在 Vue 资料库视图中提供当前项目目录导入预检入口，复用既有 `GET /api/import/preview` 只读契约；预检只展示可导入数、跳过数和跳过原因，不创建导入批次。
- B-141L 在 Vue 资料库视图中提供文档集合只读筛选入口，复用既有 `GET /api/document-collections` 与 `GET /api/documents?collection_id=...` 契约；当前只迁移全部/未分组/指定集合过滤，不迁移集合编辑或加入/移出文档。
- B-141M 在 Vue 资料库视图中提供文档集合新建和删除入口，复用既有 `POST /api/document-collections` 与 `POST /api/document-collections/delete` 契约；删除集合不删除文档，当前不迁移集合重命名或加入/移出文档。
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
| `frontend/src/api/document-collections.js` | Vue 资料库文档集合 API helper，调用既有 `/api/document-collections` 列表/新建契约和 `/api/document-collections/delete` 删除契约 |
| `frontend/src/api/imports.js` | Vue 资料库导入 API helper，调用既有 `/api/import/preview`、`/api/import`、`/api/import/note`、`/api/import/url`、`/api/import/upload`、`/api/import/batches` 和 `/api/import/batches/detail` |
| `frontend/src/state/app-state.js` | Vue 迁移期共享状态模型和基础视图切换 |
| `frontend/src/components/` | 迁移期布局组件，例如 `AppShell.vue`、`ProjectSpacePanel.vue`、`QuestionPanel.vue`、`AnswerPanel.vue`、`DocumentListPanel.vue`、`DocumentPreviewPanel.vue`、`DocumentImportPanel.vue`、`DocumentCollectionPanel.vue`、`ImportBatchHistoryPanel.vue` |
| `frontend/src/views/` | 工作台、资料库、评估、设置等页面组件 |
| `webapp/static_dist/` | Vite 生产构建输出，由 FastAPI 托管 |
| `webapp/static/` | 迁移期间的 legacy 原生前端 fallback |

## 4. 非目标

- 不在 B-141A/B-141B/B-141C/B-141D/B-141E/B-141F/B-141G/B-141H/B-141I/B-141J/B-141K/B-141L/B-141M 迁移完整业务页面。
- B-141C 不迁移导入、重命名、删除、文档列表、问答、评估或设置完整流程。
- B-141D 不迁移 SSE 流式输出、取消、聊天会话/历史、回答反馈、Agent 工具或检索调试。
- B-141E 不迁移文件导入、目录同步、上传、笔记、URL 摘录、删除文档、文档集合增删改或导入批次历史。
- B-141F 不迁移目录同步、浏览器文件夹上传、普通文件上传、导入预检、删除文档、文档集合增删改或导入批次历史。
- B-141G 不迁移目录同步、浏览器文件夹上传、普通文件上传、导入预检、批次回滚、批次删除、批次重试、删除文档或文档集合增删改。
- B-141H 不迁移浏览器文件夹上传、同步当前项目目录、导入预检、删除文档、文档集合增删改或数据库 schema。
- B-141I 不迁移同步当前项目目录、导入预检、删除文档、文档集合增删改或数据库 schema。
- B-141J 不迁移导入预检、删除文档、文档集合增删改、项目改名/删除或数据库 schema。
- B-141K 不执行导入、不创建导入批次、不迁移删除文档、文档集合增删改、项目改名/删除或数据库 schema。
- B-141L 不迁移文档集合新建、编辑、删除、加入文档、移出文档、删除文档、项目改名/删除或数据库 schema。
- B-141M 不迁移文档集合重命名、加入文档、移出文档、删除文档、项目改名/删除或数据库 schema。
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

B-141F 起，Vue 资料库继续迁移轻量导入薄片：`imports.js` 只调用既有 `POST /api/import/note` 与 `POST /api/import/url`，`DocumentImportPanel` 负责文本笔记和 URL 摘录两个表单、提交状态和错误/成功提示。成功导入后刷新 B-141E 文档列表。后端 API、SQLite schema、目录同步、文件上传、删除、集合管理和批次历史不在本片调整。

B-141G 起，Vue 资料库继续迁移导入批次历史薄片：`imports.js` 扩展只读 `GET /api/import/batches` 与 `GET /api/import/batches/detail` helper，`ImportBatchHistoryPanel` 负责最近批次列表、批次详情、汇总计数以及跳过/读取失败明细展示。文本笔记或 URL 摘录导入成功后会刷新文档列表和导入批次历史。后端 API、SQLite schema、目录同步、文件上传、导入预检、批次回滚/删除/重试和集合管理不在本片调整。

B-141H 起，Vue 资料库继续迁移普通文件上传导入薄片：`imports.js` 扩展 `POST /api/import/upload` helper，普通文件使用文件名作为 `relative_path`，文本文件上传 `content`，DOCX/PDF 上传 `content_base64 + size`。`DocumentImportPanel` 增加普通 `multiple` file input，明确不设置 `webkitdirectory`；`App.vue` 在成功后刷新项目空间、文档列表和导入批次历史。后端 API、SQLite schema、浏览器文件夹上传、同步当前项目目录、导入预检、删除和集合管理不在本片调整。

B-141I 起，Vue 资料库继续迁移浏览器文件夹上传导入薄片：`imports.js` 扩展 `POST /api/import/upload` helper，文件夹入口读取 `webkitRelativePath`，首段作为 `project_name`，其余路径作为文档 `relative_path`，并发送 `source_type=browser_folder_upload`。`DocumentImportPanel` 增加单独的 `webkitdirectory multiple` file input；普通文件上传 input 仍不设置 `webkitdirectory`。`App.vue` 在成功后选择后端返回项目，并刷新项目空间、文档列表和导入批次历史。后端 API、SQLite schema、同步当前项目目录、导入预检、删除和集合管理不在本片调整。

B-141J 起，Vue 资料库继续迁移当前项目目录同步薄片：`imports.js` 扩展 `POST /api/import` helper，`DocumentImportPanel` 增加“同步当前项目目录”按钮，未选择项目空间时禁用。`App.vue` 在成功后刷新文档列表和导入批次历史，并复用导入结果计数展示。后端 API、SQLite schema、导入预检、删除、集合管理和项目改名/删除不在本片调整。

B-141K 起，Vue 资料库继续迁移当前项目目录导入预检薄片：`imports.js` 扩展 `GET /api/import/preview` helper，`DocumentImportPanel` 在本地目录区域增加“预检当前项目目录”按钮和只读结果摘要，展示可导入数、跳过数和跳过原因。`App.vue` 单独保存 `importPreview`、`importPreviewLoading` 和 `importPreviewError`，预检完成后不刷新文档列表、不刷新导入批次历史，也不创建导入批次。后端 API、SQLite schema、删除、集合管理和项目改名/删除不在本片调整。

B-141L 起，Vue 资料库继续迁移文档集合只读筛选薄片：`document-collections.js` 只调用既有 `GET /api/document-collections`，`DocumentCollectionPanel` 展示“全部文档 / 未分组 / 指定集合”筛选、集合列表和集合文档数。`App.vue` 保存集合列表、集合加载状态和当前 `selectedDocumentCollectionId`，选择筛选项后复用 B-141E 的 `listDocuments(projectId, collectionId)` 刷新文档列表。后端 API、SQLite schema、集合新建/编辑/删除、加入/移出文档和删除文档不在本片调整。

B-141M 起，Vue 资料库继续迁移文档集合最小写操作：`document-collections.js` 扩展 `POST /api/document-collections` 和 `POST /api/document-collections/delete` helper，`DocumentCollectionPanel` 提供集合名称输入、新建按钮和删除集合按钮，`App.vue` 在创建或删除后刷新集合列表；删除当前筛选集合时清空筛选并刷新文档列表。后端 API、SQLite schema、集合重命名、加入/移出文档和删除文档不在本片调整。

## 6. 验收标准

- `frontend/` 存在最小 Vue 3 + Vite 工程。
- Vue 前端存在 `apiGet` / `apiPost`、共享状态模型、工作台 / 资料库 / 评估 / 设置四个基础视图、资料库项目空间选择/创建薄片、资料库文档列表/预览薄片、资料库文本/URL 导入薄片、资料库导入批次历史薄片、资料库普通文件上传薄片、资料库浏览器文件夹上传薄片、资料库当前目录同步薄片、资料库导入预检薄片、资料库文档集合只读筛选/新建/删除薄片，以及工作台非流式问答入口。
- Vue 工作台可在已选择项目空间时提交问题到既有 `/api/answer`，并展示回答、来源、模型模式和来源质量摘要。
- Vue 资料库可在已选择项目空间时读取文档列表，并通过单文档预览接口展示正文。
- Vue 资料库可在已选择项目空间时提交文本笔记或 URL 摘录导入，并在成功后刷新文档列表。
- Vue 资料库可在已选择项目空间时读取导入批次历史，点击批次后查看只读详情、汇总计数和跳过/读取失败明细。
- Vue 资料库可选择一个或多个普通文件上传；有当前项目空间时导入当前项目，没有项目空间时由后端创建 `browser-upload` 项目。
- Vue 资料库可通过浏览器文件夹选择导入本机文件夹；前端不读取原始宿主机绝对路径，只上传授权文件内容和相对路径。
- Vue 资料库可在已选择项目空间时同步当前项目目录；未选择项目空间时同步入口禁用。
- Vue 资料库可在已选择项目空间时预检当前项目目录，展示可导入数、跳过数和跳过原因；预检不会写入文档或导入批次。
- Vue 资料库可在已选择项目空间时读取文档集合，并按全部、未分组或指定集合过滤文档列表。
- Vue 资料库可在已选择项目空间时新建或删除文档集合；删除集合会提示“集合内文档不会被删除”，并在删除当前筛选集合后回到全部文档。
- `npm run build` 可生成 `webapp/static_dist/`。
- FastAPI 优先服务 `webapp/static_dist/`；构建产物不存在时回退 `webapp/static/`。
- Web MVP 后端测试保持通过。
- 文档说明清楚当前是工程化骨架阶段，不宣称完整 Vue UI 已迁移完成。
