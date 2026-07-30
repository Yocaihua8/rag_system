from __future__ import annotations

import pytest

from backend.domain.obsidian_protocol import (
    artifact_target_path,
    default_output_root,
    managed_frontmatter_matches,
    markdown_body,
    normalize_output_root,
    normalize_vault_path,
    path_is_within_root,
    render_managed_markdown,
    stable_artifact_id,
    text_sha256,
)


@pytest.mark.parametrize(
    "path",
    [
        "/absolute.md",
        "C:/vault/note.md",
        "../escape.md",
        "folder/../escape.md",
        "folder//note.md",
        "folder\\note.md",
        "folder/\x00note.md",
        "folder/note.txt",
    ],
)
def test_normalize_vault_path_rejects_unsafe_or_non_markdown_paths(path):
    with pytest.raises(ValueError):
        normalize_vault_path(path)


def test_output_root_uses_exact_segment_boundary_and_safe_default():
    root = normalize_output_root("Knowledge Island/示例项目")

    assert path_is_within_root(
        "Knowledge Island/示例项目/学习计划.md",
        root,
    )
    assert not path_is_within_root(
        "Knowledge Island/示例项目-copy/学习计划.md",
        root,
    )
    assert default_output_root(' A/B:*?" ') == "Knowledge Island/A-B"


def test_managed_markdown_has_stable_frontmatter_and_deterministic_hash():
    stable_id = stable_artifact_id(
        "project-1",
        "project_understanding",
    )
    content = render_managed_markdown(
        stable_id=stable_id,
        project_id="project-1",
        artifact_type="project_understanding",
        revision=2,
        body="# 项目理解\n\n正文",
    )

    assert content.startswith("---\nknowledge_island_managed: true\n")
    assert f'knowledge_island_id: "{stable_id}"' in content
    assert 'knowledge_island_project_id: "project-1"' in content
    assert "knowledge_island_revision: 2" in content
    assert markdown_body(content) == "# 项目理解\n\n正文"
    assert text_sha256(content) == text_sha256(content)
    assert managed_frontmatter_matches(
        {
            "knowledge_island_managed": True,
            "knowledge_island_id": stable_id,
            "knowledge_island_project_id": "project-1",
            "knowledge_island_artifact_type": "project_understanding",
        },
        stable_id=stable_id,
        project_id="project-1",
        artifact_type="project_understanding",
    )


def test_artifact_paths_are_confined_to_the_output_root():
    root = "Knowledge Island/示例"

    assert artifact_target_path(root, "project_understanding") == (
        "Knowledge Island/示例/项目理解.md"
    )
    assert artifact_target_path(root, "learning_plan") == (
        "Knowledge Island/示例/学习计划.md"
    )
    assert artifact_target_path(
        root,
        "assessment_record",
        timestamp="2026-07-23T10:20:30Z",
    ) == "Knowledge Island/示例/评估记录/20260723-102030.md"
