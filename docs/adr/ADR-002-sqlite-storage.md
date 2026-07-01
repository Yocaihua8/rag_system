# ADR-002 SQLite 作为关系数据源与兼容副本

> 状态：Accepted
> Date：2026-05-21
> Owner：RAG 团队
> Related：`../design/database-design.md`、`../design/architecture-overview.md`、`ADR-007-qdrant-vector-store.md`

## 1. 背景

Web MVP（v0.7.0，2026-05-21）需要一个持久化层来存储以下数据：

- 业务数据：项目空间、文档、分块、聊天会话与消息、导入批次、文档集合、评估题目与结果、Agent 工具审计、检索复盘
- 向量索引：chunk embedding 向量（`chunk_vectors` 表）
- 配置数据：LLM 设置、模型 Profile、Prompt 预设

核心设计约束：
1. **本地优先**：无需用户安装和管理任何额外服务，`python app.py` 即可启动
2. **单用户**：当前无多租户 / 多用户需求（B-118 研究结论：不进入当前实现）
3. **零部署依赖**：Docker 容器和本地直接运行应当无差异，不引入 PostgreSQL / MySQL 等需要持久化服务进程的依赖

## 2. 决策结论

使用 **Python 标准库 `sqlite3`**，以单文件 SQLite 数据库（默认路径 `runtime/app.db`）承担**全部持久化**职责，包括关系数据与向量索引副本。

具体配置：
- `PRAGMA foreign_keys = ON`：启用外键约束
- `PRAGMA busy_timeout = 30000`：写入竞争时最多等待 30 秒，支持跨项目并发导入（B-08）
- WAL 日志模式：通过 B-08 的 busy timeout 替代显式 WAL，避免 Docker volume 兼容性问题

向量索引以 `chunk_vectors` 表作为**兼容副本**保留，Qdrant local mode（B-134）作为可选升级路径；Qdrant 不可用时自动回退 SQLite 全扫描。

Schema 迁移通过兼容 `ALTER TABLE ... ADD COLUMN` 实现原地升级，无需迁移工具。

## 3. 决策原因

1. **零运行时依赖**：`sqlite3` 是 Python 标准库，无需 `pip install`；单文件数据库，备份 = 复制一个文件
2. **单用户场景足够**：SQLite 的并发写入限制（单写者）对本地单用户不构成瓶颈；B-08 的进程内项目锁已实现跨项目并发、同项目串行
3. **最小变更量**：`backend/storage/knowledge_store.py`（`KnowledgeStore` 类）封装全部 CRUD，业务层不感知存储实现细节
4. **向量副本保证可用性**：`chunk_vectors` 表与 Qdrant 保持双写同步；Qdrant 不可用时（未安装 `qdrant-client` 或服务异常）透明降级，不阻断任何功能
5. **迁移路径清晰**：未来若需多用户，`KnowledgeStore` 接口不变，只替换底层驱动即可（见 §5 备选方案对比）

## 4. 备选方案

### 4.1 方案 A：PostgreSQL

- 优点：并发写、JSONB、完整外键、可扩展到多用户
- 缺点：需要独立服务进程（`pg_ctl` / Docker pg 容器）；用户需配置连接串；备份需 `pg_dump`；与"零部署依赖"约束直接冲突
- 未采用原因：本地单用户场景下部署成本远超收益；多用户时再评估（B-118 结论）

### 4.2 方案 B：纯 Qdrant（向量 + 元数据）

- 优点：向量检索性能最优；部分 Qdrant 版本支持 payload 过滤存储元数据
- 缺点：Qdrant payload 不是关系型存储，JOIN / 外键 / 聚合查询笨拙；关系数据（聊天记录、评估、审计）仍需另一存储层；Qdrant 未安装时整个系统不可用
- 未采用原因：作为唯一存储层依赖过强；混合存储反而增加复杂度；SQLite + Qdrant 双层方案兼顾可用性与性能

### 4.3 方案 C：TinyDB / JSON 文件

- 优点：更轻量，纯 Python
- 缺点：无事务、无索引、并发不安全；搜索性能随数据量线性下降
- 未采用原因：SQLite 同样是零依赖，但提供事务、索引和 SQL 查询，各方面都优于 JSON 文件

## 5. 影响

### 5.1 正面影响

- 本地启动零配置：`python app.py` 自动在 `runtime/` 下初始化数据库
- 备份简单：一次 `cp runtime/app.db backup/` 即完整备份
- 测试隔离：测试通过 `KI_DB_PATH` 环境变量指向临时路径，与生产库完全隔离
- Qdrant 可选：`qdrant-client` 未安装时打印 `WARNING` 并继续工作，不阻断 CI

### 5.2 负面影响

- 向量全扫描性能：大型项目（万级 chunk）在未安装 Qdrant 时向量查询需全表扫描，`O(n)` 时间复杂度
- 写并发上限：单写者模型，跨项目高频并行写入时 `busy_timeout` 是最后防线，不适合多用户高并发
- Schema 迁移无版本管理：兼容 ADD COLUMN 覆盖大多数场景，但破坏性变更（列改名 / 删除）需手写迁移脚本

### 5.3 对现有系统的改动点

| 模块 | 内容 |
|------|------|
| `backend/storage/knowledge_store.py` | `KnowledgeStore.__init__` 初始化 SQLite 连接，执行 `CREATE TABLE IF NOT EXISTS` 与兼容迁移 |
| `runtime/app.db` | 默认数据库文件路径；Docker 通过 volume `ki-runtime` 持久化 |
| `backend/providers/vector_store/` | Qdrant provider 与 SQLite `chunk_vectors` 双写同步；搜索时优先 Qdrant，降级 SQLite |

## 6. 后续动作

### 6.1 已完成

- `backend/storage/knowledge_store.py`：`KnowledgeStore` 封装 15+ 张业务表 CRUD，含兼容迁移
- B-08：`busy_timeout = 30000` + 进程内项目锁，支持跨项目并发导入
- B-134（ADR-007）：Qdrant local mode 作为向量索引可选升级，`chunk_vectors` 作为兼容副本保留

### 6.2 未来评估触发条件

- 单项目 chunk 数超过 10 万：评估强制开启 Qdrant 或迁移 PostgreSQL pgvector
- 引入多用户 / 团队空间（B-118 准入门槛）：评估迁移 PostgreSQL

### 6.3 回滚策略

N/A —— SQLite 是 MVP 基础组件，无前序实现可回滚；向量层可通过关闭 Qdrant 配置回退至纯 SQLite 检索。
