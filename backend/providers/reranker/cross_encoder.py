from __future__ import annotations

import sys
from collections.abc import Callable, Sequence
from typing import Any

from backend.providers.base import BaseReranker


DEFAULT_CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class CrossEncoderReranker(BaseReranker):
    def __init__(
        self,
        model_name: str = DEFAULT_CROSS_ENCODER_MODEL,
        *,
        model_factory: Callable[[str], Any] | None = None,
    ) -> None:
        self.model_name = model_name
        self._model_factory = model_factory or _load_cross_encoder
        self._model: Any | None = None
        self._load_failed = False

    def rerank(
        self,
        query: str,
        candidates: Sequence[object],
        top_n: int | None = None,
    ) -> list[object]:
        candidate_list = list(candidates)
        if not candidate_list:
            return []
        model = self._get_model()
        if model is None:
            return _limit(candidate_list, top_n)

        pairs = [(query, _candidate_text(candidate)) for candidate in candidate_list]
        scores = [float(score) for score in model.predict(pairs)]
        ranked = sorted(
            zip(scores, candidate_list),
            key=lambda item: item[0],
            reverse=True,
        )
        return _limit([candidate for _, candidate in ranked], top_n)

    def _get_model(self) -> Any | None:
        if self._model is not None:
            return self._model
        if self._load_failed:
            return None
        try:
            self._model = self._model_factory(self.model_name)
        except ImportError:
            self._load_failed = True
            print(
                "WARNING: sentence-transformers is not installed; reranker disabled",
                file=sys.stderr,
            )
            return None
        return self._model


def _load_cross_encoder(model_name: str) -> Any:
    from sentence_transformers import CrossEncoder

    return CrossEncoder(model_name)


def _candidate_text(candidate: object) -> str:
    content = getattr(candidate, "content", None)
    if content is not None:
        return str(content)
    chunk = getattr(candidate, "chunk", None)
    chunk_content = getattr(chunk, "content", None)
    if chunk_content is not None:
        return str(chunk_content)
    snippet = getattr(candidate, "snippet", None)
    if snippet is not None:
        return str(snippet)
    return str(candidate)


def _limit(items: list[object], top_n: int | None) -> list[object]:
    if top_n is None:
        return items
    return items[:top_n]


__all__ = [
    "CrossEncoderReranker",
    "DEFAULT_CROSS_ENCODER_MODEL",
]
