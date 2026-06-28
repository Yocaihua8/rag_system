# GitHub 仓库整体导入

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-06-28
> Related：B-133, docs/design/api-spec.md, docs/requirements/functional-modules.md

## 1. 目标

B-133 为开发者用户提供 GitHub 仓库整体导入入口。用户提交 GitHub 仓库 clone URL 后，系统在本地受控运行时目录执行浅克隆，并把仓库内可解析文件导入为一个新的知识库项目，用于后续搜索、问答和知识整理。

## 2. 功能边界

- 支持 `https://github.com/<owner>/<repo>`、`https://github.com/<owner>/<repo>.git` 和 `git@github.com:<owner>/<repo>.git` 形式的 GitHub 仓库地址。
- 支持可选分支名；未填写时使用仓库默认分支。
- 支持可选项目名称；未填写时使用仓库名。
- 导入过程复用现有目录导入解析能力，遵守 `webapp/import_rules.py` 中的可导入后缀与忽略目录规则。
- 仓库克隆目录位于 Web MVP 的本地运行时目录 `runtime/webapp/github-repos/` 下，不修改 SQLite schema。
- 导入完成后返回新建项目、导入摘要、导入批次和文档列表。

## 3. 暂不支持

- 不接入 GitHub API。
- 不保存 GitHub Token、SSH Key、用户名或密码。
- 不处理私有仓库鉴权流程；如本机 `git` 已具备访问权限，可由底层 clone 命令自行处理。
- 不做仓库增量同步、定时拉取或 webhook。
- 不支持任意站点或任意 git host，只覆盖 GitHub 仓库 URL。

## 4. 接口

新增 Web MVP API：

```http
POST /api/import/github-repo
Content-Type: application/json
```

请求体：

```json
{
  "repo_url": "https://github.com/example/project.git",
  "branch": "main",
  "project_name": "Example Project"
}
```

响应体：

```json
{
  "project": {},
  "result": {},
  "batch": {},
  "documents": []
}
```

错误处理：

- `repo_url` 为空时返回 `400`。
- 仓库地址不是 GitHub clone URL 时返回 `400`。
- 本机缺少 `git` 或 clone 失败时返回 `400`，错误信息不包含凭据。

## 5. 页面入口

Vue 资料库导入面板新增 GitHub 仓库导入表单，包含仓库地址、分支名和项目名输入。导入成功后切换到新建项目并刷新项目、文档与导入批次列表。

## 6. 架构落点

- API 路由仍位于 `webapp/routes/imports.py`，保持 Web MVP 过渡期路由结构。
- GitHub clone 与仓库路径管理封装在独立导入模块中，避免把 subprocess 细节写入路由。
- 文档解析、chunk、embedding、存储继续复用现有目录导入链路。
- 本任务不新增后端 provider，不修改 `src/` legacy 代码。
