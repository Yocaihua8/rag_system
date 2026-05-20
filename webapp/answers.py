from __future__ import annotations

from webapp.models import SearchHit


def compose_answer(question: str, hits: list[SearchHit]) -> str:
    useful_hits = [hit for hit in hits if hit.score > 0]
    if not useful_hits:
        return f"没有找到与“{question}”直接相关的资料。请先导入项目文档，或换一个更具体的问题。"

    snippets = [hit.snippet for hit in useful_hits[:3] if hit.snippet]
    if not snippets:
        return "找到了相关资料，但片段为空。请检查导入文件内容。"
    return "根据已导入资料：\n\n" + "\n\n".join(f"- {snippet}" for snippet in snippets)
