# 问题复盘 {{INCIDENT_TITLE}}

> 状态：Draft
> Author：{{AUTHOR}}
> Date：{{CURRENT_DATE}}
> Related：{{RELATED_DOCS_OR_ISSUES}}

本文档用于记录一次已经收敛的问题复盘。普通 devlog 记录日常进展；问题复盘记录一次异常、事故、重大缺陷或复杂排障的背景、根因、最终方案和防复发动作。

## 1. 背景

| 项 | 内容 |
|----|------|
| 现象 | {{SYMPTOM}} |
| 影响范围 | {{IMPACT}} |
| 首次发现时间 | {{CURRENT_LOCAL_DATETIME}} |
| 恢复时间 | {{CURRENT_LOCAL_DATETIME}} |
| 当前状态 | 已恢复 / 已缓解 / 观察中 / 待修复 |

## 2. 时间线

| 时间 | 事件 | 处理人 |
|------|------|--------|
| {{CURRENT_LOCAL_DATETIME}} | {{EVENT}} | {{OWNER}} |

## 3. 失败方案

| 方案 | 为什么失败 | 学到什么 |
|------|------------|----------|
| {{FAILED_ATTEMPT}} | {{FAIL_REASON}} | {{LESSON}} |

## 4. 最终方案

说明最终采用的修复或缓解方案，以及为什么它能解决问题。

- 方案摘要：{{FINAL_SOLUTION}}
- 关键约束：{{CONSTRAINTS}}
- 验证方式：{{VERIFICATION}}

## 5. 根因

| 类型 | 根因 |
|------|------|
| 直接原因 | {{DIRECT_CAUSE}} |
| 深层原因 | {{ROOT_CAUSE}} |
| 未提前发现的原因 | {{WHY_NOT_CAUGHT}} |

## 6. 防复发

| 动作 | 类型 | 负责人 | 截止日期 | 跟踪 |
|------|------|--------|----------|------|
| {{ACTION}} | 测试 / 监控 / 文档 / 流程 / 架构 | {{OWNER}} | {{CURRENT_DATE}} | BACKLOG-{{ID}} |

## 7. BACKLOG / ADR 回流

- 需要进入 BACKLOG 的事项：{{BACKLOG_ITEMS_OR_NA}}
- 需要新增或更新 ADR 的决策：{{ADR_ITEMS_OR_NA}}
- 需要同步的正式文档：{{DOCS_TO_UPDATE_OR_NA}}

## 8. 结论

- 已解决：{{RESOLVED}}
- 仍需跟进：{{FOLLOW_UP}}
- 不再采用的做法：{{DEPRECATED_APPROACH}}
