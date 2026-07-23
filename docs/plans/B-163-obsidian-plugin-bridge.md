# B-163 Obsidian 插件桥与受控双向同步

> ⚠️ 创建此文件前，必须已完成以下操作（AI 自检）：
> - [x] `docs/BACKLOG.md` 中 B-163 状态为 `doing`
> - [x] B-163 说明列已填入本文件路径
> - [x] 关联功能文档和设计文档已按实际范围填写

> 状态：Active
> 创建时间：2026-07-23
> 创建方：Codex
> 关联 BACKLOG：B-163
> 关联功能文档：docs/features/notion-obsidian-sync.md, docs/features/project-knowledge-coach.md
> 关联设计文档：docs/design/architecture-overview.md, docs/design/database-design.md, docs/design/api-spec.md, docs/adr/ADR-009-obsidian-plugin-bridge.md

## 1. 目标

实现仅面向 Obsidian 桌面端的本地插件桥：一次性限时配对、哈希令牌、Markdown 增量事件幂等同步、保留文档身份的重命名、受控发布预览/确认/插件执行、冲突阻断和不可变发布修订。后端不直接访问 Vault，旧 `/api/import/obsidian-vault` 继续作为一次性只读导入。

## 2. 前置条件

- B-162 已完成，Coach 分析、覆盖、计划和评估数据可用于渲染发布产物
- ADR-009 已冻结桌面插件、令牌边界、输出目录、托管标记和三阶段写回协议
- Obsidian 官方 API 已核对：Vault 事件在 `workspace.onLayoutReady()` 后注册；后台更新使用 `Vault.process()`；Frontmatter 使用 `FileManager.processFrontMatter()`；链接元数据来自 `MetadataCache`

## 3. 任务拆解

- [x] 新增 Obsidian 配对、连接、同步事件、发布和不可变修订模型与存储
- [x] 实现连接令牌鉴权、配对和 Markdown 增量事件同步，支持幂等、重命名保留身份、删除和输出根排除
- [ ] 实现四类 Coach Markdown 渲染、发布预览/确认/待执行/结果状态机、冲突与回滚修订
- [ ] 建立独立 Obsidian TypeScript 插件工程，实现 Vault 事件队列、元数据采集和受控文件执行
- [ ] 接入十个 Obsidian API、同步 OpenAPI/数据库/功能/测试文档，完成回归并关闭任务

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `backend/domain/obsidian_*.py`, `backend/storage/obsidian_store.py` | 新增配对、同步和发布领域与持久化 |
| 代码 | `backend/routes/obsidian.py`, `backend/api/dispatch.py`, `backend/api/server.py`, `backend/api/openapi_schema.py` | 新增 Obsidian API 与专用令牌请求上下文 |
| 代码 | `backend/storage/knowledge_store.py`, `backend/domain/source_import.py` | 新增保留身份的文档重命名和虚拟来源边界 |
| 插件 | `integrations/obsidian-plugin/` | 新增独立桌面插件、测试和构建 |
| 测试 | `tests/test_backend/`, `tests/test_webapp/`, `integrations/obsidian-plugin/src/*.test.ts` | 存储、同步、发布、路由与插件行为 |
| 文档 | `docs/features/notion-obsidian-sync.md`, `docs/design/api-spec.md`, `docs/design/database-design.md`, `docs/design/architecture-overview.md`, `docs/guides/testing.md` | 回流 B-163 当前事实 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | B-162 已完成并删除其 plan |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | N/A | N/A |

> 已扫描 `docs/plans/` 与 `docs/superpowers/plans/`，未发现其他标记为 `Active` 或 `Interrupted` 的任务 plan；`docs/plans/README.md` 的 Active 是文档状态，不是执行 plan。

## 6. 完成标准

- [ ] 功能行为符合 `docs/features/notion-obsidian-sync.md` 与 ADR-009 的业务和安全规则
- [ ] 配对码、令牌、事件和发布严格按连接及项目隔离，明文令牌不持久化
- [ ] 发布路径、托管标记、稳定 ID、项目 ID 和 hash 任一不满足时不得覆盖
- [ ] 后端、插件、OpenAPI 和文档一致性测试通过
- [ ] 相关文档已同步（见下方回流清单）
- [ ] BACKLOG B-163 状态已更新为 `done`

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 配对、连接令牌和同步事件协议 | `docs/features/notion-obsidian-sync.md`, `docs/design/api-spec.md` | [ ] |
| Obsidian 数据实体和状态机 | `docs/design/database-design.md`, `docs/design/architecture-overview.md` | [ ] |
| 插件 API 使用、构建和安全边界 | `docs/features/notion-obsidian-sync.md`, `docs/guides/testing.md` | [ ] |
| 发布预览、确认、冲突和回滚 | `docs/features/project-knowledge-coach.md`, `docs/design/api-spec.md` | [ ] |

## 8. 执行记录

- 2026-07-23：Context7 月度额度耗尽，已明确告知；改用 Obsidian 官方开发文档和官方 `obsidian-api` TypeScript 定义核对 API。
- 2026-07-23：官方当前类型包为 `obsidian 1.13.2`；Vault `create/modify/delete/rename(file, oldPath)`、`MetadataCache.resolvedLinks/unresolvedLinks`、`Vault.process()` 与 `FileManager.processFrontMatter()` 契约已确认。
- 2026-07-23：发布正文由后端生成规范 Markdown，插件以 `Vault.process()` 做原子 hash/标记校验和全文替换；Frontmatter API用于读取与复核托管标记，避免双重序列化导致 hash 漂移。
- 2026-07-23：六张 Obsidian 表、聚合发布与逐产物不可变修订已落地；文档重命名保留 document/chunk ID 并更新外部向量路径，目标冲突不会提前标记分析 stale。
- 2026-07-23：一次性五分钟配对码和随机连接 token 只保存 SHA-256；插件事件按连接 `event_id` 持久幂等，支持 upsert/rename/delete、离线重放、元数据载荷和输出根精确排除。
- 2026-07-23：B-163 存储、路径、配对、同步、文档身份与请求上下文共 25 项聚焦测试通过。

## 9. 状态快照

- **最后更新**：2026-07-23
- **进度**：已完成 2 / 5 项
- **最新 commit**：`e547233` — feat: 实现 Obsidian 配对与幂等事件同步
- **代码状态**：`feature/project-knowledge-coach-v2`；Obsidian 存储、配对、专用令牌、路径约束和幂等增量同步已提交
- **下一步**：实现 Coach Markdown 渲染与受控发布状态机
- **续任务须知**：连接令牌只允许插件路由；后端不直接读写 Vault；旧一次性导入保持不变
