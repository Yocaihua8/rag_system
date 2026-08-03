# v3 Sources 合同

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-03
> Scope：v3 Sources 的发现、索引、读取和 HTTP 边界
> Related：`api-spec.md`、`database-design.md`、`agent-runtime-and-tool-contract.md`、`../features/project-sources.md`

## 1. 目标与边界

Sources 为 v3 Project 的受控本地资料入口。第一段只允许对已存在的 `projects.root_path` 进行只读扫描，并把受支持文本文件的受管副本写入 v3 `sources/documents`；不得将 v2 文档、向量、运行数据或导入 API 复用为 v3 Sources 的实现。

创建 Project 已是显式目录绑定。后续扫描不需要额外写入确认，因为它不改动项目文件或外部系统；扫描对 v3 数据库的写入必须有 `Idempotency-Key`，同 key 与相同请求回放相同结果。

## 2. 路径与内容安全

- 每次扫描从 Store 中重新读取 Project 根，要求根仍存在且为目录。
- 递归前解析根，所有候选文件必须是根内的常规文件；拒绝绝对输入路径、`..` 逃逸、符号链接和不可读文件。
- 忽略规则沿用 v3 项目检查的忽略目录；文件类型沿用现有文本导入白名单。大小、条目和总内容上限在实现前设为显式常量并有测试。
- 服务端可以在 v3 `documents.content` 保存受控文本副本以服务后续检索，但 Sources 列表和扫描响应不得返回正文、绝对根、`source_path`、`config_json` 或内部错误栈。
- 所有返回的文件定位使用正斜杠相对路径；来源标识使用稳定 UUID，不把本地路径当 ID。

## 3. 第一段 HTTP 合同

| 方法 | 路径 | 请求 | 成功 | 失败 |
|------|------|------|------|------|
| POST | `/api/v3/projects/{project_id}/sources/scan` | 无 body；`Idempotency-Key` 必填 | `201`，返回扫描后的 `source` 和摘要 | `404 project not found`、`409 project root unavailable`、`422` 请求/键非法 |
| GET | `/api/v3/projects/{project_id}/sources` | 可选 `status`、`limit`、`offset` | `200`，返回受管 Sources 列表 | `404 project not found`、`422` query 非法 |
| GET | `/api/v3/projects/{project_id}/documents` | 可选 `source_id`、`limit`、`offset` | `200`，返回文档元数据列表 | `404 project/source not found`、`422` query 非法 |

`SourceResource` 最少包含 `id / project_id / source_type / name / status / document_count / indexed_at`。`DocumentResource` 最少包含 `id / project_id / source_id / relative_path / mime_type / size_bytes / checksum / version / updated_at`。第一段不开放文档正文下载、任意路径读取、删除、外部连接器、向量化或全文检索。

## 4. 持久化与一致性

- 每个 Project 只有一个 `source_type=project_root`、`locator=.` 的资料源；重复扫描更新其 `updated_at` 与状态。
- 同一 Project 的 `documents.relative_path` 仍受唯一约束。扫描中的新增或变更文件更新内容、checksum、大小、mime、版本和时间；不再存在的受管文件必须从当前可见列表移除，并在同一事务中级联删除其 chunks/vectors。
- 扫描以一个数据库事务提交最终 Source、Document 和幂等回放记录。若根目录不可读或扫描开始前路径不安全，不写入部分结果。
- 单个文件读失败、超限或格式不支持写入响应摘要而非 Document 内容；成功文件照常提交。摘要是审计信息，不替代每个 Document 的持久状态。

## 5. 前端与后续能力

React 项目页只能读取这三个 v3 接口并显示真实空态、加载、失败和扫描摘要。只有 `source_type=project_root` 的真实结果可展示；不得用 v2 文档或原型数据回退。

Project Insights、Sources 预览、资料编辑、导出和连接器均不由本合同自动开放，必须各自增加 API、权限、测试和状态说明。
