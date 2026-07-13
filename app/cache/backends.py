"""Pluggable embedding backends for semantic caching."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class EmbeddingBackend(ABC):
    """Abstract embedding backend."""

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Return embedding vector for text."""
        ...

    @abstractmethod
    def similarity(self, a: list[float], b: list[float]) -> float:
        """Return cosine similarity between two vectors."""
        ...


class ExactMatchBackend(EmbeddingBackend):
    """Fallback backend: only exact text matches count."""

    def embed(self, text: str) -> list[float]:
        # Use a simple hash-based embedding so identical texts match
        return [hash(text) % 10000 / 10000.0]

    def similarity(self, a: list[float], b: list[float]) -> float:
        return 1.0 if a == b else 0.0


class SentenceTransformerBackend(EmbeddingBackend):
    """Production backend using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is required for SentenceTransformerBackend. "
                "Install it with: pip install sentence-transformers"
            ) from exc
        self._model = SentenceTransformer(model_name)

    def embed(self, text: str) -> list[float]:
        import numpy as np

        vec = self._model.encode(text, convert_to_numpy=True)
        if isinstance(vec, np.ndarray):
            return vec.tolist()
        return list(vec)

    def similarity(self, a: list[float], b: list[float]) -> float:
        import math

        dot = sum(x * y for x, y in zip(a, b, strict=False))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
