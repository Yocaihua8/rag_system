# GitHub 仓库导入

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：GitHub.com 仓库浅克隆与本地资料导入
> Related：`project-space-ingestion.md`、`../design/api-spec.md`、`../guides/setup.md`、`../guides/troubleshooting.md`

## 1. 用户目标

用户在资料弹窗输入 GitHub 仓库地址，可选分支和项目名，系统浅克隆仓库并把可解析文件导入为新的项目空间。

## 2. 当前可达

- 支持 `https://github.com/<owner>/<repo>`、带 `.git` 的 HTTPS 地址和 `git@github.com:<owner>/<repo>.git`。
- 未填分支时使用仓库默认分支；未填项目名时使用仓库名。
- 克隆目录默认位于 `runtime/v2/github-repos/`，随 `RAG_RUNTIME_DIR` 改变。
- 导入复用通用后缀、忽略目录、解析、分块、向量和批次规则；成功后切换到新项目。

## 3. 安全与边界

- 系统不接入 GitHub API，不保存 Token、SSH Key、用户名或密码。
- 私有仓库没有应用内鉴权流程；只有本机 Git 已经具备访问能力时，底层 clone 才可能成功。
- 只接受 GitHub 仓库地址，不接受任意 Git host。
- 当前没有增量 pull、定时同步、Webhook、submodule 管理或凭证向导。
- clone 失败或本机缺少 Git 时返回脱敏错误，不得输出 URL 中潜在凭证。
