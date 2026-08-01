# AI 任务计划

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：`docs/plans/` 中 Active/Interrupted plan 的生命周期
> Related：`../BACKLOG.md`、`plan-template.md`、`../../AGENTS.md`

Plan 是执行期间的临时恢复点，不是完成历史。完成事实进入 `CHANGELOG.md` 与 Git；任务完成后删除 plan。

## 当前计划

- [`B-171-interactive-knowledge-learning.md`](B-171-interactive-knowledge-learning.md)：Active；语义移植逐知识点交互学习与只读 SQL 练习。

## 创建

1. 在 [`../BACKLOG.md`](../BACKLOG.md) 找到或新建 `B-xxx`，状态设为 `doing`。
2. 扫描本目录所有 `Active` / `Interrupted` plan 的影响范围。
3. 有重叠时让用户选择等待、合并、覆盖或分区；把结论写入新 plan。
4. 复制 [`plan-template.md`](plan-template.md) 为 `{B-ID}-{slug}.md`。
5. 填写关联 BACKLOG、功能/设计文档、影响范围、回流清单和状态快照。
6. 把 plan 相对路径写回 BACKLOG。

## 执行

每完成一个任务：

1. 勾选任务；
2. 创建聚焦该阶段的 Git commit；
3. 在状态快照记录 commit、工作区、进度和下一步。

出现偏差或关键决策写入执行记录；重大、长期且跨模块的决策另建 ADR。

## 中断与恢复

- 主动中断：状态设为 `Interrupted`，更新最后 commit、下一步和续任务须知；BACKLOG 保持 `doing` 或按真实外部阻塞设 `blocked`。
- 被动中断：下次从最后已提交快照继续，不重做已完成阶段。
- 恢复前核对 plan、Git log 和工作区；一致后状态改回 `Active`。

## 完成

1. 完成回流清单和必要 ADR/索引；
2. 新问题写入 BACKLOG；
3. 对使用者/维护者有意义的完成事实写入 CHANGELOG；
4. 从 BACKLOG 移除完成条目；
5. 删除 plan。

不把完成 plan 迁入其他历史目录，不建立 DevLog 或 readiness 快照。
