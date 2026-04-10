# Legacy CLI entry kept for backward compatibility.
# New primary runtime is Qt desktop: app.qt.app / app.launcher --mode qt.
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from backend.app.config import EXPORT_PATH, RAW_PATH, MATURITY_PRIORITY, ensure_storage_dirs
from backend.app.modules.generation.interview_generator import generate_interview_summary_markdown
from backend.app.modules.generation.jd_matcher import build_draft_bullets, generate_jd_match_summary
from backend.app.modules.generation.resume_generator import generate_resume_project_markdown
from backend.app.schemas.task import QueryTask
from backend.app.services.document_service import (
    build_chunks_for_documents,
    load_all_markdown_documents,
    save_processed_documents,
)
from backend.app.services.retrieval_service import SimpleRetrievalService
from backend.app.utils.jd_parser import load_jd_keywords

SORT_OPTIONS = ["updated", "keyword", "maturity"]


def _prepare_retriever():
    ensure_storage_dirs()

    documents = load_all_markdown_documents()
    if not documents:
        raise RuntimeError("No markdown documents found under F:/PersonalRAG/knowledge_base/raw")

    save_processed_documents(documents)
    chunks = build_chunks_for_documents(documents, chunk_size=520, overlap=60, save_to_disk=True)
    return documents, chunks


def run_resume(task_keywords: List[str]) -> Path:
    documents, chunks = _prepare_retriever()

    task = QueryTask(
        task_type="resume_generation",
        target_domains=["resume", "notes"],
        tags=["python", "fastapi", "rag"],
        question="RAG assistant role, show retrieval workflow, API integration, and reliability improvements",
    )

    retriever = SimpleRetrievalService(documents=documents, chunks=chunks)
    top_chunks = retriever.search_chunks(task=task, top_k=8)

    markdown = generate_resume_project_markdown(
        job_keywords=task_keywords,
        retrieved_chunks=top_chunks,
        project_name="Python RAG Desktop Assistant",
    )

    output_path = EXPORT_PATH / "demo_resume_java_backend.md"
    output_path.write_text(markdown, encoding="utf-8")
    return output_path


def run_interview(task_keywords: List[str]) -> Path:
    documents, chunks = _prepare_retriever()

    task = QueryTask(
        task_type="interview_summary",
        target_domains=["resume", "notes"],
        tags=["python", "fastapi", "rag"],
        question="Interview script: RAG pipeline workflow, retrieval quality, and integration debugging",
    )

    retriever = SimpleRetrievalService(documents=documents, chunks=chunks)
    top_chunks = retriever.search_chunks(task=task, top_k=10)

    markdown = generate_interview_summary_markdown(
        job_keywords=task_keywords,
        retrieved_chunks=top_chunks,
        project_name="Python RAG Desktop Assistant",
    )

    output_path = EXPORT_PATH / "demo_interview_script.md"
    output_path.write_text(markdown, encoding="utf-8")
    return output_path


def _dedupe_key_from_block(block: str) -> str:
    keyword = ""
    location = ""
    for line in block.splitlines():
        text = line.strip()
        if text.startswith("[技术标签]"):
            keyword = text.replace("[技术标签]", "").strip().lower()
        if text.startswith("[建议补充位置]"):
            location = text.replace("[建议补充位置]", "").strip().lower()
    return "{0}::{1}".format(keyword, location)


def _extract_index_fields(block: str) -> Dict[str, str]:
    keyword = ""
    location = ""
    updated = ""
    maturity = ""
    for line in block.splitlines():
        text = line.strip()
        if text.startswith("[技术标签]"):
            keyword = text.replace("[技术标签]", "").strip()
        if text.startswith("[建议补充位置]"):
            location = text.replace("[建议补充位置]", "").strip()
        if text.startswith("[最近更新时间]"):
            updated = text.replace("[最近更新时间]", "").strip()
        if text.startswith("[成熟度]"):
            maturity = text.replace("[成熟度]", "").strip()
    return {
        "keyword": keyword or "draft",
        "location": location or "unknown",
        "updated": updated,
        "maturity": maturity,
    }


def _extract_module_name(location: str) -> str:
    if "->" in location:
        return location.split("->", 1)[1].strip()
    return location.strip()


