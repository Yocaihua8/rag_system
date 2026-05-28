# Plans — AI 任务计划

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-26

本目录存放 AI 编码助手在执行 BACKLOG 任务时生成的**任务计划文件**。

## 1. 定位与边界

| 文档 | 面向 | 内容 | 生命周期 |
|------|------|------|----------|
| `../BACKLOG.md` | 团队 | 要做什么、优先级、规模 | 长期维护 |
| `../adr/*.md` | 团队 | 为什么这样设计 | 永久保留 |
| `../devlog/*.md` | 开发者 | 做了什么、卡在哪 | 按里程碑归档 |
| `./*.md`（本目录） | AI + 执行者 | 怎么做、任务拆解、完成标准 | **任务完成后删除** |

**一句话区分**：BACKLOG 是"要做什么"，ADR 是"为什么这么定"，DevLog 是"做到哪了"，**Plan 是"这次怎么做"**。

## 2. 文件命名规范

**主动创建**（推荐，B-ID 作为前缀，关联关系从文件名即可看出）：

```text
{B-ID}-{slug}.md
```

示例：`B-038-eval-question-model.md`、`B-125-reranker-integration.md`

**工具自动生成**（Claude Code、superpowers 等工具产生，接受日期命名）：

```text
{YYYY-MM-DD}-{slug}.md
```

示例：`2026-05-07-student-dashboard.md`（归入 `docs/superpowers/plans/`）

> 命名格式不同，但**BACKLOG 同步要求完全相同**。工具生成后必须补做 `AGENTS.md § 9.3` 的同步操作。

## 3. 生命周期

**主动创建路径**：

```
BACKLOG 条目 todo
      │
      ▼  AI 主动创建 plan，同步更新 BACKLOG 状态和说明列
BACKLOG doing，plan Active
      │
      ▼  执行完成，回流清单全部勾选
代码合并，文档同步
      │
      ▼  plan 删除，BACKLOG 置 done
```

**工具自动生成路径**（superpowers / Claude Code 等）：

```
工具落地 plan 文件（docs/superpowers/plans/ 或其他目录）
      │
      ▼  AI 在同一对话中立即检索 BACKLOG
      │   ├── 有匹配条目 → 状态改 doing，说明列填 plan 路径
      │   └── 无匹配条目 → 新建条目，填路径
      ▼
BACKLOG doing，plan 与 BACKLOG 双向关联
      │
      ▼  执行完成，回流清单全部勾选
代码合并，文档同步
      │
      ▼  plan 删除，BACKLOG 置 done
```

**关键原则**：不管 plan 怎么产生，完成即删除；定稿内容必须在删除前回流到正式文档。

## 4. 何时必须回流

删除 plan 文件前，检查以下事项：

| 内容 | 回流目标 |
|------|----------|
| 功能行为变更 | `../features/<name>.md` |
| 接口变更 | `../design/api-spec.md` |
| 数据库结构变更 | `../design/database-design.md` |
| 重大技术决策 | `../adr/<ADR-ID>.md` + `../adr/README.md` 索引 |
| 遇到的问题与规避 | `../BACKLOG.md § 6`（已知问题）或 `../devlog/` |

## 5. 模板

新建计划时复制 `plan-template.md`，按模板字段填写。
完整执行规则见 `../../AGENTS.md § 9`。
