# 结构基线（2026-04，v2）

> **状态**：Active
> **取代**：旧版 STRUCTURE_BASELINE（2026-04 初版，记录三分法迁移状态）
> **主文档**：见 `SYSTEM_ARCHITECTURE.md`

---

## 1. 主路径（Active）

新架构采用 **`src/` 统一源码根**，按职责分五层：

```
src/
├── config/       配置层（最先加载，仅 stdlib）
├── domain/       纯业务逻辑层（零 I/O，零 Qt）
├── ports/        抽象接口层（只依赖 domain）
├── adapters/     具体实现层（SQLite / Ollama / ChromaDB）
├── application/  用例编排层（组合 ports，无 Qt）
└── desktop/      Qt 表现层（仅依赖 application）
```

**主调用方向（严格单向）：**

```
config ← domain ← ports ← adapters
                        ← application ← desktop
```

**唯一入口：**

```powershell
py -3 app.py
```

---

## 2. 非业务目录

| 路径 | 状态 | 说明 |
|------|------|------|
| `frontend/` | 遗留 Web 前端，未维护 | 保留归档，不参与新架构 |
| `archive/` | 冻结历史代码 | 只读参考 |
| `scripts/` | 运维辅助脚本 | 全部已更新，使用 `src/` 路径 |
| `data/` | 示例数据 | 仅供开发测试 |

> `backend/` 和 `desktop/` 旧目录已于 2026-04-16 清理删除。

---

## 3. 新增代码约束

1. 新增业务模型进入 `src/domain/models/`
2. 新增纯函数逻辑进入 `src/domain/services/`
3. 新增接口契约进入 `src/ports/`
4. 新增存储/模型适配进入 `src/adapters/`
5. 新增业务用例进入 `src/application/`
6. 新增 UI 组件进入 `src/desktop/views/` 或 `src/desktop/controllers/`
7. **禁止** 在 `src/domain/` 中 import 任何第三方 I/O 库
8. **禁止** 在 `src/application/` 中直接 import adapter 类（仅 `container.py` 例外）
9. **禁止** 在 Qt 主线程中执行 LLM 调用、Embedding、文件 I/O

---

## 4. 关键新增组件（v2 相比旧架构）

| 组件 | 路径 | 说明 |
|------|------|------|
| IEmbedder | `src/ports/embedder.py` | Embedding 接口 |
| IVectorStore | `src/ports/vector_store.py` | 向量存储接口 |
| OllamaEmbedder | `src/adapters/embedding/ollama_embedder.py` | nomic-embed-text |
| ChromaVectorStore | `src/adapters/vector_store/chroma_store.py` | 本地向量库 |
| VectorRetriever | `src/adapters/retrieval/vector_retriever.py` | 语义检索 |
| AppContainer | `src/application/container.py` | 依赖组装根 |
| BaseWorker | `src/desktop/workers/base_worker.py` | QThread 基础 |
