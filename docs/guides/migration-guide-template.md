# 版本迁移指南模板

> 状态：Draft
> Owner：{{OWNER}}
> Last Updated：{{CURRENT_DATE}}
> From Version：{{OLD_VERSION}}
> To Version：{{NEW_VERSION}}
> Related：`../design/api-changes.md`

本文档面向使用方，说明如何从旧版本迁移到新版本。它不同于 `technical-migration-plan.md`：本文件关注“使用者怎么升级”，`technical-migration-plan.md` 关注“团队内部如何完成技术迁移”。

## 1. 迁移摘要

| 项 | 内容 |
|----|------|
| 迁移类型 | {{MIGRATION_CHANGE_TYPE}} |
| 推荐迁移窗口 | {{MIGRATION_WINDOW}} |
| 是否包含破坏性变更 | 是 / 否 |
| 是否需要停机 | 是 / 否 / 视部署方式 |
| 预计人工时间 | {{PERSON_HOURS_RANGE}} |
| 预计日历周期 | {{CALENDAR_DURATION_RANGE}} |

## 2. 适用对象

- 正在使用 `{{OLD_VERSION}}` 或更早版本的项目。
- 使用了以下能力的项目：{{FEATURE_OR_API_LIST}}。
- 不适用于：{{OUT_OF_SCOPE_OR_NA}}。

## 3. 旧版本与新版本差异

| 类别 | 旧版本 | 新版本 | 是否破坏性变更 |
|------|--------|--------|----------------|
| API | {{OLD_API}} | {{NEW_API}} | 是 / 否 |
| 配置 | {{OLD_CONFIG}} | {{NEW_CONFIG}} | 是 / 否 |
| 数据 | {{OLD_DATA}} | {{NEW_DATA}} | 是 / 否 |
| 行为 | {{OLD_BEHAVIOR}} | {{NEW_BEHAVIOR}} | 是 / 否 |

## 4. 迁移前检查

- [ ] 已确认当前版本号和部署环境。
- [ ] 已备份配置、数据和关键日志。
- [ ] 已确认回滚包、回滚脚本或回滚配置可用。
- [ ] 已通知受影响使用方和支持团队。
- [ ] 已确认外部依赖、第三方服务和权限配置满足新版本要求。

## 5. 迁移步骤

### 5.1 准备阶段

| 步骤 | 操作 | 验证 |
|------|------|------|
| 1 | {{PREPARE_ACTION_1}} | {{VERIFY_1}} |
| 2 | {{PREPARE_ACTION_2}} | {{VERIFY_2}} |

### 5.2 执行阶段

| 步骤 | 操作 | 验证 |
|------|------|------|
| 1 | {{MIGRATION_ACTION_1}} | {{VERIFY_1}} |
| 2 | {{MIGRATION_ACTION_2}} | {{VERIFY_2}} |
| 3 | {{MIGRATION_ACTION_3}} | {{VERIFY_3}} |

### 5.3 收尾阶段

| 步骤 | 操作 | 验证 |
|------|------|------|
| 1 | {{CLEANUP_ACTION_1}} | {{VERIFY_1}} |
| 2 | {{CLEANUP_ACTION_2}} | {{VERIFY_2}} |

## 6. 代码 / 配置示例

### 6.1 迁移前

```text
{{OLD_USAGE_OR_CONFIG_EXAMPLE}}
```

### 6.2 迁移后

```text
{{NEW_USAGE_OR_CONFIG_EXAMPLE}}
```

## 7. 验证清单

- [ ] 核心启动命令可执行：`{{START_COMMAND}}`
- [ ] 主流程测试通过：`{{SMOKE_TEST_COMMAND}}`
- [ ] 兼容性检查通过：`{{COMPATIBILITY_CHECK_COMMAND}}`
- [ ] 日志中没有新增错误：`{{LOG_CHECK_COMMAND}}`
- [ ] 指标、告警或用户反馈未出现异常。

## 8. 回滚方案

| 回滚触发条件 | 回滚动作 | 验证方式 | Owner |
|--------------|----------|----------|-------|
| {{CONDITION_1}} | {{ROLLBACK_ACTION_1}} | {{CHECK_1}} | {{OWNER}} |
| {{CONDITION_2}} | {{ROLLBACK_ACTION_2}} | {{CHECK_2}} | {{OWNER}} |

回滚后必须记录实际原因、影响范围、恢复时间和后续修复计划。

## 9. 常见问题

### Q1：{{QUESTION}}

答：{{ANSWER}}

### Q2：{{QUESTION}}

答：{{ANSWER}}

## 10. 升级支持

| 渠道 | 适用场景 | 响应说明 |
|------|----------|----------|
| {{CHANNEL_1}} | {{SCENARIO_1}} | {{RESPONSE_RULE_1}} |
| {{CHANNEL_2}} | {{SCENARIO_2}} | {{RESPONSE_RULE_2}} |
