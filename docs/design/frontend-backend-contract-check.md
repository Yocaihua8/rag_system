# 前后端契约对照分析

> 状态：Draft
> Owner：RAG 团队
> Last Updated：2026-07-30
> Scope：{{SCOPE}}
> Related：`api-spec.md`、{{RELATED_DOCS}}

本文档用于在联调、重构或问题排查时对照前端行为与后端接口契约。它不是接口权威源；接口字段、错误码和权限以 `api-spec.md` 为准。

## 1. 分析目标

| 项 | 内容 |
|----|------|
| 页面 / 流程 | {{PAGE_OR_FLOW}} |
| 前端入口 | `{{FRONTEND_ENTRY}}` |
| 后端模块 | `{{BACKEND_MODULE}}` |
| 触发原因 | {{REASON}} |
| 验收标准 | {{ACCEPTANCE_CRITERIA}} |

## 2. 前端行为

| 行为 | 触发点 | 当前请求 | 参数来源 | 期望结果 |
|------|--------|----------|----------|----------|
| {{BEHAVIOR}} | {{UI_TRIGGER}} | `{{CURRENT_REQUEST}}` | {{PARAM_SOURCE}} | {{EXPECTED_RESULT}} |

## 3. 现有接口

| 接口 | 当前契约 | 是否满足 | 备注 |
|------|----------|----------|------|
| `{{METHOD}} {{PATH}}` | {{CONTRACT_SUMMARY}} | 是 / 否 / 部分 | {{NOTE}} |

## 4. 缺失接口

| 缺口 | 影响 | 优先级 | 建议归属 |
|------|------|--------|----------|
| {{GAP}} | {{IMPACT}} | P0 / P1 / P2 | 前端 / 后端 / 产品 |

## 5. 修复建议

| 优先级 | 建议 | 影响文件 / 模块 | 验证方式 |
|--------|------|-----------------|----------|
| P0 | {{FIX_SUGGESTION}} | `{{PATH_OR_MODULE}}` | {{VERIFICATION}} |

## 6. 相关文件索引

### 前端

- `{{FRONTEND_FILE}}`：{{DESCRIPTION}}

### 后端

- `{{BACKEND_FILE}}`：{{DESCRIPTION}}

### 文档

- `api-spec.md`：接口契约权威源
- `{{RELATED_DOC}}`：{{DESCRIPTION}}

## 7. 结论

- 当前可直接使用的接口：{{AVAILABLE_APIS}}
- 需要补齐或修正的接口：{{MISSING_OR_CHANGED_APIS}}
- 本轮不处理的范围：{{OUT_OF_SCOPE}}
