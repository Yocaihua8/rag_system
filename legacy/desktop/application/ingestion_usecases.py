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

import hashlib

from legacy.desktop.config.settings import AppSettings
from legacy.desktop.domain.errors import NotFoundError
from legacy.desktop.domain.models.chunk import Chunk
from legacy.desktop.domain.models.document import Document
from legacy.desktop.domain.models.source import Source
from legacy.desktop.application.markdown_content import markdown_to_plain_text, normalize_document_content
from legacy.desktop.domain.models.task import Task, TaskKind, TaskStatus
from legacy.desktop.ports.chunk_store import IChunkStore
from legacy.desktop.ports.document_store import IDocumentStore
from legacy.desktop.ports.retriever import IRetriever
from legacy.desktop.ports.task_store import ITaskStore
from legacy.desktop.ports.source_store import ISourceStore
from legacy.desktop.ports.workspace_store import IWorkspaceStore


# ── 支持的文件格式 ────────────────────────────────────────────────────────
SUPPORTED_SUFFIXES: Set[str] = {
    ".md", ".markdown", ".txt", ".py", ".ts", ".java",
    ".json", ".yaml", ".yml", ".pdf", ".docx",
}
TEXT_SUFFIXES: Set[str] = {
    ".md", ".markdown", ".txt", ".py", ".ts", ".java",
    ".json", ".yaml", ".yml",
}  # 普通文本格式
TEXT_SOURCE_TYPES: Set[str] = {s.strip(".") for s in TEXT_SUFFIXES}
MIN_SECTION_LENGTH = 50

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
        source_store: ISourceStore | None = None,
    ) -> None:
        self._workspace_store = workspace_store
        self._document_store = document_store
        self._chunk_store = chunk_store
        self._task_store = task_store
        self._retriever = retriever
        self._settings = settings
        self._source_store = source_store

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
            existing_sources: dict[str, Source | None] = {}
            if self._source_store:
                for doc in existing_docs:
                    existing_sources[doc.source_path] = self._source_store.get_by_document(doc.id)

            # 清理磁盘上已删除的旧文档
            deleted_ids: list[str] = []
            for doc in existing_docs:
                if not Path(doc.source_path).exists():
                    deleted_ids.append(doc.id)
            if deleted_ids:
                for deleted_doc_id in deleted_ids:
                    self._retriever.remove_by_document(deleted_doc_id)
                    self._document_store.delete(deleted_doc_id)
                    if self._source_store:
                        self._source_store.delete_by_document(deleted_doc_id)

            # 筛选出新文件或内容变更的文件
            files_to_process = []
            skipped = 0
            for fp in files:
                key = str(fp)
                if key in existing_map:
                    existing_doc = existing_map[key]
                    try:
                        source_type = _infer_source_type(fp)
                        current_content = _extract_source_content(fp, source_type)
                    except Exception:
                        skipped += 1
                        continue
                    checksum = _compute_checksum(current_content)
                    if self._source_store:
                        source = existing_sources.get(key)
                        if source is not None and source.checksum == checksum:
                            skipped += 1
                            continue
                    elif current_content == existing_doc.raw_content:
                        skipped += 1
                        continue
                    # 内容已变更：删除旧文档（级联删除旧 chunks）
                    self._retriever.remove_by_document(existing_doc.id)
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
        source_records: List[Source] = []

        for i, file_path in enumerate(files_to_process, 1):
            try:
                source_type = _infer_source_type(file_path)
                content = _extract_source_content(file_path, source_type)
            except RuntimeError as exc:
                yield _p(
                    i,
                    new_count,
                    f"[{i}/{new_count}] {file_path.name}（跳过：{exc}）",
                    stage="process",
                )
                continue
            except Exception:
                yield _p(
                    i,
                    new_count,
                    f"[{i}/{new_count}] {file_path.name}（读取失败）",
                    stage="process",
                )
                continue

            checksum = _compute_checksum(content)
            domain = _infer_domain(file_path, content)
            tags = _build_tags(content)
            source_type = _infer_source_type(file_path)
            normalized = normalize_document_content(content, source_type)
            doc = Document.create(
                workspace_id=ws.id,
                title=file_path.stem,
                source_path=str(file_path),
                content=normalized.normalized_markdown,
                domain=domain,
                source_type=source_type,
                raw_content=normalized.raw_content,
                normalized_markdown=normalized.normalized_markdown,
                plain_text=normalized.plain_text,
                rendered_html=normalized.rendered_html,
                tags=tags,
            )
            documents.append(doc)
            source_records.append(
                Source.create(
                    document_id=doc.id,
                    source_type=source_type,
                    source_path=str(file_path),
                    checksum=checksum,
                )
            )
            chunks = _split_document(doc, self._settings.chunk_size, self._settings.chunk_overlap)
            all_chunks.extend(chunks)

            yield _p(i, new_count, f"[{i}/{new_count}] {file_path.name}", stage="process")

        # ④ 批量存储
        if documents:
            self._document_store.save_batch(documents)
        if all_chunks:
            self._chunk_store.save_batch(all_chunks)
        if self._source_store:
            for source in source_records:
                self._source_store.save(source)

        yield _p(new_count, new_count,
                 f"存储完成，开始建立索引（{len(all_chunks)} 个片段）...",
                 stage="embed")

        # ⑤ 建立检索索引（含 Embedding）
        #  全量模式：all_chunks 已包含所有文件
        if force_reindex:
            self._retriever.index(all_chunks)
        else:
            if all_chunks:
                self._retriever.index(all_chunks)

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


