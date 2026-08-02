# DevLog 开发日志

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-02
> Scope：按日记录开发过程、问题、临时决定和下一步
> Related：`../BACKLOG.md`、`../adr/README.md`、`../../CHANGELOG.md`、`../plans/README.md`

DevLog 记录实际开发过程，不替代当前规格、BACKLOG、ADR、CHANGELOG 或 Git 历史。

## 1. 职责边界

| 文档 | 内容 | 更新节奏 |
|------|------|----------|
| `../BACKLOG.md` | 未完成任务、已知问题和技术债 | 状态变化时 |
| `YYYY/MM/YYYY-MM-DD.md` | 当天实际完成、问题、临时决定和下一步 | 每个开发日追加 |
| `../adr/*.md` | 已定稿且跨模块的架构决策 | 决策确认时 |
| `../../CHANGELOG.md` | 对使用者或维护者有意义的完成变化 | 阶段或版本完成时 |
| Git | 可恢复的文件级实现历史 | 每个聚焦阶段 |

## 2. 写作规则

- 只写已发生的过程事实，不把目标或计划写成已经实现。
- 当天多次更新只追加到同一个文件，不新建第二份日报。
- 问题需要继续跟踪时写入 BACKLOG，DevLog 只保留 ID 和当日处置。
- 重大决策提升为 ADR，DevLog 只记录 ADR 编号和当日影响。
- 使用者可感知的完成事实进入 CHANGELOG，不在 DevLog 重复写发布说明。
- 单份日志保持在 150 行以内；复杂故障使用问题复盘模板。
- 不记录 API Key、Token、密码、用户数据或不必要的绝对路径。

## 3. 路径与命名

- 日报：`docs/devlog/YYYY/MM/YYYY-MM-DD.md`。
- 同一天只保留一个日报文件。
- 根目录只允许 `README.md`、`devlog-template.md` 和 `postmortem-template.md`。
- 问题复盘：`docs/devlog/YYYY/MM/YYYY-MM-DD-incident-slug-postmortem.md`。
- 日志永久留在年月目录，不创建额外 archive。

## 4. 模板

- 日报使用 [`devlog-template.md`](devlog-template.md)。
- 复杂故障复盘使用 [`postmortem-template.md`](postmortem-template.md)。
