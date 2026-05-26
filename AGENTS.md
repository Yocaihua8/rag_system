# AGENTS.md

> 本文件为 AI 编码助手（Claude Code、Cursor、Copilot 等）提供项目操作上下文。
> 代码结构或团队约定发生实质性变化时同步更新。不替代 `CONTRIBUTING.md`，后者为人工贡献规范。

## 1. 项目概述

Knowledge Island 是一个本地 RAG（检索增强生成）知识库系统，帮助用户将本地文档转化为可检索的知识库，并通过 LLM 回答基于文档的问题。支持关键词检索、语义向量检索、Agent 工具辅助问答。

| 项 | 值 |
|----|----|
| 项目类型 | Web 全栈（FastAPI + Uvicorn 后端 + Vue 3/Vite 前端骨架 + legacy 原生静态前端） |
| 当前阶段 | MVP |
| 主要用户 | 本地个人用户、小团队知识沉淀场景 |
| 文档入口 | `docs/README.md` |

## 2. 技术栈

| 类型 | 名称 | 版本 | 说明 |
|------|------|------|------|
| 语言 | Python | 3.10+ | 后端运行时 |
| HTTP 框架 | FastAPI + Uvicorn | FastAPI 0.115+ / Uvicorn 0.30+ | B-139 迁移，ADR-001 |
| 数据库 | SQLite | 随 Python | 全量存储，含向量（ADR-002） |
| 向量存储 | SQLite 内置扩展 | — | B-134 评估 Qdrant 替换 |
| 前端 | Vue 3 + Vite / legacy 原生 HTML/CSS/JS | Vue 3.5+ / Vite 7+ | B-141A 已引入工程骨架；完整业务 UI 迁移前保留 `webapp/static/` fallback |
| 测试框架 | pytest | 7+ | — |
| 包管理器 | pip + venv | — | 依赖文件 `requirements.txt` |

## 3. 目录速查

| 路径 | 用途 |
|------|------|
| `webapp/` | Web MVP 生产代码根目录 |
| `frontend/` | Vue 3 + Vite 前端工程源码（B-141 起） |
| `src/` | Legacy PySide6 桌面端（六边形架构，历史参考） |
| `tests/` | 测试代码根目录 |
| `docs/requirements/` | 需求背景、功能范围、MVP 定义 |
| `docs/design/` | 架构、接口、数据库、权限、状态流 |
| `docs/features/` | 各功能模块规格（每个功能一份） |
| `docs/adr/` | 架构决策记录 |
| `docs/plans/` | AI 任务计划（与 BACKLOG 联动，执行完删除） |
| `docs/BACKLOG.md` | 待办、已知问题、技术债 |
| `CHANGELOG.md` | 对外发布变更 |

> 完整目录结构见 `docs/README.md § 2`。

## 4. 开发环境与常用命令

### 4.1 启动本地环境

```bash
python -m venv .venv
.venv\Scripts\activate                    # Windows
pip install -r requirements.txt
cp .env.example .env                      # 配置 API Key 等环境变量
.venv\Scripts\python.exe app.py           # 启动 Web MVP（默认 http://127.0.0.1:8765）
```

可选依赖（按需安装）：

```bash
pip install pymupdf    # PDF 正文抽取
pip install jieba      # 中文分词（提升关键词检索质量）
```

### 4.2 测试与验证

```bash
# Web MVP 全量测试
.venv\Scripts\python.exe -m pytest tests/test_webapp -q

# 旧业务层回归（确认 legacy 未被新入口改坏）
.venv\Scripts\python.exe -m pytest tests/test_application tests/test_domain tests/test_adapters -q
```

> 详细搭建步骤见 `docs/guides/setup.md`。

## 5. 架构概要

本项目默认入口为 Web MVP，采用**三层架构**；Legacy（`src/`）采用六边形架构，作为历史参考保留。

**Web MVP 三层职责**：

- 表现层：`frontend/`（Vue 3 + Vite 工程骨架）、`webapp/static/`（迁移期 legacy 静态前端）、`webapp/server.py`（FastAPI app、静态文件、SSE）、`webapp/api.py`（兼容分发、参数校验）
- 业务层：`webapp/answers.py`（回答生成）、`webapp/search.py`（检索）、`webapp/ingestion.py`（导入管线）、`webapp/agent_tools.py`（Agent 工具）
- 数据层：`webapp/storage.py`（SQLite 唯一读写入口）

**关键边界**：

- `api.py` 只做参数校验和用例编排，不直接操作 SQLite
- `storage.py` 是 SQLite 唯一入口，不承载业务规则
- Agent 工具只允许只读操作，白名单硬编码在 `webapp/agent_tools.py`（ADR-003）
- API Key 只保存引用（`env:*` / `saved:*`），任何接口响应不得包含明文 Key（ADR-004）

> 完整说明见 `docs/design/architecture-overview.md`。接口契约见 `docs/design/api-spec.md`。

## 6. 代码约定（速查）

### 6.1 命名