def _compute_checksum(content: str) -> str:
    """基于 UTF-8 文本内容计算文件 checksum。"""
    return hashlib.sha256(content.encode("utf-8", errors="ignore")).hexdigest()


def _infer_source_type(file_path: Path) -> str:
    suffix = file_path.suffix.lower().strip(".")
    return suffix if suffix else "file"


def _extract_source_content(file_path: Path, source_type: str) -> str:
    if source_type in TEXT_SOURCE_TYPES:
        return file_path.read_text(encoding="utf-8", errors="ignore")

    if source_type == "pdf":
        return _extract_pdf_text(file_path)

    if source_type == "docx":
        return _extract_docx_text(file_path)

    raise RuntimeError(f"不支持的文件类型: {source_type}")


def _extract_pdf_text(file_path: Path) -> str:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("缺少解析依赖 PyMuPDF，请先安装（pip install pymupdf）") from exc

    with fitz.open(file_path) as doc:
        text = "\n\n".join(
            (page.get_text() or "").strip() for page in doc
        ).strip()

    if not text:
        raise RuntimeError("PDF 未提取到可读文本（可能为扫描件）")
    return text


def _extract_docx_text(file_path: Path) -> str:
    try:
        from docx import Document
    except ImportError as exc:
        raise RuntimeError("缺少解析依赖 python-docx，请先安装（pip install python-docx）") from exc

    doc = Document(file_path)
    text = "\n\n".join(
        (para.text or "").strip() for para in doc.paragraphs if para.text
    ).strip()

    if not text:
        raise RuntimeError("Word 文档未提取到可读文本")
    return text


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
    text = doc.normalized_markdown
    if len(text) <= chunk_size:
        return [Chunk.create(
            doc.id,
            doc.workspace_id,
            text,
            0,
            doc.domain,
            doc.tags,
            project_id=doc.project_id,
            chunk_markdown=text,
            chunk_plain_text=doc.plain_text,
            token_count=_estimate_token_count(doc.plain_text),
        )]

    sections = _extract_md_sections(text)
    if not sections:
        # 无 Markdown 标题：按段落边界滑动窗口
        return _sliding_window_chunks(
            doc, text, "", chunk_size, overlap, 0
        )

    chunks: List[Chunk] = []
    order = 0
    short_sections: List[str] = []

    def _flush_short_sections() -> None:
        nonlocal order, chunks, short_sections
        if not short_sections:
            return
        merged = "\n\n".join(short_sections).strip()
        if len(merged) <= chunk_size:
            chunks.append(Chunk.create(
                doc.id, doc.workspace_id, merged, order, doc.domain, doc.tags,
                project_id=doc.project_id,
                chunk_markdown=merged,
                chunk_plain_text=markdown_to_plain_text(merged),
                token_count=_estimate_token_count(markdown_to_plain_text(merged)),
            ))
            order += 1
        else:
            sub = _sliding_window_chunks(
                doc, merged, "", chunk_size, overlap, order,
            )
            chunks.extend(sub)
            order += len(sub)
        short_sections = []

    for title, body in sections:
        if not body.strip():
            continue  # 跳过纯标题行
        full = f"{title}\n{body}".strip()
        if len(full) < MIN_SECTION_LENGTH:
            short_sections.append(full)
            continue

        _flush_short_sections()
        if len(full) <= chunk_size:
            chunks.append(Chunk.create(
                doc.id, doc.workspace_id, full, order, doc.domain, doc.tags,
                project_id=doc.project_id,
                chunk_markdown=full,
                chunk_plain_text=markdown_to_plain_text(full),
                token_count=_estimate_token_count(markdown_to_plain_text(full)),
            ))
            order += 1
        else:
            sub = _sliding_window_chunks(doc, body, title, chunk_size, overlap, order)
            chunks.extend(sub)
            order += len(sub)
    _flush_short_sections()

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
            doc.id, doc.workspace_id, snippet.strip(), order, doc.domain, doc.tags,
            project_id=doc.project_id,
            chunk_markdown=snippet.strip(),
            chunk_plain_text=markdown_to_plain_text(snippet.strip()),
            token_count=_estimate_token_count(markdown_to_plain_text(snippet.strip())),
        ))
        order += 1
        if end >= len(text):
            break
        pos += chunk_size - overlap
    return chunks


def _estimate_token_count(text: str) -> int:
    return len(text.split())
