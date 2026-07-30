# 运维手册 Runbook

> 状态：Draft
> Owner：RAG 团队
> Last Updated：2026-07-30
> Scope：{{SCOPE}}
> Related：{{RELATED_DOCS}}

用于**值班同学在压力下能照抄的操作手册**。原则：每一步都是可直接执行的命令或链接，不放长篇背景。

## 1. 服务清单

| 服务 | 角色 | 部署位置 | 健康检查 | Owner |
|------|------|----------|----------|-------|
| {{SERVICE_NAME}} | 核心/边缘/批 | {{HOST_OR_CLUSTER}} | {{HEALTH_CHECK_URL}} | RAG 团队 |

## 2. 常用链接

| 名称 | URL |
|------|-----|
| 监控面板 | {{MONITORING_URL}} |
| 日志查询 | {{LOG_URL}} |
| CI / 部署 | {{CI_URL}} |
| 告警配置 | {{ALERT_URL}} |
| 错误追踪（Sentry 等） | {{ERROR_TRACKING_URL}} |

## 3. 部署与回滚

### 3.1 常规部署

```bash
{{DEPLOY_COMMAND}}
```

### 3.2 回滚到上一版本

```bash
{{ROLLBACK_COMMAND}}
```

### 3.3 热修复流程

参考 `release-process.md` § 回滚方案。

## 4. 告警响应手册

每条告警**必须**配一条处置流程。

### 4.1 {{ALERT_NAME}}

- **触发条件**：{{TRIGGER_CONDITION}}
- **严重级别**：P0 / P1 / P2
- **立即行动**：
  1. {{STEP_1}}
  2. {{STEP_2}}
- **升级路径**：若 {{CONDITION}}，联系 {{ESCALATION_CONTACT}}
- **误报判定**：{{FALSE_POSITIVE_RULE}}

## 5. 常见故障与处置

### 5.1 {{ISSUE_NAME}}

- **现象**：{{SYMPTOM}}
- **快速确认命令**：
  ```bash
  {{DIAGNOSTIC_COMMAND}}
  ```
- **临时缓解**：{{MITIGATION}}
- **根因修复**：{{ROOT_CAUSE_FIX}}
- **关联 Issue / ADR**：{{LINK}}

## 6. 容量与扩缩容

| 资源 | 当前水位 | 告警阈值 | 扩容方式 |
|------|----------|----------|----------|
| {{RESOURCE}} | {{CURRENT}} | {{THRESHOLD}} | {{SCALE_METHOD}} |

## 7. 值班交接模板

```markdown
日期：2026-07-30
交班人：{{HANDOVER_FROM}}
接班人：{{HANDOVER_TO}}

### 进行中问题
- ...

### 待观察
- ...

### 本次已处理
- ...
```

## 附录：填写示例

````markdown
# 运维手册 Runbook

## 1. 服务清单

| 服务 | 角色 | 部署位置 | 健康检查 | Owner |
|------|------|----------|----------|-------|
| order-service | 核心 | k8s/order-prod | `/actuator/health` | 张三 |

## 3.1 常规部署

```bash
kubectl rollout restart deployment/order-service -n prod
```

## 4.1 订单接口错误率升高

- **触发条件**：5 分钟内 5xx 比例 > 5%
- **严重级别**：P1
- **立即行动**：
  1. 查看应用日志与监控面板
  2. 如为新版本引起，执行回滚
````
