# B-147 文档一致性检查对齐 devlog 目录结构

> 状态：Active
> 创建时间：2026-05-28
> 创建方：Codex
> 关联 BACKLOG：B-147
> 关联功能文档：docs/guides/testing.md, docs/README.md
> 关联设计文档：N/A

## 1. 目标

修复审计发现的文档一致性检查漂移：当前正式文档已使用 `docs/devlog/` 目录承载开发过程日志，但 `scripts/check_docs_consistency.py` 和根 README 仍引用已删除的 `docs/DEVLOG.md`。

完成后，文档一致性脚本应以当前 `docs/devlog/` 目录为准，不再要求已删除的聚合文件；根 README 的文档入口也应与当前结构一致。

## 2. 前置条件

- 已读取 `AGENTS.md`
- 已读取 `docs/README.md`
- 已读取 `docs/BACKLOG.md`
- 已确认当前工作区无未提交改动

## 3. 任务拆解

- [x] 补充文档一致性回归测试并确认当前失败
- [ ] 修复 devlog 目录一致性脚本与根 README 入口
- [ ] 完成验证并收口 B-147 文档状态

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `scripts/check_docs_consistency.py` | 修改 |
| 测试 | `tests/backend/test_docs_consistency.py` | 新增 |
| 文档 | `README.md` | 修改 |
| 文档 | `docs/BACKLOG.md` | 修改 |
| 文档 | `docs/plans/B-147-docs-consistency-devlog.md` | 新增 / 删除 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | N/A |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | N/A | N/A |

创建本 plan 时扫描 `docs/plans/` 与 `docs/superpowers/plans/`，未发现状态为 `Active` 或 `Interrupted` 且与本任务影响范围重叠的执行中 plan。`docs/superpowers/plans/` 下存在历史残留 plan，但未标记为 Active / Interrupted，本任务不处理。

## 6. 完成标准

- [ ] 回归测试覆盖 `docs/devlog/` 目录结构，不再要求 `docs/DEVLOG.md`
- [ ] `scripts/check_docs_consistency.py` 运行通过
- [ ] 根 README 文档入口不再指向 `docs/DEVLOG.md`
- [ ] 相关测试和 `git diff --check` 通过
- [ ] BACKLOG 条目 `B-147` 状态已更新为 `done`

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 文档过程日志入口从 `docs/DEVLOG.md` 改为 `docs/devlog/` | `README.md` | [ ] |
| B-147 修复状态 | `docs/BACKLOG.md` | [ ] |

## 8. 执行记录

- 2026-05-28：审计确认 `scripts/check_docs_consistency.py` 因缺少已删除的 `docs/DEVLOG.md` 失败；当前正式结构由 `docs/README.md` 和 `docs/template-mapping.md` 指向 `docs/devlog/`。

## 9. 状态快照

- **最后更新**：2026-05-28 00:00
- **进度**：已完成 1 / 3 项（见 § 3 勾选状态）
- **最新 commit**：待提交 — 补充 B-147 回归测试
- **代码状态**：`fix/b-147-docs-consistency`；已建立 B-147 plan 和红灯测试
- **下一步**：修复 devlog 目录一致性脚本与根 README 入口
- **续任务须知**：红灯命令 `.venv\Scripts\python.exe -m pytest tests\backend\test_docs_consistency.py -q` 失败 2 项，分别指向 `docs/DEVLOG.md` 旧聚合文件依赖和 README 旧入口。
