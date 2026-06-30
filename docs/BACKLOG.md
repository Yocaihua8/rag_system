# BACKLOG

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-06-30（B-149 CI 流水线完成并按规则从待办清单归档）
> Related：docs/requirements/functional-modules.md, docs/design/api-spec.md, docs/adr/ADR-001-fastapi-migration.md

用于记录尚未完成、待验证、待决策、已知问题和技术债。**这里允许写规划内容**，但应保持可执行和可追踪。

---

## 1. 使用规则

- 已经上线 / 已确定的内容不要留在 BACKLOG
- 每条记录必须有状态和优先级
- 大而空的愿景不写，尽量拆成可执行事项

### 1.1 待办清单 vs 已知问题

两类记录用途不同，不要写串：

| 类型 | 位置 | 关注 | 典型形态 |
|------|------|------|----------|
| 待办清单（§ 5） | `B-xxx` 表格行 | **要做的事**（可执行事项） | "流式输出接入 SSE" / "api.py 按领域拆分" |
| 已知问题（§ 6） | `ISSUE-xxx` 条目 | **已发现但尚未修复的现象** | "Markdown 符号以原始文本显示" |

**流转规则**：

- 一旦决定修复某个已知问题，**必须**在 § 5 新建对应 `B-xxx` 条目，并在原 `ISSUE-xxx` 的"计划处理方式"中引用该 ID
- 待办完成并验证后**可以**从 § 5 移除；已知问题在修复发布后**应该**从 § 6 移除并记入 `CHANGELOG.md`

---

## 2. 状态定义

- `todo`：待开始
- `doing`：进行中
- `blocked`：被阻塞
- `done`：已完成，待归档
- `wontfix`：暂不处理

---

## 3. 优先级定义

- `P0`：必须尽快处理，影响主流程
- `P1`：重要，影响使用体验或质量
- `P2`：常规优化
- `P3`：长期想法或低优先级改进

---

## 4. 规模估算定义

- `XS`：< 半天
- `S`：< 1 天
- `M`：< 3 天
- `L`：< 1 周
- `XL`：> 1 周

---

## 5. 待办清单

| ID | 类型 | 标题 | 状态 | 优先级 | 规模 | 里程碑 | 负责人 | 关联文档 | 说明 |
|----|------|------|------|--------|------|--------|--------|----------|------|
| B-150 | test | backend/ 单元测试补齐 | todo | P1 | M | v1.0.0 | RAG 团队 | docs/guides/testing.md | Phase 2 硬化主线：当前 `tests/test_backend/` 仅 3 个测试，与 webapp 28 个失衡；补齐 `backend/providers/llm`、`backend/providers/embedder`、`backend/config/paths`、`backend/config/settings` 与 Qdrant provider 降级路径覆盖 |
| B-151 | test | 前端 Vitest 单元测试 | todo | P2 | M | v1.0.0 | RAG 团队 | docs/guides/testing.md, docs/features/frontend-engineering.md | Phase 2 硬化主线：引入 Vitest，覆盖 `frontend/src/api/*` helper 的请求/错误归一化与关键组件状态；与 Playwright E2E 分层，单测跑纯逻辑、E2E 跑主流程 |
| B-152 | test | macOS/Linux Tauri 打包原生验证 | todo | P2 | M | v1.0.0 | RAG 团队 | docs/features/desktop-packaging.md | Phase 2 硬化主线：在 macOS/Linux 原生系统实测 B-24 的 `tauri:build:macos`（dmg）/`tauri:build:linux`（appimage）链路，补齐 Unix sidecar 与图标，记录平台差异与已知限制 |
| B-153 | docs | v1.0.0 发布门禁与回归清单 | todo | P1 | M | v1.0.0 | RAG 团队 | docs/release/, docs/guides/release-process.md | Phase 2 硬化主线：制定 v1.0.0 发布 readiness 清单与回归脚本，覆盖导入/检索/问答/导出/打包主流程，明确 go/no-go 门禁；沿用既有 `docs/release/*READINESS*` 模板 |
| B-154 | tech-debt | 依赖与安全审计基线 | todo | P2 | S | v1.0.0 | RAG 团队 | SECURITY.md, docs/guides/setup.md | Phase 2 硬化主线：引入 `pip-audit` / `npm audit` 基线与可选依赖矩阵验证（pymupdf / qdrant-client / sentence-transformers / ollama 缺失时降级路径），纳入 B-149 CI |
| B-23 | feature | Reranker 重排序（legacy） | wontfix | P3 | — | — | RAG 团队 | — | 已被 B-125 替代；原计划在 legacy 链路接入，Web MVP 由 B-125 统一覆盖 |
| B-67 | feature | Web 向量库与 Reranker 接入（legacy 规划） | wontfix | P3 | — | — | RAG 团队 | — | 已被 B-134（Qdrant）和 B-125（Reranker）拆分替代 |

---

## 6. 已知问题

_当前无未决已知问题。_

> ISSUE-003（文档一致性脚本要求缺失的 `docs/DEVLOG.md`）已于 2026-06-29 处理：确认仓库不维护 `docs/DEVLOG.md` 聚合索引，`scripts/check_docs_consistency.py` 改为在该文件缺失时跳过聚合索引校验（存在时仍校验）。