- Python：函数 / 变量 snake_case，类 PascalCase，数据库字段 snake_case
- 前端 JS：函数 camelCase，文件名 kebab-case

### 6.2 文件组织

- 每个 `webapp/` 模块文件只承载一个清晰职责（api / storage / search / answers / ingestion 各管一件事）
- 可选依赖（pymupdf / jieba）必须用 `try/except ImportError` 引入，失败时提供明确降级
- legacy 前端 JS 按职责拆分：`api.js` / `state.js` / `ui.js` / `projects.js` / `answer.js`
- Vue 前端源码放在 `frontend/src/`，生产构建输出到 `webapp/static_dist/`，不得提交 `node_modules/` 或构建产物

### 6.3 明确禁用的模式

- 禁止 `api.py` 直接操作 SQLite（必须经 `storage.py`）
- 禁止在前端 JS 中写业务规则（只负责展示和 API 调用）
- 禁止在 Agent 工具中执行写操作或 shell 命令（只读白名单）
- 禁止硬编码 API Key、Token 或密码

> 完整规范见 `CONTRIBUTING.md § 4`。

## 7. 测试约定

| 类型 | 路径模式 | 运行命令 |
|------|----------|----------|
| Web MVP 单元/集成 | `tests/test_webapp/` | `.venv\Scripts\python.exe -m pytest tests/test_webapp -q` |
| Legacy 业务层回归 | `tests/test_application/ tests/test_domain/ tests/test_adapters/` | `.venv\Scripts\python.exe -m pytest tests/test_application tests/test_domain tests/test_adapters -q` |

测试优先级：API 契约 > 核心业务规则（检索 / 回答 / 导入） > 数据层集成 > 前端静态文件。

> 测试策略与最低覆盖要求见 `docs/guides/testing.md`。

## 8. 文档联动规则

AI 修改代码后**必须**同步更新对应文档，否则视为未完成：

| 代码变更 | 需同步更新的文档 |
|----------|----------------|
| 新增 / 修改功能行为 | `docs/features/<name>.md` |
| 接口签名变更 | `docs/design/api-spec.md` |
| 破坏性 API 变更 | `docs/design/api-spec.md` + `docs/design/api-changes.md` |
| 数据库表结构变更 | `docs/design/database-design.md` |
| 架构模式 / 模块边界变更 | `docs/design/architecture-overview.md` + `docs/adr/`（若触发 ADR 条件） |
| 新增 ADR | `docs/adr/README.md` 索引表追加一行 |
| 版本发布 | `CHANGELOG.md` |

已知问题或技术债直接写入 `docs/BACKLOG.md`，不写在代码注释里。

> ADR 触发条件见 `docs/README.md § 4`。

## 9. Plan 文件使用规则

### 9.1 两种 plan 产生方式

| 方式 | 典型场景 | plan 位置 | 命名格式 |
|------|----------|-----------|---------|
| **主动创建**（推荐） | AI 接到明确任务，按流程先建 plan 再动手 | `docs/plans/` | `{B-ID}-{slug}.md` |
| **工具自动生成** | Claude Code、superpowers 等工具自行生成 | 工具指定目录（如 `docs/superpowers/plans/`） | `{YYYY-MM-DD}-{slug}.md` |

**两种方式都必须触发 BACKLOG 同步**，区别只是同步的时机：主动创建时在动手前完成，工具自动生成时在文件落地后立即补做。

### 9.2 主动创建流程（任务启动四步）

凡涉及**代码改动**的任务，无论用户是否提供 BACKLOG ID，均先走以下四步再动手。
纯问答、只读查阅、单行拼写修复可免。

**Step 1 — 锁定 BACKLOG 条目**

打开 `docs/BACKLOG.md` § 5，按以下逻辑处理：

| 情况 | 操作 |
|------|------|
| 找到匹配的 `B-xxx` 条目 | 记录 ID，状态改为 `doing` |
| 无匹配条目 | 末尾新增一行，分配下一个 ID，状态置 `doing`，优先级与规模由 AI 估算填入 |

**Step 2 — 冲突扫描（创建 plan 前）**

扫描所有状态为 `Active` 或 `Interrupted` 的 plan 文件（`docs/plans/` 和 `docs/superpowers/plans/`），对比其 § 4 影响范围与本次任务的预期改动范围：

| 扫描结果 | 处理方式 |
|---------|---------|
| 无重叠 | 继续 Step 3 |
| 有重叠，冲突 plan 尚未完成 | 告知用户，选择下方四种解决策略之一，确认后再继续 |
| 有重叠，冲突 plan 已完成但未删除 | 视为无冲突，提醒清理残留 plan 文件 |

**四种解决策略**：

- **等待**：本任务暂缓，等冲突 plan 完成后再开始
- **合并**：将两个任务合并为一个 plan，统一执行
- **本 plan 覆盖**：本 plan 设计优先，冲突 plan 对应部分作废（在两个 plan 的 § 5.2 中互相注明）
- **分区**：明确划定各自负责的文件/模块边界，互不干涉

