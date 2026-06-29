# B-117 MCP / 插件能力研究

> 状态：Active
> 创建时间：2026-06-30
> 创建方：Codex
> 关联 BACKLOG：B-117
> 关联功能文档：docs/features/agent-tooling-mcp-research.md
> 关联设计文档：docs/design/permission-matrix.md, docs/design/system-design-overview.md

## 1. 目标

完成 MCP / 插件能力研究，给出 Knowledge Island 是否接入、以何种安全边界接入的结论。研究只产出文档和后续任务拆分，不接入插件市场，不开放任意命令执行，不修改现有 Agent 工具权限逻辑。

## 2. 前置条件

- 已读取 `AGENTS.md`、`README.md`、`docs/README.md`、`docs/BACKLOG.md`、`docs/requirements/project-background-and-scope.md`、`docs/requirements/functional-modules.md`、`docs/design/permission-matrix.md`、`docs/design/system-design-overview.md`。
- 已检查 `webapp/agent_tools.py` 与 `tests/test_webapp/test_agent_tools.py`，确认当前只读工具白名单和审计边界。
- 已通过 Context7 查询 MCP 官方规范仓库，关注 `tools/list`、`tools/call`、resources、prompts、tool annotations 和安全要求。
- 当前工作区存在非 B-117 既有未提交改动；执行时只暂存 B-117 相关文件和 `docs/BACKLOG.md` 的 B-117 hunk。

## 3. 任务拆解

- [x] 梳理当前 Agent 工具边界与 MCP 能力映射，形成研究文档初稿。
- [x] 同步正式文档索引和权限/系统设计边界，运行文档验证。
- [ ] 同步 BACKLOG 完成状态，删除本 plan。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 文档 | `docs/features/agent-tooling-mcp-research.md` | 新增 |
| 文档 | `docs/design/permission-matrix.md` | 修改 |
| 文档 | `docs/design/system-design-overview.md` | 修改 |
| 文档 | `docs/README.md` | 修改 |
| 文档 | `docs/BACKLOG.md` | 修改 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | 无直接依赖 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | N/A | N/A |

创建本 plan 时扫描到 `docs/superpowers/plans/` 下 3 个旧 plan，均为 legacy PySide6 / 旧领域模型计划，不涉及当前 Web MVP Agent 工具边界、MCP 研究文档或本次影响范围。

## 6. 完成标准

- [ ] `docs/features/agent-tooling-mcp-research.md` 给出明确研究结论、接入边界、拒绝范围和后续拆分。
- [ ] 正式文档继续明确不开放插件市场、shell、任意命令执行或未经允许的自动工具调用。
- [ ] 运行文档相关验证命令并记录结果。
- [ ] 相关文档已同步（见下方"回流清单"）。
- [ ] BACKLOG 条目 `B-117` 状态已更新为 `done`。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| MCP / 插件能力研究结论、准入边界、拒绝范围 | `docs/features/agent-tooling-mcp-research.md` | [x] |
| 只读工具与 MCP 未来接入的权限边界 | `docs/design/permission-matrix.md` | [x] |
| 系统设计中的 Agent 工具扩展边界 | `docs/design/system-design-overview.md` | [x] |
| 新研究文档索引 | `docs/README.md` | [x] |
| B-117 完成状态 | `docs/BACKLOG.md` | [ ] |

## 8. 执行记录

- 2026-06-30：B-117 明确为 research 小项，只做文档结论和后续任务拆分，不改运行时代码和 API。
- 2026-06-30：新增 `docs/features/agent-tooling-mcp-research.md`，结论为当前不接入插件市场或任意 MCP server；后续仅可按 allowlist、只读、手动触发、审计记录方式研究最小适配层。
- 2026-06-30：同步 `docs/README.md`、`docs/features/README.md`、`docs/design/permission-matrix.md`、`docs/design/system-design-overview.md`；验证 `.venv\Scripts\python.exe -m pytest tests\test_webapp\test_docs_contract.py -q` 通过 23 项，`.venv\Scripts\python.exe scripts\check_docs_consistency.py` 通过。

## 9. 状态快照

- **最后更新**：2026-06-30 00:00
- **进度**：已完成 2 / 3 项（见 § 3 勾选状态）
- **最新 commit**：`b97cb9e` — `docs: 完成 MCP 插件能力研究初稿`
- **代码状态**：`fix/b-08-concurrent-index`；工作区存在非 B-117 既有改动，需精确暂存
- **下一步**：同步 BACKLOG 完成状态，删除本 plan
- **续任务须知**：只暂存 B-117 相关文件和 `docs/BACKLOG.md` 的 B-117 hunk
