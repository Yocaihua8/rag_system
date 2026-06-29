# B-07 结果导出（Markdown / PDF）

> 状态：Active
> 创建时间：2026-06-29
> 创建方：Codex
> 关联 BACKLOG：B-07
> 关联功能文档：docs/features/result-export.md
> 关联设计文档：docs/design/api-spec.md

## 1. 目标

为 Web MVP 补齐生成结果导出能力，使已生成的问答消息可以通过本地 API 导出为 Markdown 或 PDF 文件，并写入预留目录 `data/outputs/`。

## 2. 前置条件

- 已读取 `AGENTS.md`、`docs/BACKLOG.md`、`docs/design/api-spec.md`、`docs/features/README.md`。
- 已确认 `docs/features/feature-template.md` 不存在，本次沿用现有功能文档结构新建 `docs/features/result-export.md`。
- 当前工作区存在非本任务未提交改动，执行时只处理 B-07 相关文件和 hunk。

## 3. 任务拆解

- [ ] 补充结果导出 API 的红灯测试，覆盖 Markdown、PDF、非法格式与跨项目消息保护。
- [ ] 实现 `POST /api/export/result`，写入 `data/outputs/` 并返回导出文件元数据。
- [ ] 同步 OpenAPI、API 规格和功能文档，完成验证后关闭 BACKLOG 并删除本 plan。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `webapp/routes/export.py` | 修改 |
| 代码 | `webapp/result_export.py` | 新增 |
| 代码 | `webapp/openapi_schema.py` | 修改 |
| 测试 | `tests/test_webapp/test_api.py` | 修改 |
| 测试 | `tests/test_webapp/test_api_route_split.py` | 修改 |
| 文档 | `docs/features/result-export.md` | 新增 / 修改 |
| 文档 | `docs/features/README.md` | 修改 |
| 文档 | `docs/design/api-spec.md` | 修改 |
| 文档 | `docs/BACKLOG.md` | 修改 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | 无直接依赖 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | N/A | N/A |

创建本 plan 时扫描到 3 个 `docs/superpowers/plans/` 旧 plan，影响范围集中在 legacy 桌面端、领域模型与历史文档，不涉及 `webapp/routes/export.py`、`data/outputs/` 或本次 API 契约。

## 6. 完成标准

- [ ] 功能行为符合 `docs/features/result-export.md` 的业务规则
- [ ] 测试通过（参照 `docs/guides/testing.md` 最低要求）
- [ ] 相关文档已同步（见下方"回流清单"）
- [ ] BACKLOG 条目 `B-07` 状态已更新为 `done`

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 结果导出接口契约 | `docs/design/api-spec.md` | [ ] |
| 结果导出用户可见行为与边界 | `docs/features/result-export.md` | [ ] |
| 功能文档索引 | `docs/features/README.md` | [ ] |
| B-07 完成状态 | `docs/BACKLOG.md` | [ ] |

## 8. 执行记录

- 2026-06-29：`docs/features/README.md` 提到的 `feature-template.md` 未找到，改为参考现有功能文档结构创建 `result-export.md`。
- 2026-06-29：本次不修改 SQLite schema，不引入大型 PDF 依赖，导出文件写入本地 `data/outputs/`。

## 9. 状态快照

- **最后更新**：2026-06-29 00:00
- **进度**：已完成 0 / 3 项（见 § 3 勾选状态）
- **最新 commit**：`N/A` — 尚未提交
- **代码状态**：`fix/b-08-concurrent-index`；工作区存在非 B-07 既有改动，需精确暂存
- **下一步**：补充结果导出 API 的红灯测试，覆盖 Markdown、PDF、非法格式与跨项目消息保护
- **续任务须知**：只暂存 B-07 相关文件和 `docs/BACKLOG.md` 的 B-07 hunk
