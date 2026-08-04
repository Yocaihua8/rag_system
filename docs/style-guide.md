# 文档写作规范

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-02
> Scope：`docs/` 当前文档和模板
> Related：`../README.md`、`README.md`、`features/feature-template.md`、`adr/ADR-000-template.md`、`design/rfc-template.md`、`plans/plan-template.md`

## 原则

- 先写当前结论，再写必要背景；避免按提交时间堆叠正文。
- 当前实现、未来规划和历史事实分开。未来只进 BACKLOG，完成历史只进 CHANGELOG/Git。
- 以源码、配置、Schema 和测试校准事实；无法确认时写 `TBD`、`N/A` 或“待确认”。
- 不引用已删除目录、临时产物、个人绝对路径或本机凭证。
- 命令必须从仓库根可执行，并与当前依赖/目录一致。

## 元数据

活动 Markdown 文档在标题后包含：

```text
> 状态：Active
> Owner：RAG 团队
> Last Updated：YYYY-MM-DD
> Scope：...
> Related：...
```

ADR 使用 Accepted/Proposed 等决策状态；模板可保留 `{{PLACEHOLDER}}`，普通活动文档不得残留占位符。

## 链接与路径

- Markdown 链接优先使用相对当前文件的路径；代码/配置引用使用仓库根相对路径。
- 移动文件时同批更新索引、Related、正文引用和文档检查规则。
- `requirements`、`design`、`features`、`adr`、`guides` 和 `plans` 保持扁平，不再按前端、后端、集成或运维建立专题子目录。
- `devlog` 是唯一允许按 `YYYY/MM/` 嵌套的标准目录；根目录只保留 README 和模板，日报文件名必须与年月目录一致。

## 模板

模板按职责放在 [`features/feature-template.md`](features/feature-template.md)、[`adr/ADR-000-template.md`](adr/ADR-000-template.md)、[`design/rfc-template.md`](design/rfc-template.md)、[`plans/plan-template.md`](plans/plan-template.md)、[`devlog/devlog-template.md`](devlog/devlog-template.md)、[`devlog/postmortem-template.md`](devlog/postmortem-template.md) 以及 `guides/` 下的贡献/集成模板。使用模板后替换全部占位符，并删除不适用章节；不得把模板本身当作项目事实。

## 验证

```powershell
pwsh -NoProfile -File scripts/check-placeholders.ps1
pwsh -NoProfile -File scripts/check-doc-links.ps1
.\.venv\Scripts\python.exe scripts/check_docs_consistency.py
```

文档门禁不读取历史例外目录，因为历史文档已从活动树删除。
