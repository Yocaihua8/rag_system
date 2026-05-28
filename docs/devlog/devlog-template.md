# DevLog {{YYYY-MM-DD}}

> Author：{{AUTHOR}}
> Iteration：{{ITERATION_OR_SPRINT}}（可选）
> Related：{{RELATED_DOCS_OR_ISSUES}}（可选）

## 1. Done（今日/本周完成）

- {{ITEM_1}}
- {{ITEM_2}}

## 2. Issues（遇到的问题）

记录阻塞、异常、临时规避。问题本身若需追踪，请同步进 `BACKLOG.md` 并在此仅留指针。

- **问题**：{{PROBLEM}}
  **影响**：{{IMPACT}}
  **当前处理**：{{WORKAROUND_OR_STATUS}}
  **跟踪**：{{BACKLOG_ID_OR_LINK}}（可选）

## 3. Decisions（临时决策）

记录本次开发中做出的小决策。**重大决策必须提升为 ADR**，此处仅放 ADR 编号。

- {{DECISION}} → 原因：{{REASON}}
- 关联 ADR：{{ADR_ID}}（可选）

## 4. Next（下一步）

- {{NEXT_ITEM_1}}
- {{NEXT_ITEM_2}}

## 5. Links（相关链接）

- Commit：{{COMMIT_HASH_OR_URL}}（可选）
- PR：{{PR_URL}}（可选）
- 关联文档：{{DOC_PATH}}（可选）

---

## 附录：填写示例

下方为一条简化的单日 devlog 填写样例。**复制模板时请删除本附录**。

```markdown
# DevLog 2026-05-23

> Author：RAG 团队
> Related：BACKLOG B-108、`docs/design/api-spec.md`

## 1. Done
- 完成多会话聊天第一片（B-108）：`chat_sessions` 表、session 切换、`/api/answer` 按 session_id 隔离
- 备份导出接口（B-102）：`GET /api/export/project` 只读返回项目快照和聊天记录，不含 API Key

## 2. Issues
- **问题**：大量 B-xxx 任务堆在同一天，测试覆盖时间不足
  **影响**：部分接口只做了冒烟测试
  **当前处理**：标记为 P1，下次迭代补齐
  **跟踪**：B-31

## 3. Decisions
- 备份恢复不覆盖原项目 → 原因：降低误覆盖风险，统一恢复为新的 `browser-upload:` 项目空间

## 4. Next
- B-109 模型 Profile 多配置设计

## 5. Links
- 关联文档：`docs/design/database-design.md`
```
