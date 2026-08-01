# 贡献者指南模板

> 状态：Draft
> Owner：{{OWNER}}
> Last Updated：{{CURRENT_DATE}}
> Related：`branch-conventions.md`；若已启用根贡献规范或 team pack，再关联 `../../CONTRIBUTING.md`、`team-collaboration.md`

本文档用于给新贡献者提供一份可执行的参与指南。若项目已启用 `../../CONTRIBUTING.md`，本文件在其通用规范上补充参与细节；未启用时，本文件可独立作为贡献入口。

## 1. 适用范围

| 项 | 内容 |
|----|------|
| 项目名称 | {{PROJECT_NAME}} |
| 主要维护者 | {{MAINTAINER_TEAM_OR_OWNER}} |
| 适用对象 | {{CONTRIBUTOR_TYPE}} |
| 默认沟通渠道 | {{CHANNEL}} |
| 贡献前必读 | `../../README.md`、`setup.md`；若存在 `../../CONTRIBUTING.md`，同时阅读该文件 |

## 2. 贡献类型

| 类型 | 示例 | 入口 | 是否需要 Issue |
|------|------|------|----------------|
| Bug 修复 | {{BUG_FIX_EXAMPLE}} | Issue / PR | 是 |
| 新功能 | {{FEATURE_EXAMPLE}} | Issue / RFC / PR | 是 |
| 文档改进 | {{DOCS_EXAMPLE}} | Issue / PR | 视范围 |
| 测试补充 | {{TEST_EXAMPLE}} | PR | 视范围 |
| 重构 / 性能 | {{REFACTOR_EXAMPLE}} | RFC / PR | 通常需要 |
| 安全问题 | {{SECURITY_EXAMPLE}} | 安全入口 | 不走公开 Issue |

## 3. 环境准备

| 步骤 | 命令 / 文档 | 预期结果 |
|------|-------------|----------|
| 克隆仓库 | `git clone {{REPOSITORY_URL}}` | 本地仓库可访问 |
| 安装依赖 | `{{INSTALL_COMMAND}}` | 依赖安装完成 |
| 初始化配置 | `{{ENV_INIT_COMMAND}}` | 本地配置存在，且不包含真实密钥 |
| 启动服务 | `{{DEV_COMMAND}}` | 本地服务可访问 |
| 运行基础测试 | `{{TEST_COMMAND}}` | 测试通过或记录已知失败 |

## 4. Issue 流程

1. 搜索已有 Issue，避免重复提交。
2. 选择合适模板：Bug、Feature、Documentation 或其他项目自定义模板。
3. 填写可复现信息、影响范围、期望行为和已尝试方案。
4. 等待维护者确认标签、优先级、Owner 和是否需要 RFC。
5. 只有范围明确、验收条件可验证后，才进入开发。

## 5. PR 流程

| 阶段 | 要求 |
|------|------|
| 创建分支 | 按 `branch-conventions.md` 命名，避免直接推主分支 |
| 开发前 | 确认实际启用的 Issue / BACKLOG / plan 中的影响范围；未启用的入口不作硬性要求 |
| 提交前 | 运行测试、lint、构建或本项目指定验证命令 |
| 创建 PR | 若存在 `.github/pull_request_template.md`，使用该模板；否则在 PR 中直接填写影响范围和验证结果 |
| Review | 按项目治理规则确定人数；未配置团队 Review 门禁时由维护者明确验收方式 |
| 合并前 | 已配置 CI 或 CODEOWNERS 时完成对应检查；按实际启用范围同步文档与 CHANGELOG |

## 6. 测试

| 变更类型 | 最低测试要求 | 推荐命令 |
|----------|--------------|----------|
| 核心逻辑 | 单元测试 + 边界条件 | `{{UNIT_TEST_COMMAND}}` |
| 接口契约 | 接口测试 / 契约验证 | `{{API_TEST_COMMAND}}` |
| UI / 交互 | 主流程验证 / 截图检查 | `{{UI_TEST_COMMAND}}` |
| 文档模板 | 自检脚本 / 链接检查 | `{{DOCS_CHECK_COMMAND}}` |

无法运行测试时，PR 必须说明原因、失败日志、替代验证方式和需要 Reviewer 关注的风险。

## 7. 变更记录

- 若已启用 `../../CHANGELOG.md`，面向使用者可感知的新增、修改、修复、移除或安全变更写入该文件。
- 开发过程由 Git 提交与 PR 保存；不要新建独立日志目录。
- 若已启用 tracking pack 与 `../BACKLOG.md`，未完成规划、技术债和已知问题写入该文件；否则写入实际任务入口，不要混入已生效文档。

## 8. Review 期望

Reviewer 重点检查：

- 变更是否满足 Issue / BACKLOG / RFC 的目标和非目标。
- 是否保持模块边界、层边界和低耦合约束。
- 是否存在兼容性、安全、权限、数据迁移或性能风险。
- 测试是否覆盖主流程、边界条件和失败路径。
- 已启用的文档、CHANGELOG、BACKLOG、ADR 是否按影响范围同步；缺失的可选文件不作为阻塞项。

贡献者收到 Review 后应逐条响应：已修改、不同意并说明理由、或拆分到实际启用的后续任务入口。

## 9. 维护者职责

| 职责 | Owner | 说明 |
|------|-------|------|
| Issue triage | {{OWNER}} | 确认标签、优先级、复现信息 |
| RFC 评审 | {{OWNER}} | 判断是否进入实施 |
| PR Review | {{OWNER}} | 检查行为、测试、文档和风险 |
| Release note | {{OWNER}} | 确认 `CHANGELOG.md` 与发布说明 |
| 安全响应 | {{OWNER}} | 走安全渠道，不在公开 Issue 泄露细节 |

## 10. 附录：贡献前检查

- [ ] 若存在 `../../CONTRIBUTING.md`，已阅读并遵守；不存在时以本指南为准
- [ ] 已按 `setup.md` 跑通本地环境
- [ ] 已搜索重复 Issue / PR
- [ ] 已确认影响范围和文件/模块锁定
- [ ] 已知道本次变更需要运行哪些验证命令
