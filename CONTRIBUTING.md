# 贡献指南

感谢参与 Knowledge Island 项目。本文档用于统一开发流程、协作方式、提交要求和文档维护方式。

---

## 目录

1. 前置条件
2. 开发环境搭建
3. 分支与提交规范
4. 代码规范
5. 测试要求
6. 文档要求
7. Pull Request 流程
8. 架构决策记录（ADR）

---

## 1. 前置条件

| 工具 | 版本 | 用途 | 是否必需 |
|------|------|------|----------|
| Python | 3.10+ | 后端运行时 | 是 |
| Node.js / npm | Node 20+ | Vue 构建、单测和 Playwright | 是 |
| pip / venv | 随 Python | 依赖管理 | 是 |
| Git | 任意现代版本 | 版本控制 | 是 |
| Docker Desktop | 任意现代版本 | 容器化启动验证 | 按需 |
| PyMuPDF (`pymupdf`) | 与当前依赖兼容 | PDF 文本提取 | 可选 |
| Rust / Tauri CLI | 见 `src-tauri/` 与根 `package.json` | 桌面壳开发和打包 | 按需 |

---

## 2. 开发环境搭建

详细说明见 `docs/guides/setup.md`。

最小启动步骤：

```bash
# 1. 创建虚拟环境并安装依赖
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# 2. 复制环境变量模板
cp .env.example .env

# 3. 构建 Vue 生产静态文件
npm ci
npm run build

# 4. 启动本地 Web 应用
.venv\Scripts\python.exe app.py
```

浏览器访问 `http://127.0.0.1:8765`。

可选依赖安装：

```bash
pip install pymupdf    # PDF 正文抽取
```

---

## 3. 分支与提交规范

详细说明见 `docs/guides/branch-conventions.md`。

### 分支命名

```text
feature/<description>    新功能，如 feature/streaming-output
fix/<description>        问题修复，如 fix/vector-score-nan
refactor/<description>   重构，如 refactor/api-split-blueprints
docs/<description>       文档，如 docs/rewrite-per-spec
chore/<description>      维护，如 chore/upgrade-pymupdf
```

### 提交信息

遵循 Conventional Commits，使用中文摘要：

```text
feat(answers): 接入流式输出 SSE
fix(search): 修复向量分数 NaN 导致排序异常
docs(backlog): 新增竞品差距分析待办项
```

---

## 4. 代码规范

### 后端（backend/）

- `backend/api/` 与 `backend/routes/` 只做 HTTP 适配、参数校验和用例编排，不直接操作 SQLite
- `backend/storage/` 是 SQLite 唯一读写入口，不承载页面规则
- 业务行为放在 `backend/domain/`，provider 适配放在 `backend/providers/`
- 可选依赖必须用 `try/except ImportError` 引入并提供明确降级
- Agent 工具只允许只读操作，白名单硬编码在 `backend/domain/agent_tools.py`
- API Key 只保存引用（`env:*` / `saved:*`），任何接口响应不得包含明文 Key

### 前端（frontend/ + backend/static_dist/）

- 所有业务规则在后端实现，前端只负责展示和 API 调用。
- Vue 源码放在 `frontend/src/`，生产构建产物输出到 `backend/static_dist/`，不得提交构建产物。
- 当前前端以 reactive `appState` 切换视图，不使用 vue-router；不得在文档或测试中虚构 URL 路由。
- 修改前端后运行 `npm run build`，并按 `docs/guides/testing.md` 选择对应 Web 测试。

### 桌面与插件

- `src-tauri/` 只负责窗口、托盘和后端 sidecar 生命周期，不复制 Web 业务逻辑。
- `integrations/obsidian-plugin/` 是独立 desktop-only 插件；同步事件和受控发布必须保持令牌、路径、hash 与冲突边界。
- 静态配置测试不能替代真实安装包/WebView/API 连通性验证。

### Legacy（archive/src-desktop-legacy/）

- 旧 PySide6 / 六边形代码已归档，仅历史参考。
- 新任务不得重新接入 legacy 代码到当前 Web/Tauri 链路，除非 BACKLOG 明确要求并先完成 plan。

---

## 5. 测试要求

详细说明见 `docs/guides/testing.md`。

| 变更类型 | 必须通过的测试 |
|----------|---------------|
| `backend/api/`、`backend/routes/` 路由变更 | 对应 `tests/test_webapp/test_*_api.py` 与契约测试 |
| 检索 / 向量 / 分块变更 | `tests/test_webapp/test_search.py` / `test_embeddings.py` |
| 导入管线变更 | `tests/test_webapp/test_document_processing.py` |
| 聊天 / 会话变更 | `tests/test_webapp/test_chat_history.py` |
| Agent 工具变更 | `tests/test_webapp/test_agent_tools.py` |
| 任何 API 变更 | `tests/test_webapp/test_docs_contract.py` |
| Vue 行为变更 | `npm run test:unit` + `npm run build` + 相关 Playwright |
| Obsidian 插件变更 | 插件 `npm test` + `npm run typecheck` + `npm run build` |
| Tauri 配置/打包变更 | 静态回归 + 目标平台原生构建/运行验证 |

运行 Python 主测试：

```bash
.venv\Scripts\python.exe -m pytest tests/test_backend tests/test_webapp -q
```

只修改文档时至少运行：

```powershell
pwsh -NoProfile -File scripts\check-placeholders.ps1
pwsh -NoProfile -File scripts\check-doc-links.ps1
.venv\Scripts\python.exe scripts\check_docs_consistency.py
```

---

## 6. 文档要求

| 变更类型 | 需更新的文档 |
|----------|-------------|
| 新增需求 / 调整范围 | `docs/requirements/*` |
| 新增模块 / 改动功能 | `docs/requirements/functional-modules.md` |
| API 接口变更 | `docs/design/api-spec.md` |
| API 破坏性变更 | `docs/design/api-spec.md` + `docs/design/api-changes.md` |
| 数据库 Schema 变更 | `docs/design/database-design.md` |
| 架构模式变化 | `docs/design/architecture-overview.md` + ADR（必要时）|
| 已知问题 / 技术债 | `docs/BACKLOG.md` |
| 版本发布 | `CHANGELOG.md` |

所有文档头部必须包含：

```text
# 标题

> 状态：Active
> Owner：RAG 团队
> Last Updated：YYYY-MM-DD
> Scope：文档范围
> Related：相关文档路径
```

---

## 7. Pull Request 流程

1. 从 `main` 创建功能分支
2. 完成代码、测试和文档变更
3. 本地运行测试确认通过
4. 发起 PR，描述变更原因和范围
   - 使用 `.github/pull_request_template.md`
5. 自查清单：
   - [ ] 测试通过
   - [ ] 文档已同步
   - [ ] `CHANGELOG.md` 已更新
   - [ ] 无明文 API Key 泄漏
   - [ ] 可选依赖有降级处理

---

## 8. 架构决策记录（ADR）

重大架构决策必须记录在 `docs/adr/` 目录。

**完整的强制 / 非强制触发条件**以 `docs/README.md § 4 何时应新建 ADR` 为权威源，本节不再复述。

提交代码时只需自检：

- 本次改动是否触发了 `docs/README.md § 4` 中的强制条件？若是，同步提交 ADR。
- 若触发了 ADR，对应 `docs/features/*.md` 头部 `Related ADR` 字段**必须**填入 ADR 编号。

ADR 模板见 `docs/adr/ADR-000-template.md`。
