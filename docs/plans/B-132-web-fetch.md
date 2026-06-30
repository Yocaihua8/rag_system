# B-132 网页自动爬取

> 状态：Active
> 创建时间：2026-06-30
> 创建方：Codex
> 关联 BACKLOG：B-132
> 关联功能文档：docs/features/web-crawling-research.md
> 关联设计文档：docs/requirements/functional-modules.md, docs/design/api-spec.md

## 1. 目标

在 Knowledge Island Web MVP 中实现 B-119 收敛后的最小安全切片：用户在资料库页输入单个公开网页 URL，后端先执行受控抓取预览，用户确认后把抓取正文作为新的网页抓取来源入库。当前不做递归爬虫、站点地图、定时同步、登录态抓取、浏览器 Profile/Cookie 导入或 Agent 自动访问外部 URL。

## 2. 前置条件

- 已读取 `AGENTS.md`
- 已读取 `docs/BACKLOG.md`
- 已读取 `docs/features/web-crawling-research.md`
- 已读取 `docs/requirements/functional-modules.md`
- 已读取 `docs/design/api-spec.md`
- 已读取现有导入代码：`webapp/source_import.py`、`webapp/routes/imports.py`、`frontend/src/api/imports.js`、`frontend/src/components/DocumentImportPanel.vue`
- 已通过 Context7 查询 Playwright Python 库 ID；docs 获取阶段出现 `fetch failed`，本片不依赖 Playwright 运行时

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 后端核心抓取服务：TDD 新增 URL 校验、SSRF 拦截、robots.txt 判断、大小/类型限制、HTML 正文净化测试与实现。
- [x] 后端导入接口：TDD 新增 `/api/import/web-fetch/preview` 与 `/api/import/web-fetch/commit`，确认入库使用独立 `web:` 虚拟来源和 `web_fetch` 批次类型。
- [ ] 前端资料库入口：TDD 新增 API helper、导入面板预览/确认交互、App 状态刷新，复用现有导入状态和批次历史。
- [ ] 文档回流：同步 `api-spec`、功能模块、研究文档、OpenAPI 显式路径、CHANGELOG 和必要测试说明。
- [ ] 完成收口：运行相关后端/前端/文档验证，BACKLOG B-132 状态置 `done` 后按规则移出 § 5，删除本 plan。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `webapp/web_fetch.py` | 新增：受控单 URL 抓取、robots、SSRF、正文抽取 |
| 代码 | `webapp/source_import.py` | 修改：新增 `web:` 虚拟来源导入 |
| 代码 | `webapp/routes/imports.py` | 修改：新增 web-fetch preview / commit 路由 |
| 代码 | `webapp/openapi_schema.py` | 修改：新增显式 OpenAPI 路径 |
| 前端 | `frontend/src/api/imports.js` | 修改：新增预览/确认 API helper |
| 前端 | `frontend/src/components/DocumentImportPanel.vue` | 修改：新增网页抓取表单和预览区 |
| 前端 | `frontend/src/App.vue` | 修改：接入预览/确认状态和刷新逻辑 |
| 前端 | `frontend/src/state/app-state.js` | 修改：新增 web fetch 预览状态 |
| 测试 | `tests/test_webapp/test_web_fetch.py` | 新增：核心抓取服务单元测试 |
| 测试 | `tests/test_webapp/test_api.py` | 修改：新增 API 行为测试 |
| 测试 | `tests/test_webapp/test_api_route_split.py` | 修改：新增 route module 测试 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 修改：新增 Vue 静态契约测试 |
| 文档 | `docs/features/web-crawling-research.md` | 修改：标记最小实现已落地边界 |
| 文档 | `docs/requirements/functional-modules.md` | 修改：同步 URL 自动抓取能力 |
| 文档 | `docs/design/api-spec.md` | 修改：新增接口契约 |
| 文档 | `CHANGELOG.md` | 修改：记录 B-132 用户可见变化 |
| 文档 | `docs/BACKLOG.md` | 修改：B-132 生命周期状态 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | B-119 研究结论已经沉淀为正式功能文档，本实现不依赖未完成 plan。 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| `docs/plans/B-149-ci-pipeline.md` | B-149 影响 `.github/workflows/ci.yml`、`docs/guides/testing.md`、`docs/guides/release-process.md`；B-132 不修改这些文件，仅修改 B-132 相关导入代码、前端和正式功能/API 文档。 | 分区 |

## 6. 完成标准

- [ ] `/api/import/url` 行为保持手动摘录，不发起网络请求
- [ ] `/api/import/web-fetch/preview` 可返回单 URL 抓取预览，失败时不写数据库
- [ ] `/api/import/web-fetch/commit` 只接收预览字段确认入库，写入 `web:` 虚拟来源和 `web_fetch` 批次
- [ ] SSRF 拦截覆盖 localhost、回环、私网、链路本地、保留地址和重定向后目标
- [ ] robots.txt 禁止时预览失败且不写入文档
- [ ] HTML 抽取结果不包含 script/style/form 内容
- [ ] 前端可完成预览、查看元数据、确认入库和刷新文档/批次历史
- [ ] 相关测试、文档一致性和前端构建验证通过
- [ ] BACKLOG B-132 已按完成规则移出 § 5，完成记录写入 CHANGELOG

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 新增 web-fetch API 契约、错误和批次类型 | `docs/design/api-spec.md` | [ ] |
| 知识导入模块新增单 URL 抓取预览/确认能力 | `docs/requirements/functional-modules.md` | [ ] |
| B-119 研究结论中最小安全切片已落地 | `docs/features/web-crawling-research.md` | [ ] |
| 用户可见变更与 BACKLOG 完成归档 | `CHANGELOG.md`, `docs/BACKLOG.md` | [ ] |

## 8. 执行记录

- 2026-06-30：启动 B-132。Context7 `library Playwright` 首次 `fetch failed`，设置 `NO_PROXY=*` 后成功匹配 `/microsoft/playwright-python`；`docs` 获取仍 `fetch failed`。本片按 B-119 建议采用 Python 标准库静态抓取，不新增 Playwright 必需依赖。
- 2026-06-30：使用当前 checkout 执行；未创建新 worktree。当前分支 `fix/b-08-concurrent-index`，启动前工作区干净。
- 2026-06-30：完成后端核心抓取服务。红灯为 `ModuleNotFoundError: No module named 'webapp.web_fetch'`，实现后 `tests/test_webapp/test_web_fetch.py` 5 个测试通过。
- 2026-06-30：完成后端导入接口。红灯为新路由缺失导致 monkeypatch 属性不存在与 `/api/import/web-fetch/commit` 返回 404；实现后 preview / commit 目标测试通过，并通过相邻后端回归 13 项。

## 9. 状态快照

- **最后更新**：2026-06-30 20:04
- **进度**：已完成 2 / 5 项（见 § 3 勾选状态）
- **最新 commit**：`3d5dfd5` — feat: 新增网页抓取核心安全服务
- **代码状态**：`fix/b-08-concurrent-index`；后端核心抓取服务与 preview / commit 导入接口已完成，待接入前端资料库入口
- **下一步**：前端资料库入口：TDD 新增 API helper、导入面板预览/确认交互、App 状态刷新，复用现有导入状态和批次历史。
- **续任务须知**：不要修改 B-149 CI plan 负责的 `.github/workflows/ci.yml`、`docs/guides/testing.md`、`docs/guides/release-process.md`；B-132 只处理网页抓取导入。
