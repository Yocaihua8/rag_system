from __future__ import annotations

import hashlib
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Mapping


OBSIDIAN_ARTIFACT_TYPES = {
    "project_understanding",
    "knowledge_coverage",
    "learning_plan",
    "assessment_record",
}
MANAGED_FRONTMATTER_KEYS = (
    "knowledge_island_managed",
    "knowledge_island_id",
    "knowledge_island_project_id",
    "knowledge_island_artifact_type",
    "knowledge_island_revision",
)
_WINDOWS_INVALID_SEGMENT = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")


def normalize_vault_path(
    value: object,
    *,
    field: str = "path",
    require_markdown: bool = True,
) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} is required")
    path = value.strip()
    if not path:
        raise ValueError(f"{field} is required")
    if "\x00" in path:
        raise ValueError(f"{field} contains a null byte")
    if "\\" in path:
        raise ValueError(f"{field} must use forward slashes")
    if path.startswith("/") or _WINDOWS_DRIVE.match(path):
        raise ValueError(f"{field} must be a vault-relative path")
    segments = path.split("/")
    if any(segment in {"", ".", ".."} for segment in segments):
        raise ValueError(f"{field} contains an unsafe path segment")
    if require_markdown and not path.casefold().endswith(".md"):
        raise ValueError(f"{field} must reference a Markdown file")
    return "/".join(segments)


def normalize_output_root(value: object) -> str:
    return normalize_vault_path(
        value,
        field="output_root",
        require_markdown=False,
    )


def default_output_root(project_name: str) -> str:
    clean_name = _WINDOWS_INVALID_SEGMENT.sub("-", project_name.strip())
    clean_name = re.sub(r"\s+", " ", clean_name).strip(" .-")
    if clean_name in {"", ".", ".."}:
        clean_name = "项目"
    return normalize_output_root(f"Knowledge Island/{clean_name[:80]}")


def path_is_within_root(path: str, root: str) -> bool:
    return path == root or path.startswith(f"{root}/")


def text_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def stable_artifact_id(
    project_id: str,
    artifact_type: str,
    discriminator: str = "",
) -> str:
    if artifact_type not in OBSIDIAN_ARTIFACT_TYPES:
        raise ValueError("unsupported artifact_type")
    seed = f"knowledge-island:{project_id}:{artifact_type}:{discriminator}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, seed))


def artifact_target_path(
    output_root: str,
    artifact_type: str,
    *,
    timestamp: str = "",
) -> str:
    clean_root = normalize_output_root(output_root)
    filenames = {
        "project_understanding": "项目理解.md",
        "knowledge_coverage": "知识覆盖与技能差距.md",
        "learning_plan": "学习计划.md",
    }
    if artifact_type in filenames:
        return normalize_vault_path(f"{clean_root}/{filenames[artifact_type]}")
    if artifact_type != "assessment_record":
        raise ValueError("unsupported artifact_type")
    clean_timestamp = _publication_timestamp(timestamp)
    return normalize_vault_path(
        f"{clean_root}/评估记录/{clean_timestamp}.md"
    )


def render_managed_markdown(
    *,
    stable_id: str,
    project_id: str,
    artifact_type: str,
    revision: int,
    body: str,
) -> str:
    if artifact_type not in OBSIDIAN_ARTIFACT_TYPES:
        raise ValueError("unsupported artifact_type")
    if not stable_id.strip() or not project_id.strip():
        raise ValueError("stable_id and project_id are required")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        raise ValueError("revision must be a positive integer")
    frontmatter = (
        "---\n"
        "knowledge_island_managed: true\n"
        f'knowledge_island_id: "{_yaml_string(stable_id)}"\n'
        f'knowledge_island_project_id: "{_yaml_string(project_id)}"\n'
        f'knowledge_island_artifact_type: "{_yaml_string(artifact_type)}"\n'
        f"knowledge_island_revision: {revision}\n"
        "---\n\n"
    )
    return f"{frontmatter}{body.strip()}\n"


def managed_frontmatter_matches(
    frontmatter: Mapping[str, Any] | None,
    *,
    stable_id: str,
    project_id: str,
    artifact_type: str,
) -> bool:
    if not isinstance(frontmatter, Mapping):
        return False
    managed = frontmatter.get("knowledge_island_managed")
    return bool(
        managed is True
        and str(frontmatter.get("knowledge_island_id") or "") == stable_id
        and str(frontmatter.get("knowledge_island_project_id") or "")
        == project_id
        and str(frontmatter.get("knowledge_island_artifact_type") or "")
        == artifact_type
    )


def markdown_body(content: str) -> str:
    if not content.startswith("---\n"):
        return content.strip()
    marker = content.find("\n---", 4)
    if marker < 0:
        return content.strip()
    return content[marker + 4 :].lstrip("\r\n").rstrip()


def _publication_timestamp(value: str) -> str:
    if value:
        parsed = value.strip()
        if re.fullmatch(r"\d{8}-\d{6}", parsed):
            return parsed
        try:
            moment = datetime.fromisoformat(parsed.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("timestamp must be ISO-8601 or YYYYMMDD-HHMMSS") from exc
    else:
        moment = datetime.now(timezone.utc)
    return moment.astimezone(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _yaml_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


__all__ = [
    "MANAGED_FRONTMATTER_KEYS",
    "OBSIDIAN_ARTIFACT_TYPES",
    "artifact_target_path",
    "default_output_root",
    "managed_frontmatter_matches",
    "markdown_body",
    "normalize_output_root",
    "normalize_vault_path",
    "path_is_within_root",
    "render_managed_markdown",
    "stable_artifact_id",
    "text_sha256",
]
