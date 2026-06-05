"""
KeywordRetriever — 基于 token 词频重叠的关键词检索（降级方案）。

不依赖 Ollama 或向量库，完全在内存中运行。
适用场景：Ollama 不可用 / 首次运行向量索引尚未建立。
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Dict, List, Set

from legacy.desktop.domain.models.chunk import Chunk
from legacy.desktop.ports.retriever import IRetriever, RetrievalQuery, RetrievalResult


def _tokenize(text: str) -> Set[str]:
    """
    多语言分词：英文按单词边界、中文使用 jieba 或 bigram 提取有意义的 token。
    同时过滤停用词和过短 token。
    """
    tokens: Set[str] = set()
    text_lower = text.lower()

    # ── 英文单词（含数字） ──
    tokens.update(re.findall(r"[a-zA-Z0-9]+", text_lower))

    # ── 中文分词 ──
    _tokenize_chinese(text, tokens)

    # ── 过滤：去除过短的 token 和纯数字 ──
    return {t for t in tokens if len(t) > 1 and not t.isdigit()}


def _tokenize_chinese(text: str, tokens: Set[str]) -> None:
    """对文本中的中文片段进行分词，优先使用 jieba，回退到 bigram。"""
    # 提取连续的中文字符段
    chinese_segments = re.findall(r"[\u4e00-\u9fff]+", text)
    if not chinese_segments:
        return

    # 尝试 jieba 分词（可选轻量依赖）
    if _jieba:
        for seg in chinese_segments:
            words = _jieba.lcut(seg)
            tokens.update(w for w in words if len(w) >= 2)
    else:
        # Bigram 回退：连续双字切分
        for seg in chinese_segments:
            if len(seg) == 1:
                continue
            for i in range(len(seg) - 1):
                tokens.add(seg[i:i + 2])


# 懒加载 jieba
def _get_jieba():
    try:
        import jieba
        return jieba
    except ImportError:
        return None


_jieba = _get_jieba()


class KeywordRetriever(IRetriever):

    def __init__(self) -> None:
        # { workspace_id: List[Chunk] }
        self._index: Dict[str, List[Chunk]] = defaultdict(list)

    # ------------------------------------------------------------------ #
    # IRetriever 实现
    # ------------------------------------------------------------------ #

    def search(self, query: RetrievalQuery) -> RetrievalResult:
        candidates = self._index.get(query.workspace_id, [])
        if not candidates:
            return RetrievalResult(chunks=[], scores=[])

        q_tokens = _tokenize(query.question)
        if not q_tokens:
            return RetrievalResult(chunks=[], scores=[])

        scored = []
        for chunk in candidates:
            # 领域过滤
            if query.domains and chunk.domain not in query.domains:
                continue
            c_tokens = _tokenize(chunk.content)
            overlap = len(q_tokens & c_tokens)
            if overlap == 0:
                continue
            # 标签匹配加分
            tag_bonus = sum(1 for t in query.tags if t in chunk.tags)
            score = overlap / len(q_tokens) + tag_bonus * 0.1
            scored.append((chunk, round(score, 4)))

        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:query.top_k]
        return RetrievalResult(
            chunks=[c for c, _ in top],
            scores=[s for _, s in top],
        )

    def index(self, chunks: List[Chunk]) -> None:
        """追加到内存索引（调用前先 clear 以避免重复）。"""
        for chunk in chunks:
            self._index[chunk.workspace_id].append(chunk)

    def clear(self, workspace_id: str) -> None:
        self._index.pop(workspace_id, None)

    def remove_by_document(self, document_id: str) -> None:
        for ws_id, chunks in list(self._index.items()):
            self._index[ws_id] = [c for c in chunks if c.document_id != document_id]
