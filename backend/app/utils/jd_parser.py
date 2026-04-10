from pathlib import Path
from typing import Dict, List, Optional, Tuple

from backend.app.config import RAW_PATH


def _parse_jd_sections(text: str) -> List[Dict[str, str]]:
    sections = []
    current = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            if current:
                sections.append(current)
            current = {"header": line[3:].strip()}
            continue

        if not current:
            continue

        if line.startswith("- "):
            content = line[2:].strip()
            if "：" in content:
                key, value = content.split("：", 1)
                current[key.strip()] = value.strip()
            elif ":" in content:
                key, value = content.split(":", 1)
                current[key.strip()] = value.strip()

    if current:
        sections.append(current)

    return sections


def _split_keywords(raw_value: str) -> List[str]:
    if not raw_value:
        return []
    separators = [",", "，", "/", "|", ";", "、"]
    value = raw_value
    for sep in separators:
        value = value.replace(sep, ",")
    parts = [p.strip() for p in value.split(",")]
    return [p for p in parts if p]


def load_jd_keywords(job_name: str, jd_file: Optional[Path] = None) -> Tuple[List[str], str]:
    path = jd_file or (RAW_PATH / "jds" / "jd_library.md")
    if not path.exists():
        return [], job_name

    text = path.read_text(encoding="utf-8")
    sections = _parse_jd_sections(text)

    target = None
    for section in sections:
        title = section.get("岗位名称") or section.get("Job Title") or section.get("Job")
        if title and job_name.lower() in title.lower():
            target = section
            break

    if not target and sections:
        target = sections[0]

    if not target:
        return [], job_name

    keywords_raw = (
        target.get("技术关键词")
        or target.get("Keywords")
        or target.get("技术关键字")
        or ""
    )
    keywords = _split_keywords(keywords_raw)
    resolved_job = target.get("岗位名称") or target.get("Job Title") or job_name
    return keywords, resolved_job
