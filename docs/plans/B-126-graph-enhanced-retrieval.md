# B-126 Graph-enhanced 检索 Implementation Plan

> 状态：Active
> 创建时间：2026-06-29
> 创建方：Codex
> 关联 BACKLOG：B-126
> 关联功能文档：docs/features/graph-enhanced-retrieval.md
> 关联设计文档：docs/design/database-design.md, docs/design/api-spec.md, docs/design/architecture-overview.md

## 1. 目标

在 Web MVP 现有 BM25 + 向量 + 可选 reranker 检索流程中接入只读 Graph-enhanced 候选扩展：当数据库存在 B-48 legacy `graph_nodes` / `graph_edges` 数据时，基于初始命中 chunk 的来源路径映射图谱节点，并补充一跳相邻节点对应的来源 chunk；图谱表不存在时保持现有检索行为不变。

## 2. 前置条件

- 已读取 `AGENTS.md`、`docs/README.md`、`CONTRIBUTING.md`、`docs/guides/testing.md`。
- 已确认 `docs/BACKLOG.md` 中 B-126 存在并已置为 `doing`。
- 已确认当前 Web MVP `webapp/storage.py` 不初始化 `graph_nodes` / `graph_edges`；本任务不修改 SQLite schema。
- 已运行基线：`.venv\Scripts\python.exe -m pytest tests\test_webapp\test_search.py -q`，20 passed。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] Task 1：锁定 B-126、创建 plan 与功能文档占位。
- [ ] Task 2：补充只读图谱存储查询与红灯测试。
- [ ] Task 3：把图谱候选扩展接入 `search_documents()`，并保持 reranker / Qdrant 行为兼容。
- [ ] Task 4：同步正式文档、完成验证、关闭 BACKLOG 并删除本 plan。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `webapp/storage.py` | 新增只读图谱候选查询方法；不修改 schema |
| 代码 | `webapp/search.py` | 在候选生成后补充 graph 关联 chunk |
| 代码 | `webapp/models.py` | 如有必要扩展 SearchHit 可观察字段 |
| 测试 | `tests/test_webapp/test_search.py` | 增加 Graph-enhanced 检索红绿测试 |
| 文档 | `docs/features/graph-enhanced-retrieval.md` | 新增并回流正式行为说明 |
| 文档 | `docs/design/api-spec.md` | 同步检索结果字段与行为说明 |
| 文档 | `docs/design/database-design.md` | 澄清 graph 表当前为 legacy 兼容只读输入 |
| 文档 | `docs/design/architecture-overview.md` | 同步检索业务层能力 |
| 文档 | `docs/BACKLOG.md` | B-126 状态从 doing 收口到 done |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | 本任务不依赖其他未完成 plan。 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | 已扫描 `docs/plans/` 与 `docs/superpowers/plans/`；旧 superpowers plan 面向 legacy `src/` / desktop，不覆盖 Web MVP `webapp/search.py`、`webapp/storage.py`。 | N/A |

## 6. 完成标准

全部勾选后方可删除本 plan 文件：

- [ ] 功能行为符合 `docs/features/graph-enhanced-retrieval.md` 的业务规则。
- [ ] 图谱表不存在时现有检索测试保持通过。
- [ ] 图谱表存在时，命中节点的一跳相邻节点来源可作为 graph 候选返回。
- [ ] reranker 接收 graph 扩展后的候选池，且默认禁用 reranker 时排序兼容现有行为。
- [ ] 相关文档已同步（见下方"回流清单"）。
- [ ] BACKLOG 条目 `B-126` 状态已更新为 `done`。

## 7. 回流清单

删除本文件前，确认以下内容已写入正式文档：

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| Graph-enhanced 检索启用条件、降级行为、结果字段 | `docs/features/graph-enhanced-retrieval.md` | [ ] |
| 检索 API hits/sources 中 graph 字段与行为说明 | `docs/design/api-spec.md` | [ ] |
| `graph_nodes` / `graph_edges` 在 Web MVP 中的只读兼容边界 | `docs/design/database-design.md` | [ ] |
| 检索业务层包含图谱候选扩展但不新增服务依赖 | `docs/design/architecture-overview.md` | [ ] |

## 8. 执行记录

- 2026-06-29：确认 B-48 图谱表落点位于 `archive/src-desktop-legacy/`，当前 Web MVP schema 未初始化图谱表；为遵守“修改数据库 schema 需先确认”的项目规则，本任务采用只读兼容接入。

## 9. 状态快照

- **最后更新**：2026-06-29 19:25
- **进度**：已完成 1 / 4 项（见 § 3 勾选状态）
- **最新 commit**：`a9afed2` — docs: 启动 B-126 图谱检索计划
- **代码状态**：main；Task 1 已提交；未修改代码行为
- **下一步**：Task 2：补充只读图谱存储查询与红灯测试
- **续任务须知**：不得修改 `webapp/storage.py` schema；图谱表不存在时必须 no-op。
