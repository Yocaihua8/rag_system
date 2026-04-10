from typing import List

from backend.app.schemas.chunk import Chunk


ACTION_VERBS = ["Lead", "Design", "Implement", "Drive", "Optimize", "Integrate", "Deliver"]


def _extract_bullets(chunks: List[Chunk]) -> List[str]:
    bullets = []
    for chunk in chunks:
        for line in chunk.content.splitlines():
            text = line.strip()
            if text.startswith("- ") or text.startswith("* "):
                bullets.append(text[2:].strip())
    if not bullets:
        for chunk in chunks:
            snippet = chunk.content.strip().replace("\n", " ")
            if snippet:
                bullets.append(snippet[:120])
    return bullets


def _rewrite_bullet(raw: str, job_keywords: List[str], idx: int) -> str:
    verb = ACTION_VERBS[idx % len(ACTION_VERBS)]
    keyword_hint = ", ".join(job_keywords[:3]) if job_keywords else "python rag"
    if "improv" in raw.lower() or "reduce" in raw.lower() or "result" in raw.lower():
        return "- {0} {1}".format(verb, raw)
    return "- {0} {1}, highlighting {2} delivery and engineering reuse.".format(verb, raw, keyword_hint)


def generate_resume_project_markdown(
    job_keywords: List[str],
    retrieved_chunks: List[Chunk],
    project_name: str = "Python RAG Desktop Assistant",
) -> str:
    bullets = _extract_bullets(retrieved_chunks)
    polished = [_rewrite_bullet(b, job_keywords, i) for i, b in enumerate(bullets[:6])]

    keyword_line = ", ".join(job_keywords) if job_keywords else "Python, FastAPI, RAG"
    body = "\n".join(polished) if polished else "- TODO: retrieval is empty, add more knowledge base bullets."

    return """## {0} ({1})

- Project Scope: End-to-end workflow for import, chunking, index build, retrieval, and answer generation.
- Responsibility: Python service delivery, API alignment, and desktop integration debugging.

### Highlights
{2}

### Tech Stack
- Python, FastAPI, SQLite, Vue, pywebview
""".format(project_name, keyword_line, body)
