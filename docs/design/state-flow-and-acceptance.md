# 状态流转与验收标准

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：导入、问答、Coach、Obsidian 发布和 Tauri sidecar 的当前状态机
> Related：`api-spec.md`、`database-design.md`、`frontend-backend-contract-check.md`、`../features/README.md`

## 1. 导入

### 1.1 通用提交

```text
用户选择来源
  -> 参数/路径/格式校验
  -> 读取并规范化为 documents.content
  -> 按 relative_path 创建、更新或保持文档
  -> 重建 document_chunks / chunk_vectors
  -> 可选同步 Qdrant
  -> 记录 import_batches 与 import_batch_items
  -> success / partial / failed
```

- `success`：导入流程完成且没有需要报告的失败项。
- `partial`：至少有可用结果，同时存在跳过或错误项。
- `failed`：批次无法形成可用结果；部分在项目或有效负载尚未建立前失败的请求不会创建批次。
- 批次摘要字段为 `imported/created/updated/unchanged/deleted/skipped/errors`；预览接口不创建批次。

当前文档表只保存原始统一正文 `content`，不生成 `normalized_markdown/plain_text/rendered_html` 三份字段。分块参数来自启动时的 `RAG_CHUNK_SIZE/RAG_CHUNK_OVERLAP`，仅作用于后续写入或缺失 chunk 回填；可选 Qdrant 写入失败只产生警告，不回滚 SQLite 已完成入库。

### 1.2 受控网页抓取

```text
preview（联网、校验目标/重定向/robots/大小/类型、抽取正文）
  -> 返回 preview 和内容校验信息，不写库
  -> 用户 commit（只接收并校验 preview，不重新联网）
  -> 写入 web: 虚拟来源并记录 web_fetch 批次
```

验收时必须区分 `/api/import/url` 的手工 URL 摘录与 `/api/import/web-fetch/*` 的真实抓取。

## 2. 问答与聊天

```text
问题校验
  -> BM25 + 向量候选（可选 graph legacy 一跳扩展）
  -> 可选 Cross-Encoder 重排
  -> 组装来源约束 prompt
  -> 模型流或本地来源片段回退
  -> token* -> done
                    \-> answer_error（流内失败）
  -> 成功后保存 chat_messages
```

- `GET /api/answer/stream` 的事件只有 `token`、`done`、`answer_error`；`done` payload 与同步 `/api/answer` 成功响应一致。
- 无可用模型、模型不可达或上游流失败时可以退回来源片段回答；无命中时不得生成伪造来源。
- 客户端取消只关闭当前 EventSource；不应把未收到 `done` 的流显示成已完成回答。
- 编辑历史消息会以 `parent_message_id` 和递增 `branch_index` 创建分支记录，不原地覆盖父消息。

## 3. Coach 分析与覆盖

```text
pending -> running -> completed
                   \-> failed
completed --来源指纹变化--> stale
stale --重新分析--> 新 analysis run
```

- 知识点稳定身份跨分析运行保留，但来源与映射绑定具体 run。
- `stale` 结果可只读追溯，不得作为当前结果发起新的定向评估、逐点学习或学习计划生成。
- 学习地图必须把 `unassessed` 与低分 `needs_work` 分开展示。

## 4. Coach 评估

```text
active -> completed
      \-> abandoned
```

- 同项目、同分析运行、同目标最多一个 active 会话。
- 作答前不返回 `expected_points_json`；一题只保存一份原始回答，重复相同请求可幂等处理。
- 结果 evaluator 为 `rule` 或 `model`；模型不可用时允许带 warning 回退规则评估。
- 结果状态：`unassessed`、`needs_work`（`<0.50`）、`developing`（`0.50 <= score < 0.75`）、`mastered`（`>=0.75`）。

## 5. Coach 逐知识点学习

```text
ready --begin_learning--> learning --begin_question--> awaiting_answer
awaiting_answer --submit--> evaluated
evaluated --retry--> retrying --submit--> evaluated
evaluated --next--> learning | completed
任意可写非终态 --abandon--> abandoned
```