def _dedupe_drafts(existing_text: str, draft_blocks: List[str]) -> List[str]:
    existing_lower = existing_text.lower()
    unique_blocks = []

    for block in draft_blocks:
        key = _dedupe_key_from_block(block)
        if key and key in existing_lower:
            continue
        unique_blocks.append(block)

    return unique_blocks


def _sort_strategy(sort_by: str) -> str:
    if sort_by == "keyword":
        return "keyword asc, tie-breaker: updated desc"
    if sort_by == "maturity":
        return "maturity priority, tie-breaker: updated desc, keyword asc"
    return "updated desc, tie-breaker: keyword asc"


def _build_diff_summary(total: int, added: int, skipped: int, bullets_path: Path, sort_by: str) -> str:
    return """# Draft Writeback Preview

- Target file: {0}
- Total drafts: {1}
- New drafts to append: {2}
- Skipped (duplicate): {3}
- Sort strategy: {4}
""".format(bullets_path, total, added, skipped, _sort_strategy(sort_by))


def _build_grouped_index(deduped: List[str]) -> str:
    if not deduped:
        return "## New Draft Index\n\n- (none)"

    grouped: Dict[str, List[str]] = {}
    for block in deduped:
        info = _extract_index_fields(block)
        location = info["location"]
        keyword = info["keyword"]
        grouped.setdefault(location, []).append(keyword)

    lines = ["## New Draft Index (Grouped)"]
    for location in sorted(grouped.keys()):
        lines.append("- {0}".format(location))
        for keyword in grouped[location]:
            lines.append("  - {0}".format(keyword))
    return "\n".join(lines)


def _find_sections(lines: List[str]) -> List[Tuple[str, int, int]]:
    headers = []
    for idx, line in enumerate(lines):
        if line.startswith("## "):
            headers.append((line[3:].strip(), idx))

    sections = []
    for i, (name, start) in enumerate(headers):
        end = headers[i + 1][1] if i + 1 < len(headers) else len(lines)
        sections.append((name, start, end))
    return sections


def _maturity_rank(value: str) -> int:
    if not value:
        return 999
    return MATURITY_PRIORITY.get(value.strip().lower(), MATURITY_PRIORITY.get(value.strip(), 500))


def _sort_blocks(blocks: List[str], sort_by: str) -> List[str]:
    def sort_key(block: str) -> Tuple[int, str, str]:
        info = _extract_index_fields(block)
        keyword = info["keyword"].lower()
        updated = info["updated"] or "0000-00-00"
        maturity = info["maturity"]

        if sort_by == "keyword":
            return (999, keyword, "-" + updated)
        if sort_by == "maturity":
            return (_maturity_rank(maturity), "-" + updated, keyword)
        return (0, "-" + updated, keyword)

    return sorted(blocks, key=sort_key)


def _insert_blocks_by_module(existing_text: str, blocks: List[str], sort_by: str) -> str:
    if not blocks:
        return existing_text

    lines = existing_text.splitlines()
    sections = _find_sections(lines)

    def find_section(name: str) -> Tuple[int, int]:
        for sec_name, start, end in sections:
            if sec_name == name:
                return start, end
        return -1, -1

    remainder = []
    for block in _sort_blocks(blocks, sort_by):
        info = _extract_index_fields(block)
        module = _extract_module_name(info["location"])
        start, end = find_section(module)
        if start == -1:
            remainder.append(block)
            continue

        insert_at = end
        if insert_at > 0 and lines[insert_at - 1].strip() != "":
            lines.insert(insert_at, "")
            insert_at += 1
        lines[insert_at:insert_at] = block.splitlines()
        sections = _find_sections(lines)

    if remainder:
        lines.append("")
        lines.append("## 自动补充草稿")
        for block in _sort_blocks(remainder, sort_by):
            lines.append("")
            lines.extend(block.splitlines())

    return "\n".join(lines) + "\n"


def _append_drafts_to_bullets(draft_blocks: List[str], dry_run: bool, sort_by: str) -> List[str]:
    if not draft_blocks:
        return []

    bullets_path = RAW_PATH / "resume" / "project_bullets.md"
    existing = ""
    if bullets_path.exists():
        existing = bullets_path.read_text(encoding="utf-8")

    deduped = _dedupe_drafts(existing, draft_blocks)
    if not deduped:
        return []

    if dry_run:
        summary = _build_diff_summary(len(draft_blocks), len(deduped), len(draft_blocks) - len(deduped), bullets_path, sort_by)
        index = _build_grouped_index(deduped)
        preview_path = EXPORT_PATH / "draft_bullets_preview.md"
        preview_path.write_text(summary + "\n" + index + "\n\n" + "\n\n".join(deduped), encoding="utf-8")
        return deduped

    updated = _insert_blocks_by_module(existing, deduped, sort_by)
    bullets_path.write_text(updated, encoding="utf-8")
    return deduped


