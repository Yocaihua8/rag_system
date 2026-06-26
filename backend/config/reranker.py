from __future__ import annotations

import importlib.util
import os
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from backend.providers.base import BaseReranker
from backend.providers.reranker.cross_encoder import CrossEncoderReranker, DEFAULT_CROSS_ENCODER_MODEL


@dataclass(frozen=True)
class RerankerSettings:
    enabled: bool = False
    model: str = DEFAULT_CROSS_ENCODER_MODEL


_CACHED_KEY: tuple[bool, str] | None = None
_CACHED_RERANKER: BaseReranker | None = None


def load_reranker_settings(environ: Mapping[str, str] | None = None) -> RerankerSettings:
    values = os.environ if environ is None else environ
    return RerankerSettings(
        enabled=_truthy(values.get("RAG_RERANKER_ENABLED", "")),
        model=str(values.get("RAG_RERANKER_MODEL") or DEFAULT_CROSS_ENCODER_MODEL),
    )


def build_reranker(
    settings: RerankerSettings | None = None,
    *,
    dependency_available: Callable[[], bool] | None = None,
) -> BaseReranker | None:
    current = settings or load_reranker_settings()
    if not current.enabled:
        return None
    dependency_check = dependency_available or _sentence_transformers_available
    if not dependency_check():
        print(
            "WARNING: sentence-transformers is not installed; reranker disabled",
            file=sys.stderr,
        )
        return None
    return CrossEncoderReranker(model_name=current.model)


def get_default_reranker() -> BaseReranker | None:
    global _CACHED_KEY, _CACHED_RERANKER

    settings = load_reranker_settings()
    key = (settings.enabled, settings.model)
    if _CACHED_KEY == key:
        return _CACHED_RERANKER

    _CACHED_KEY = key
    _CACHED_RERANKER = build_reranker(settings)
    return _CACHED_RERANKER


def _sentence_transformers_available() -> bool:
    return importlib.util.find_spec("sentence_transformers") is not None


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


__all__ = [
    "RerankerSettings",
    "build_reranker",
    "get_default_reranker",
    "load_reranker_settings",
]
