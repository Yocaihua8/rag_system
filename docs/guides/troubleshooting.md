# 故障排查模板

> 状态：Draft
> Owner：RAG 团队
> Last Updated：2026-07-30
> Related：`runbook.md`、`support-policy.md`

本文档用于沉淀常见故障的排查路径。它不是事故复盘；若问题已经造成较大影响或需要根因分析，排查后应补充 `../devlog/postmortem-template.md`。

## 1. 使用方式

1. 先定位现象和影响范围。
2. 按可能原因逐项执行检查命令。
3. 只执行与当前环境匹配的解决步骤。
4. 无法确认根因时，按升级路径收集信息并交给对应 Owner。

## 2. 快速分级

| 级别 | 判断标准 | 处理时限 | 升级对象 |
|------|----------|----------|----------|
| P0 | 主流程不可用、数据风险、安全风险 | {{TIME_LIMIT}} | {{ESCALATION_OWNER}} |
| P1 | 重要功能受影响，有临时规避 | {{TIME_LIMIT}} | {{ESCALATION_OWNER}} |
| P2 | 局部异常或体验问题 | {{TIME_LIMIT}} | {{ESCALATION_OWNER}} |
| P3 | 咨询、低风险问题 | {{TIME_LIMIT}} | {{ESCALATION_OWNER}} |

## 3. 排查条目模板

### 3.1 {{PROBLEM_TITLE}}

**现象**：

- {{SYMPTOM_1}}
- {{SYMPTOM_2}}

**影响范围**：

| 维度 | 内容 |
|------|------|
| 环境 | {{ENVIRONMENT}} |
| 用户 / 租户 | {{AFFECTED_USERS}} |
| 功能 / 接口 | {{AFFECTED_FEATURES_OR_APIS}} |
| 开始时间 | {{START_TIME}} |

**可能原因**：

| 可能原因 | 判断依据 | 检查命令 |
|----------|----------|----------|
| {{CAUSE_1}} | {{SIGNAL_1}} | `{{CHECK_COMMAND_1}}` |
| {{CAUSE_2}} | {{SIGNAL_2}} | `{{CHECK_COMMAND_2}}` |
| {{CAUSE_3}} | {{SIGNAL_3}} | `{{CHECK_COMMAND_3}}` |

**解决步骤**：

1. {{RESOLUTION_STEP_1}}
2. {{RESOLUTION_STEP_2}}
3. {{RESOLUTION_STEP_3}}

**验证方式**：

- [ ] `{{VERIFY_COMMAND_1}}`
- [ ] {{MANUAL_VERIFY_STEP}}
- [ ] 日志 / 指标恢复正常：{{LOG_OR_METRIC_EXPECTATION}}

**升级路径**：

| 条件 | 升级给谁 | 需要附带的信息 |
|------|----------|----------------|
| {{ESCALATION_CONDITION_1}} | {{OWNER_1}} | {{REQUIRED_INFO_1}} |
| {{ESCALATION_CONDITION_2}} | {{OWNER_2}} | {{REQUIRED_INFO_2}} |

## 4. 收集信息清单

排查无法在本地闭环时，至少收集以下信息：

- 时间范围：{{TIME_RANGE}}
- 环境：{{ENVIRONMENT}}
- 版本号 / commit：{{VERSION_OR_COMMIT}}
- 请求 ID / Trace ID：{{TRACE_ID_OR_NA}}
- 错误日志：{{LOG_PATH_OR_QUERY}}
- 已尝试步骤：{{ATTEMPTED_STEPS}}
- 是否可复现：{{REPRODUCIBLE}}

## 5. 防复发回流

- 能修复的问题：创建或更新 `../BACKLOG.md` 条目。
- 需要设计决策的问题：创建 RFC 或 ADR。
- 造成事故的问题：填写 `../devlog/postmortem-template.md` 并回流行动项。
- 文档缺口：更新本文件或对应 runbook。
