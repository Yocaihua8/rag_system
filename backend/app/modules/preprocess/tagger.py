from pathlib import Path
from typing import List


DOMAIN_KEYWORDS = {
    "resume": ["resume", "bullet", "project_updates"],
    "job_jd": ["jd", "job"],
    "notes": ["notes", "knowledge", "kb"],
    "paper": ["paper", "research"],
    "prompts": ["prompt", "codex", "llm", "agent"],
}

TECH_KEYWORDS = {
    "python": ["python", "fastapi"],
    "fastapi": ["fastapi"],
    "rag": ["rag", "retrieval"],
    "retrieval": ["retrieval", "search"],
    "embedding": ["embedding", "vector"],
    "chunking": ["chunk", "chunking", "split"],
    "sqlite": ["sqlite"],
    "websocket": ["websocket", "ws"],
    "api": ["api", "http"],
    "vue": ["vue", "vue3", "element-plus"],
    "draft": ["draft"],
    "export": ["export", "print"],
}


def infer_domain(file_path: Path, content: str) -> str:
    text = "{0}\n{1}".format(file_path.as_posix(), content).lower()
    path_text = file_path.as_posix().lower()

    if "/raw/resume/" in path_text:
        return "resume"
    if "/raw/jds/" in path_text:
        return "job_jd"
    if "/raw/notes/" in path_text:
        return "notes"
    if "/raw/paper/" in path_text:
        return "paper"
    if "/raw/prompts/" in path_text:
        return "prompts"

    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return domain

    return "resume"


def infer_tech_tags(content: str) -> List[str]:
    lower_content = content.lower()
    tags = []
    for tag, keywords in TECH_KEYWORDS.items():
        if any(keyword in lower_content for keyword in keywords):
            tags.append(tag)
    return tags


def build_tags(file_path: Path, content: str) -> List[str]:
    tags = set(infer_tech_tags(content))
    domain = infer_domain(file_path, content)
    tags.add(domain)

    path_text = file_path.as_posix().lower()
    if "update" in path_text:
        tags.add("update")
    if "overview" in path_text:
        tags.add("overview")

    return sorted(tags)