- 同项目、同分析运行至多一个 `ready / learning / awaiting_answer / evaluated / retrying` 会话；同目标重复启动恢复原会话，不同目标不能覆盖活动会话。
- 知识点目标生成一个步骤，技能目标最多三个步骤。服务端一次只公开当前步骤和当前 exercise；未来步骤、巩固题、参考答案及评分依据不得提前返回。
- 每一步阈值为 `0.75`、最多三次 attempt。首答和第一次重试使用主问题；第二次仍未达标后公开巩固题；三次未达标仍可 `next`，步骤结果为 `needs_work`。
- 每次作答以 `(session_id,idempotency_key)` 幂等，并使用请求 hash 防止同 key 不同 payload；会话 `version` CAS 冲突返回最新会话快照，不允许旧客户端静默覆盖。
- `reveal` 后同一 exercise 的新 attempt 仍可练习，但 `counts_for_mastery=false`。只有未揭示答案且达标的有效 attempt 参与当前掌握证据。
- 来源指纹变化后历史会话只读；终态 `completed / abandoned` 也只读，但不能把正常终态误报为 stale。
- 从确认计划任务启动时，首个完成评分的 attempt 可单调推进该任务到 `in_progress`，全部步骤有效达标后推进到 `done`；打开、放弃或来源过期不会把任务标为完成。

SQL 练习状态仍使用上述会话机。提交只允许一条 `SELECT` 或非递归 `WITH ... SELECT`；每次 attempt 在结构化 fixture 创建的独立临时 SQLite 数据库中评分，正式应用数据库不参与执行。安全、语法、结果或必要语义不匹配均返回确定反馈，不能伪装为已掌握。

## 6. 学习计划

```text
generate -> draft -> confirmed -> archived
              |          |
              |          -> 只更新任务进度
              -> 可编辑结构/排序并确认
```

- 每项目最多一个 confirmed 版本；确认新版本时旧确认版转为 archived。
- 再次生成创建新的 revision，不覆盖已确认计划。
- 结构更新、进度更新和确认使用 revision/items hash/progress hash 防止并发静默覆盖。
- `learning` 任务必须引用同项目、同运行的真实来源；无来源只能生成 `source_gap`。

## 7. Obsidian 连接与同步

连接：

```text
创建限时 pairing（明文码只返回一次）
  -> 插件 complete，配对码 consumed
  -> active connection
  -> revoke -> revoked
```

同步事件：

```text
received -> applied
         -> ignored
         -> failed
```

- `upsert/rename/delete` 事件以 `(connection_id, event_id)` 幂等。
- 重命名保留来源身份；删除清理索引并使依赖分析过期。
- 输出根中的受管文件不反向摄入，避免同步反馈循环。

## 8. Obsidian 发布

```text
preview -> draft
  -> 用户 confirm -> confirmed -> queued
  -> 插件领取并逐 artifact 校验
  -> applied | conflict | failed
```

- 浏览器确认后的 `queued` 不能显示成发布成功。
- 插件只有在目标位于 `output_root`、文件包含受管标记且 `expected_vault_hash` 匹配时才可更新。
- 每个 artifact 只有一个终态结果；发布聚合在全部回传后汇总终态。
- 冲突只回报，不自动合并或覆盖；回滚通过旧内容的新发布执行，不修改历史修订。

## 9. Tauri sidecar

```text
Tauri setup
  -> 默认路径：固定 8765，显式关闭 desktop mode
  -> opt-in 安全路径：选择 loopback 临时端口 + 生成 32 字节随机令牌
  -> 通过子进程环境 spawn knowledge-island-backend
  -> 保存 child handle 与内存 bootstrap，转发 stdout/stderr
  -> 仅 main WebView 可读取 bootstrap
  -> sidecar 异常退出：清空 child 与 bootstrap
  -> 主窗口关闭：隐藏到托盘，sidecar 继续运行
  -> 托盘退出：kill child + 清空 bootstrap -> app exit
```

当前实现没有在显示 WebView 前轮询 `/api/health`、没有端口占用恢复、也不会在 sidecar 异常退出后自动重启。安全路径默认关闭，正式 Vue/CSP 仍使用固定 8765；打包成功或 sidecar 成功 spawn 不能替代安装后 API 主流程验证。

## 10. 最低验收矩阵

| 流程 | 最低通过标准 |
|------|--------------|
| 导入 | 真实写入文档/chunk/vector；批次成功、部分失败和跳过可区分 |
| 问答 | SSE 顺序可解析；`done` 有真实来源或明确无来源；取消不伪装完成 |
| Coach | stale 传播正确；评估与有效学习 attempt 的证据投影、状态阈值一致 |
| 逐点学习 | 七态迁移、三次 attempt、幂等/CAS、答案揭示资格、来源只读、计划单调联动正确；SQL 评分不访问正式数据库 |
| 学习计划 | 草稿可改、确认版结构不可改、并发冲突不被吞掉 |
| Obsidian | 配对/事件幂等；queued 与 applied 区分；路径/hash 冲突不覆盖 |
| Tauri | 安装后 WebView 能连接实际 sidecar API，退出时 sidecar 被终止 |