def run_jd_match(
    job_name: str,
    task_keywords: List[str],
    auto_from_library: bool,
    threshold: int,
    write_drafts: bool,
    dry_run: bool,
    sort_by: str,
) -> Path:
    documents, chunks = _prepare_retriever()

    if auto_from_library or not task_keywords:
        library_keywords, resolved_job = load_jd_keywords(job_name)
        if library_keywords:
            task_keywords = library_keywords
        job_name = resolved_job

    task = QueryTask(
        task_type="jd_match",
        target_domains=["resume", "notes", "job_jd"],
        tags=["python", "fastapi", "rag"],
        question="JD match summary for {0} with focus on retrieval, API design, and desktop integration".format(job_name),
    )

    retriever = SimpleRetrievalService(documents=documents, chunks=chunks)
    top_chunks = retriever.search_chunks(task=task, top_k=10)

    if write_drafts:
        draft_blocks = build_draft_bullets(task_keywords, top_chunks)
        _append_drafts_to_bullets(draft_blocks, dry_run, sort_by)

    markdown = generate_jd_match_summary(
        job_name=job_name,
        job_keywords=task_keywords,
        retrieved_chunks=top_chunks,
        project_name="Python RAG Desktop Assistant",
        coverage_threshold=threshold,
    )

    output_path = EXPORT_PATH / "demo_jd_match_summary.md"
    output_path.write_text(markdown, encoding="utf-8")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Resume/Project RAG MVP demo")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = False

    resume_parser = subparsers.add_parser("resume", help="Generate resume bullets")
    resume_parser.add_argument(
        "--keywords",
        nargs="*",
        default=["Python", "FastAPI", "RAG", "API Integration"],
        help="Job keywords used to tailor generated resume bullets.",
    )

    interview_parser = subparsers.add_parser("interview", help="Generate interview summary and script")
    interview_parser.add_argument(
        "--keywords",
        nargs="*",
        default=["Python", "FastAPI", "RAG", "Retrieval"],
        help="Keywords used to tailor the interview script.",
    )

    jd_parser = subparsers.add_parser("jd", help="Generate JD matching summary")
    jd_parser.add_argument(
        "--job",
        default="RAG Engineer",
        help="Job title or name for the JD match summary.",
    )
    jd_parser.add_argument(
        "--keywords",
        nargs="*",
        default=[],
        help="JD keywords used to tailor the match summary. Leave empty to auto-read from jd_library.md",
    )
    jd_parser.add_argument(
        "--auto",
        action="store_true",
        help="Force auto-read keywords from jd_library.md",
    )
    jd_parser.add_argument(
        "--threshold",
        type=int,
        default=70,
        help="Coverage threshold for warning (default: 70)",
    )
    jd_parser.add_argument(
        "--write-drafts",
        action="store_true",
        help="Append draft bullets into project_bullets.md",
    )
    jd_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview draft bullets without writing to project_bullets.md",
    )
    jd_parser.add_argument(
        "--sort-by",
        choices=SORT_OPTIONS,
        default="updated",
        help="Sort drafts within module: updated|keyword|maturity",
    )

    parser.set_defaults(command="resume")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "interview":
        output = run_interview(args.keywords)
        print("[OK] Interview script generated: {0}".format(output))
        return

    if args.command == "jd":
        output = run_jd_match(
            args.job,
            args.keywords,
            args.auto,
            args.threshold,
            args.write_drafts,
            args.dry_run,
            args.sort_by,
        )
        print("[OK] JD match summary generated: {0}".format(output))
        if args.dry_run and args.write_drafts:
            print("[OK] Draft preview: {0}".format(EXPORT_PATH / "draft_bullets_preview.md"))
        return

    output = run_resume(args.keywords)
    print("[OK] Resume markdown generated: {0}".format(output))


if __name__ == "__main__":
    main()