将扫描结果填入新 plan 的 § 5.2。

**Step 3 — 创建 plan 文件并完成文档关联**

在 `docs/plans/` 新建 `{B-ID}-{slug}.md`，**同一步骤内**完成：

1. 头部"关联 BACKLOG"填入 Step 1 的 B-ID
2. 头部"关联功能文档"：去 `docs/features/` 找对应文档；无则新建占位文件
3. 头部"关联设计文档"：按改动类型填（接口变更 → `design/api-spec.md`；DB 变更 → `design/database-design.md`；架构变更 → `design/architecture-overview.md`）
4. § 4"影响范围"填写将被修改的代码路径和文档路径
5. § 5.2 填入 Step 2 的冲突扫描结果
6. § 7"回流清单"逐行列出"改了什么 → 更新哪个文档"

**Step 4 — plan 路径写回 BACKLOG**

在该条目"说明"列追加 plan 文件的相对路径。

### 9.3 工具自动生成后的补同步（superpowers / Claude Code 等）

工具在 `docs/superpowers/plans/`（或其他目录）落地 plan 文件后，**在同一次对话中立即执行**：

1. **读取 plan 文件**，提取任务主题
2. **检索 `docs/BACKLOG.md` § 5**：
   - 找到语义匹配的条目 → 状态改 `doing`，说明列追加 plan 路径（相对于项目根目录）
   - 未找到 → 新建条目，填写标题/类型/优先级/规模，状态置 `doing`，说明列填入 plan 路径
3. **识别影响范围**，在 plan 文件中补写（若工具生成的内容缺失）
4. **将以上关联信息写入 plan 文件头部**（若工具生成时未填）

> 若当前对话无法确定语义匹配的 BACKLOG 条目，**禁止跳过**，应新建条目后再关联。

### 9.4 执行节奏（每个子任务的固定动作）

每完成 § 3 中的**一个任务**后，立即按顺序执行以下三步，不可跳过：

1. **勾选 § 3 对应条目**
2. **`git commit`**，message 简述本次完成的内容
3. **更新 plan § 9 状态快照**：填写最后更新时间、最新 commit hash、下一步任务

> 这三步的目的：在任意时刻被打断，损失的进度最多只有"当前子任务"。

遇到偏差或关键决策时，记入 plan § 8 执行记录。

### 9.5 任务中断处理

**主动中断**（有时间收尾）：

1. 将 plan 头部状态改为 `Interrupted`
2. 确认 § 9 状态快照已更新到最新
3. 补充 § 9 的"续任务须知"字段
4. 更新 BACKLOG：有外部阻塞 → `blocked`；仅未完成 → 保持 `doing`

**被动中断**（额度耗尽 / 强制停止，无收尾机会）：

- 无需任何操作——§ 9 快照已在上一个子任务完成时更新
- 恢复时：读 § 9 快照，检查 git log，从"下一步"字段指向的任务继续

**禁止在中断时删除 plan 文件**。

### 9.6 恢复未完成的 plan

新 session 开始时，若发现 `docs/plans/`（或 `docs/superpowers/plans/`）下存在 `状态：Interrupted` 的 plan 文件：

1. 读取 plan § 9 中断记录，了解当前状态和剩余任务
2. 读取 plan § 3，确认哪些任务已勾选、哪些待做
3. 检查代码状态（§ 9 中记录的分支/改动）是否与实际一致
4. 将 plan 头部状态改回 `Active`，继续执行剩余任务

### 9.7 完成流程

1. 确认回流清单全部勾选（每项已写入对应文档）
2. 重大技术决策 → 新建 ADR，更新 `docs/adr/README.md` 索引
3. 新发现的问题 → 写入 `docs/BACKLOG.md § 6`
4. BACKLOG 条目状态改为 `done`
5. **删除 plan 文件**（工具自动生成的文件同样需要删除）

> Plan 文件格式见 `docs/plans/plan-template.md`，生命周期规则见 `docs/plans/README.md`。

## 10. AI 操作边界

**可以自主执行**：

- 修改 `webapp/` 下的业务代码与测试
- 按上方"文档联动规则"同步文档
- 在 `docs/BACKLOG.md` 追加待办或已知问题条目
- 创建、更新、删除 `docs/plans/` 下的 plan 文件

**需先确认再执行**：

- 删除或重命名已有公共 API 接口
- 修改数据库 Schema（`webapp/storage.py` 中的 `CREATE TABLE` / `ALTER TABLE`）
- 变更 Agent 工具权限逻辑（白名单内容）
- 新增 ADR（需和用户确认决策内容）
- 修改 `src/`（Legacy）代码
- 向主分支直接推送

**禁止**：

- 硬编码 API Key、Token 或数据库密码
- 在 Agent 工具中执行写操作或 shell 命令
- 在接口响应中包含明文 API Key
- 在正式文档中混写当前已实现内容与未来规划（规划放 `BACKLOG.md`）
- 批量删除 `src/desktop/` 或 `docs/architecture/` 等历史目录（确认迁移完成前）
