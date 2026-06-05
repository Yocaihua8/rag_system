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
| pip / venv | 随 Python | 依赖管理 | 是 |
| Node.js / npm | Node 20+ / npm 10+ | Vue/Vite 前端构建 | 是 |
| Git | 任意现代版本 | 版本控制 | 是 |
| Docker Desktop | 任意现代版本 | 容器化启动验证 | 按需 |
| pymupdf | 1.20+ | PDF 文本提取 | 可选 |
| jieba | 0.42+ | 中文分词 | 可选 |

---

## 2. 开发环境搭建

详细说明见 `docs/guides/setup.md`。

最小启动步骤：

```bash
# 1. 创建虚拟环境并安装依赖
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
npm --prefix frontend install
npm --prefix frontend run build

# 2. 复制环境变量模板
cp .env.example .env

# 3. 启动 Web MVP
.venv\Scripts\python.exe backend/app.py
```

浏览器访问 `http://127.0.0.1:8765`。

可选依赖安装：

```bash
pip install pymupdf    # PDF 正文抽取
pip install jieba      # 中文分词（提升关键词检索质量）
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

### Web MVP（backend/knowledge_island/）

- `api.py` 只做参数校验和用例编排，不直接操作 SQLite
- `storage.py` 是 SQLite 唯一入口，不承载业务规则
- 可选依赖（pymupdf / jieba）必须用 `try/except ImportError` 引入，失败时提供明确降级
- Agent 工具只允许只读操作，白名单硬编码在 `agent_tools.py`
- API Key 只保存引用（`env:*` / `saved:*`），任何接口响应不得包含明文 Key

### 前端（frontend/）

- 所有业务规则在后端实现，前端只负责展示和 API 调用
- Vue 前端源码放在 `frontend/src/`，组件、API helper 和共享状态按既有目录组织
- 提交前运行 `tests/frontend/test_frontend_vue_app.py`、`tests/frontend/test_frontend_build.py` 和 `npm --prefix frontend run build`

### Legacy（legacy/desktop/）

- 保持六边形分层约束：配置 → 领域 → 端口 → 适配器 → 应用 → 表现
- 新任务不应同时修改 `backend/knowledge_island/` 和 `legacy/desktop/`，除非明确为迁移任务

---

## 5. 测试要求

详细说明见 `docs/guides/testing.md`。

| 变更类型 | 必须通过的测试 |
|----------|---------------|
| `backend/knowledge_island/api.py` 路由变更 | `tests/backend/test_api.py` |
| 检索 / 向量 / 分块变更 | `tests/backend/test_search.py` / `test_embeddings.py` |
| 导入管线变更 | `tests/backend/test_document_processing.py` |
| 聊天 / 会话变更 | `tests/backend/test_chat_history.py` |
| Agent 工具变更 | `tests/backend/test_agent_tools.py` |
| 任何 API 变更 | `tests/backend/test_docs_contract.py` |
| Vue 前端或静态服务变更 | `tests/frontend/test_frontend_vue_app.py` / `tests/frontend/test_frontend_build.py` |

运行全量 Web MVP 测试：

```bash
.venv\Scripts\python.exe -m pytest tests/backend tests/frontend -q
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
