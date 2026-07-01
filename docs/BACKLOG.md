# BACKLOG

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-07-01（B-155 webapp 全量重组完成）
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
| B-150 | test | backend/ 单元测试补齐 | done | P1 | M | v1.0.0 | RAG 团队 | docs/guides/testing.md | Phase 2 硬化主线：已补齐 `backend/providers/llm`、`backend/providers/embedder`、`backend/config/paths`、`backend/config/settings` 与 Qdrant provider 降级路径单元测试，并在 `docs/guides/testing.md` 记录 backend/provider 验证命令 |
| B-151 | test | 前端 Vitest 单元测试 | done | P2 | M | v1.0.0 | RAG 团队 | docs/guides/testing.md, docs/features/frontend-engineering.md | Phase 2 硬化主线：已引入 Vitest + jsdom，覆盖 `frontend/src/api/*` helper 的请求/错误归一化、SSE/上传 payload 与 `AnswerPanel`、`ProjectSpacePanel`、`QuestionComposer` 关键状态；CI 已在 Playwright E2E 前执行 `npm run test:unit` |
| B-152 | test | macOS/Linux Tauri 打包原生验证 | done | P2 | M | v1.0.0 | RAG 团队 | docs/features/desktop-packaging.md | Phase 2 硬化主线：已补齐 Tauri 桌面 bundle 图标、修正 macOS/Linux `tauri build --bundles ...` 命令、修复 Unix sidecar target 检测 pipefail 退出码，并通过 GitHub Actions `macos-latest` / `ubuntu-latest` 原生 runner 生成 `.dmg` 与 `.AppImage` artifact |
| B-153 | docs | v1.0.0 发布门禁与回归清单 | done | P1 | M | v1.0.0 | RAG 团队 | docs/release/V1_0_0_READINESS_2026-07-01.md, docs/guides/release-process.md | Phase 2 硬化主线：已新增 v1.0.0 readiness 清单与回归脚本，覆盖导入/检索/问答/导出/打包主流程，明确 go/no-go 门禁，并在发布流程中设为 v1.0.0 发布前检查入口 |
| B-154 | tech-debt | 依赖与安全审计基线 | done | P2 | S | v1.0.0 | RAG 团队 | SECURITY.md, docs/guides/setup.md | Phase 2 硬化主线：引入 `pip-audit` / `npm audit` 基线与可选依赖矩阵验证（pymupdf / qdrant-client / sentence-transformers / ollama 缺失时降级路径），纳入 B-149 CI 与 v1.0.0 readiness |
| B-155 | tech-debt | webapp/ 全量重组至 backend/ | done | P2 | XL | v1.1.0 | RAG 团队 | docs/design/architecture-overview.md | v1.0.0 后执行：已废弃受控 `webapp/` 源码目录，按职责重组至 `backend/api/`、`backend/storage/`、`backend/domain/`、`backend/routes/` 等子包；已迁移 Python import 路径、测试和文档引用；不改 API 契约、不改 SQLite schema，不改 `frontend/src` 或前端交互，仅调整 Vite 构建输出到 `backend/static_dist/` |

---

## 6. 已知问题

_当前无未决已知问题。_

> ISSUE-003（文档一致性脚本要求缺失的 `docs/DEVLOG.md`）已于 2026-06-29 处理：确认仓库不维护 `docs/DEVLOG.md` 聚合索引，`scripts/check_docs_consistency.py` 改为在该文件缺失时跳过聚合索引校验（存在时仍校验）。
