# 分支与提交规范

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-25
> Scope：Knowledge Island 本地开发分支与提交约定
> Related：docs/guides/release-process.md, CONTRIBUTING.md

## 1. 分支模型

采用**单主分支 + 短期功能分支**策略：

- `main` 为唯一长期稳定分支，始终保持可运行状态
- 功能开发在独立分支完成，完成后合并到 `main`
- 不使用 GitFlow 的 `develop` / `release` 分支（项目规模不需要）

## 2. 分支命名规范

| 类型 | 格式 | 示例 |
|------|------|------|
| 功能开发 | `feature/<description>` | `feature/streaming-output` |
| 问题修复 | `fix/<description>` | `fix/vector-score-nan` |
| 重构 | `refactor/<description>` | `refactor/api-split-blueprints` |
| 文档 | `docs/<description>` | `docs/rewrite-per-spec` |
| 维护 | `chore/<description>` | `chore/upgrade-pymupdf` |

命名规则：
- 使用小写 `kebab-case`
- 描述部分言简意赅（2-4 个词），无需加 B-XX 编号
- 避免使用 `update` / `modify` 等无意义动词

## 3. 提交信息规范

建议遵循 Conventional Commits，使用中文摘要：

```text
<type>(<scope>): <中文摘要>
```

| type | 说明 | 示例 |
|------|------|------|
| feat | 新功能 | `feat(answers): 接入流式输出 SSE` |
| fix | 修复 bug | `fix(search): 修复向量分数 NaN 导致排序异常` |
| refactor | 重构（无功能变化）| `refactor(api): 按领域拆分路由蓝图` |
| docs | 文档 | `docs(backlog): 新增竞品差距分析待办项` |
| test | 测试 | `test(embeddings): 新增 hash fallback 边界用例` |
| chore | 配置 / 依赖 | `chore: 升级 pymupdf 到 1.25` |
| perf | 性能优化 | `perf(search): 向量检索提前过滤低分 chunk` |

规则：
- 代码变更和文档变更应分开提交，便于回溯
- 影响文档行为的改动必须附带对应文档更新
- 单次提交聚焦一件事，避免"修改了 N 个功能"的大提交

## 4. 合并规则

- 个人项目允许直接推送 `main`，重大功能建议走 PR 留记录
- 合并前应确认：`python -m pytest tests/backend tests/frontend -q` 通过
- 合并方式：Squash（功能分支，保持 main 历史整洁）或 Merge（需要保留提交历史时）
- 推送前检查 `CHANGELOG.md` 是否已更新
