# {{INTEGRATION_NAME}} 接入手册

> 状态：Draft
> Owner：{{OWNER}}
> Last Updated：{{CURRENT_DATE}}
> Scope：{{SCOPE}}
> Related：`docs/design/api-spec.md`、{{RELATED_DOCS}}

本文档用于指导调用方完成一次可验证的接口或服务接入。接口字段与错误码的权威源仍是 `docs/design/api-spec.md`；本文只说明如何落地接入、联调和排错。

## 1. 接入目标

| 项 | 内容 |
|----|------|
| 接入对象 | {{API_OR_SERVICE_NAME}} |
| 调用方 | {{CALLER}} |
| 使用场景 | {{SCENARIO}} |
| 成功标准 | {{SUCCESS_CRITERIA}} |
| 不包含内容 | {{OUT_OF_SCOPE}} |

## 2. 环境

| 环境 | Base URL / 地址 | 用途 | 注意事项 |
|------|-----------------|------|----------|
| 开发 | {{DEV_ENDPOINT}} | 本地联调 | {{DEV_NOTE}} |
| 测试 | {{TEST_ENDPOINT}} | 测试验收 | {{TEST_NOTE}} |
| 生产 | {{PROD_ENDPOINT}} | 正式调用 | {{PROD_NOTE}} |

不要在本文档中写入密钥、token、密码或真实生产凭证。敏感配置只写获取方式和保管位置。

## 3. 认证

| 项 | 说明 |
|----|------|
| 认证方式 | {{AUTH_METHOD}} |
| 凭证位置 | {{TOKEN_LOCATION}} |
| 过期策略 | {{EXPIRATION_POLICY}} |
| 401 / 403 处理 | {{AUTH_ERROR_HANDLING}} |

## 4. 接口清单

| 接口 / 服务 | 方法 | 路径 / Topic | 用途 | 权限 |
|-------------|------|--------------|------|------|
| {{API_NAME}} | {{METHOD}} | `{{PATH}}` | {{PURPOSE}} | {{ROLE}} |

## 5. 请求示例

```http
{{METHOD}} {{PATH}} HTTP/1.1
Authorization: {{AUTH_HEADER_EXAMPLE}}
Content-Type: application/json
```

```json
{
  "field": "{{VALUE}}"
}
```

## 6. 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

## 7. 错误码

| 错误码 | 场景 | 调用方处理建议 |
|--------|------|----------------|
| {{ERROR_CODE}} | {{ERROR_SCENARIO}} | {{HANDLING_SUGGESTION}} |

## 8. 联调检查

- [ ] 调用方已确认目标环境地址
- [ ] 认证凭证获取方式已确认
- [ ] 成功响应已按 `data` 结构解析
- [ ] 失败响应已按错误码分支处理
- [ ] 重试、超时、取消、重复提交策略已确认
- [ ] 日志中能定位请求 ID / trace ID

## 9. 故障排查

| 现象 | 优先检查 | 负责人 |
|------|----------|--------|
| {{SYMPTOM}} | {{CHECKLIST}} | {{OWNER}} |

## 10. 变更记录

| 日期 | 变更 | 影响范围 |
|------|------|----------|
| {{CURRENT_DATE}} | {{CHANGE}} | {{IMPACT}} |
