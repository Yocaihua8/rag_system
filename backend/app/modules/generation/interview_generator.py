from typing import List

from backend.app.schemas.chunk import Chunk


def _extract_points(chunks: List[Chunk]) -> List[str]:
    points = []
    for chunk in chunks:
        for line in chunk.content.splitlines():
            text = line.strip()
            if text.startswith("- ") or text.startswith("* "):
                points.append(text[2:].strip())
    if not points:
        for chunk in chunks:
            snippet = chunk.content.strip().replace("\n", " ")
            if snippet:
                points.append(snippet[:120])
    return points


def _build_story(points: List[str], keyword_hint: str) -> str:
    if not points:
        return "TODO: add more knowledge base bullets to improve the interview script."

    core = points[:3]
    story_lines = [
        "I joined the project to stabilize the Python RAG core workflow and improve API consistency.",
        "I focused on {0} and the integration details that often cause delivery risk.".format(keyword_hint),
        "Key outcomes include: {0}.".format("; ".join(core)),
        "After that, I added guardrails such as request validation and task status tracking to improve reliability.",
    ]
    return " ".join(story_lines)


def generate_interview_summary_markdown(
    job_keywords: List[str],
    retrieved_chunks: List[Chunk],
    project_name: str = "Python RAG Desktop Assistant",
) -> str:
    points = _extract_points(retrieved_chunks)
    keyword_hint = ", ".join(job_keywords[:3]) if job_keywords else "python rag delivery"

    highlights = ["- {0}".format(p) for p in points[:6]] if points else ["- TODO: add bullets in knowledge base."]

    story = _build_story(points, keyword_hint)

    return """## Interview Script: {0}

### Project Summary
- Scope: import, chunking, index build, retrieval, and answer generation.
- Role: python service delivery, API alignment, and integration debugging.
- Keywords: {1}

### Key Highlights
{2}

### Spoken Narrative (1-2 minutes)
{3}
""".format(project_name, keyword_hint, "\n".join(highlights), story)
