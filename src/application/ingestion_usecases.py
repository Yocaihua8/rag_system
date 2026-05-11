"""
IngestWorkspaceUseCase — 知识库摄入全流程。

完整步骤：扫描文件 → 加载文本 → 打标分块 → 存储 → 嵌入 → 写入向量库 → 更新工作区状态

设计：使用生成器（yield IngestProgress）驱动进度，调用方（IngestWorker）负责
     将 progress 信号转发给 Qt UI。所有 I/O 在调用方的线程中执行。
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Optional, Set

from src.config.settings import AppSettings
from src.domain.errors import NotFoundError
from src.domain.models.chunk import Chunk
from src.domain.models.document import Document
from src.domain.models.task import Task, TaskKind, TaskStatus
from src.ports.chunk_store import IChunkStore
from src.ports.document_store import IDocumentStore
from src.ports.retriever import IRetriever
from src.ports.task_store import ITaskStore
from src.ports.workspace_store import IWorkspaceStore


# ── 支持的文件格式 ────────────────────────────────────────────────────────
SUPPORTED_SUFFIXES: Set[str] = {
    ".md", ".txt", ".py", ".ts", ".java",
    ".json", ".yaml", ".yml",
}
TEXT_SUFFIXES: Set[str] = {".pdf", ".docx"}   # 需要额外解析器（后续扩展）

# ── 领域推断关键词 ────────────────────────────────────────────────────────
_DOMAIN_HINTS = {
    "resume": ["resume", "简历", "cv", "work_experience", "项目经验"],
    "jd": ["jd", "job", "岗位", "招聘", "description", "requirement"],
    "notes": ["note", "笔记", "memo", "学习", "总结"],
    "paper": ["paper", "论文", "research", "study", "abstract"],
    "prompts": ["prompt", "template", "模板"],
}

_TECH_KEYWORDS = {
    "Python": ["python", "django", "flask", "fastapi"],
    "JavaScript": ["javascript", "js", "node", "react", "vue"],
    "TypeScript": ["typescript", "ts"],
    "Java": ["java", "spring", "maven"],
    "SQL": ["sql", "mysql", "postgres", "sqlite"],
    "Docker": ["docker", "container", "k8s", "kubernetes"],
    "AI/ML": ["pytorch", "tensorflow", "sklearn", "llm", "gpt", "bert"],
    "架构": ["microservice", "微服务", "架构", "architecture", "design pattern"],
}


@dataclass(frozen=True)
class IngestProgress:
    current: int
    total: int
    message: str
    task_id: str = ""
    done: bool = False
    error: Optional[str] = None
    stage: str = ""            # "scan" | "process" | "embed" | "store" | "done"
    elapsed_ms: int = 0         # 从任务开始到此刻的耗时（毫秒）

    @property
    def percent(self) -> int:
        if self.total == 0:
            return 0
        return min(100, int(self.current / self.total * 100))


class IngestWorkspaceUseCase:

    def __init__(
        self,
        workspace_store: IWorkspaceStore,
        document_store: IDocumentStore,
        chunk_store: IChunkStore,
        task_store: ITaskStore,
        retriever: IRetriever,
        settings: AppSettings,
    ) -> None:
        self._workspace_store = workspace_store
        self._document_store = document_store
        self._chunk_store = chunk_store
        self._task_store = task_store
        self._retriever = retriever
        self._settings = settings

    def execute(
        self,
        workspace_id: str,
        force_reindex: bool = False,
    ) -> Iterator[IngestProgress]:
        """
        生成器。调用方迭代此生成器以驱动进度。
        每 yield 一次 IngestProgress，调用方可将其转发给 UI。
        """
        ws = self._workspace_store.get(workspace_id)
        if ws is None:
            raise NotFoundError("Workspace", workspace_id)

        task = Task.create(TaskKind.INGEST, f"开始摄入：{ws.name}")
        self._task_store.save(task)

        try:
            yield from self._run(ws, task, force_reindex)
        except Exception as exc:
            failed_task = task.update(TaskStatus.FAILED, 0, str(exc))
            self._task_store.update(failed_task)
            yield IngestProgress(
                current=0, total=1,
                message=f"摄入失败：{exc}",
                task_id=task.id,
                done=True,
                error=str(exc),
                stage="error",
            )

    def _run(self, ws, task: Task, force_reindex: bool) -> Iterator[IngestProgress]:
        t0 = time.monotonic()

        def _p(current: int, total: int, message: str,
               stage: str = "", done: bool = False,
               error: Optional[str] = None) -> IngestProgress:
            elapsed = int((time.monotonic() - t0) * 1000)
            return IngestProgress(
                current=current, total=total, message=message,
                task_id=task.id, done=done, error=error,
                stage=stage, elapsed_ms=elapsed,
            )

        root = Path(ws.root_path)
        if not root.exists():
            raise FileNotFoundError(f"知识库目录不存在：{root}")

        # ① 扫描文件
        yield _p(0, 1, "扫描文件中...", stage="scan")
        files = [
            p for p in sorted(root.rglob("*"))
            if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES
        ]
        total_files = len(list(root.rglob("*") if root.exists() else []))
        if not files:
            ws_updated = ws.with_index_stats("ok", total_files, 0)
            self._workspace_store.update(ws_updated)
            done_task = task.update(TaskStatus.DONE, 100, "目录中没有可支持的文件")
            self._task_store.update(done_task)
            yield _p(1, 1, "完成（无文件）", stage="done", done=True)
            return

        total = len(files)

        # ② 决定重建 vs 增量
        if force_reindex:
            # 全量重建：清空旧数据
            yield _p(0, total, f"全量重建：发现 {total} 个文件...", stage="scan")
            self._document_store.delete_by_workspace(ws.id)
            self._chunk_store.delete_by_workspace(ws.id)
            self._retriever.clear(ws.id)
            files_to_process = files
            new_count = total
        else:
            # 增量：仅处理新增或内容变更的文件
            yield _p(0, total, f"增量扫描：发现 {total} 个文件...", stage="scan")
            existing_docs = self._document_store.list_by_workspace(ws.id)
            existing_map: dict[str, Document] = {
                d.source_path: d for d in existing_docs
            }

            # 清理磁盘上已删除的旧文档
            deleted_ids: list[str] = []
            for doc in existing_docs:
                if not Path(doc.source_path).exists():
                    deleted_ids.append(doc.id)
            if deleted_ids:
                # TODO: 待 IDocumentStore 支持按 ID 删除后启用
                pass

            # 筛选出新文件或内容变更的文件
            files_to_process = []
            skipped = 0
            for fp in files:
                key = str(fp)
                if key in existing_map:
                    existing_doc = existing_map[key]
                    try:
                        current_content = fp.read_text(encoding="utf-8", errors="ignore")
                    except Exception:
                        skipped += 1
                        continue
                    if current_content == existing_doc.content:
                        skipped += 1
                        continue
                    # 内容已变更：删除旧文档（级联删除旧 chunks）
                    self._document_store.delete(existing_doc.id)
                files_to_process.append(fp)

            new_count = len(files_to_process)
            if new_count == 0:
                ws_updated = ws.with_index_stats("ok", total_files, total)
                self._workspace_store.update(ws_updated)
                done_task = task.update(
                    TaskStatus.DONE, 100,
                    f"无变更：{total} 个文件已是最新"
                )
                self._task_store.update(done_task)
                yield _p(1, 1, f"完成（{total} 个文件均为最新）", stage="done", done=True)
                return

            yield _p(0, new_count,
                     f"增量索引：{new_count} 个新/变更文件（跳过 {skipped} 个）",
                     stage="process")

        # ③ 逐文件处理
        all_chunks: List[Chunk] = []
        documents: List[Document] = []

        for i, file_path in enumerate(files_to_process, 1):
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                yield _p(i, new_count, f"跳过（读取失败）：{file_path.name}", stage="process")
                continue

            domain = _infer_domain(file_path, content)
            tags = _build_tags(content)
            doc = Document.create(
                workspace_id=ws.id,
                title=file_path.stem,
                source_path=str(file_path),
                content=content,
                domain=domain,
                tags=tags,
            )
            documents.append(doc)
            chunks = _split_document(doc, self._settings.chunk_size, self._settings.chunk_overlap)
            all_chunks.extend(chunks)

            yield _p(i, new_count, f"[{i}/{new_count}] {file_path.name}", stage="process")

        # ④ 批量存储
        if documents:
            self._document_store.save_batch(documents)
        if all_chunks:
            self._chunk_store.save_batch(all_chunks)

        yield _p(new_count, new_count,
                 f"存储完成，开始建立索引（{len(all_chunks)} 个片段）...",
                 stage="embed")

        # ⑤ 建立检索索引（含 Embedding）
        #  全量模式：all_chunks 已包含所有文件
        #  增量模式：从 DB 重新加载全部 chunks 以重建索引（清除变更文件的旧条目）
        if force_reindex:
            self._retriever.index(all_chunks)
        else:
            self._retriever.clear(ws.id)
            all_db_chunks = self._chunk_store.list_by_workspace(ws.id)
            self._retriever.index(all_db_chunks)

        # ⑥ 更新工作区状态
        ws_updated = ws.with_index_stats("ok", total_files, total)
        self._workspace_store.update(ws_updated)
        done_task = task.update(
            TaskStatus.DONE, 100,
            f"完成：处理 {new_count} 个文件（{len(all_chunks)} 个片段），总计 {total} 个文件"
        )
        self._task_store.update(done_task)

        yield _p(
            new_count, new_count,
            f"索引完成：{new_count} 个文件 / {len(all_chunks)} 个片段（总计 {total} 个）",
            stage="done", done=True,
        )


# ── 领域推断 ──────────────────────────────────────────────────────────────

def _infer_domain(file_path: Path, content: str) -> str:
    parts = str(file_path).lower()
    text = content[:500].lower()
    for domain, hints in _DOMAIN_HINTS.items():
        for hint in hints:
            if hint in parts or hint in text:
                return domain
    return "general"


def _build_tags(content: str) -> List[str]:
    text = content[:2000].lower()
    tags = []
    for tag, keywords in _TECH_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            tags.append(tag)
    return tags


# ── 分块 ─────────────────────────────────────────────────────────────────

# Markdown 标题匹配：## 标题 / ### 子标题
_MD_HEADING = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


def _split_document(doc: Document, chunk_size: int, overlap: int) -> List[Chunk]:
    """
    Markdown 结构感知分块。

    策略：
      1. 按 Markdown 标题（## / ### 等）切分为段落组
      2. 每个段落组以标题开头，保持上下文完整
      3. 段落组 <= chunk_size → 独立 chunk
      4. 段落组 > chunk_size → 内部滑窗切分（保持 overlap），每个子块前附标题
      5. 纯文本（无标题）直接滑窗切分
    """
    text = doc.content
    if len(text) <= chunk_size:
        return [Chunk.create(doc.id, doc.workspace_id, text, 0, doc.domain, doc.tags)]

    sections = _extract_md_sections(text)
    if not sections:
        # 无 Markdown 标题：按段落边界滑动窗口
        return _sliding_window_chunks(
            doc, text, "", chunk_size, overlap, 0
        )

    chunks: List[Chunk] = []
    order = 0
    for title, body in sections:
        if not body.strip():
            continue  # 跳过纯标题行
        full = f"{title}\n{body}".strip()
        if len(full) <= chunk_size:
            chunks.append(Chunk.create(
                doc.id, doc.workspace_id, full, order, doc.domain, doc.tags
            ))
            order += 1
        else:
            sub = _sliding_window_chunks(doc, body, title, chunk_size, overlap, order)
            chunks.extend(sub)
            order += len(sub)
    return chunks


def _extract_md_sections(text: str) -> List[tuple[str, str]]:
    """
    按 Markdown 标题切分文档为 (标题行, 正文) 的段落组。
    第一个段落组标题为空字符串（标题前的内容）。
    """
    matches = list(_MD_HEADING.finditer(text))
    if not matches:
        return []

    sections: List[tuple[str, str]] = []
    # 第一个标题前的内容
    first_pos = matches[0].start()
    if first_pos > 0:
        preamble = text[:first_pos].strip()
        if preamble:
            sections.append(("", preamble))

    for i, m in enumerate(matches):
        title = m.group(0).strip()  # 完整标题行 "## 技能"
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()
        sections.append((title, body))

    return sections


def _sliding_window_chunks(
    doc: Document,
    text: str,
    section_title: str,
    chunk_size: int,
    overlap: int,
    start_order: int,
) -> List[Chunk]:
    """对超过 chunk_size 的文本段落做滑窗切分，每个子块前附标题上下文。"""
    chunks: List[Chunk] = []
    order = start_order
    pos = 0
    while pos < len(text):
        end = min(pos + chunk_size, len(text))
        snippet = text[pos:end]
        if section_title:
            snippet = f"{section_title}\n{snippet}"
        chunks.append(Chunk.create(
            doc.id, doc.workspace_id, snippet.strip(), order, doc.domain, doc.tags
        ))
        order += 1
        if end >= len(text):
            break
        pos += chunk_size - overlap
    return chunks
