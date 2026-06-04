"""Abstract base class for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator

from app.core.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionStreamChunk,
    EmbeddingRequest,
    EmbeddingResponse,
    ModelInfo,
    ProviderHealth,
)


class BaseProvider(ABC):
    """Abstract interface for LLM providers."""

    def __init__(self, name: str, base_url: str, api_key: str | None = None) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._healthy = True
        self._latency_ms: float | None = None

    @property
    def healthy(self) -> bool:
        return self._healthy

    @property
    def latency_ms(self) -> float | None:
        return self._latency_ms

    @abstractmethod
    async def chat_completion(
        self, request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """Generate a chat completion."""
        ...

    @abstractmethod
    async def chat_completion_stream(
        self, request: ChatCompletionRequest
    ) -> AsyncIterator[ChatCompletionStreamChunk]:
        """Stream chat completion chunks."""
        ...

    @abstractmethod
    async def embedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings."""
        ...

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """List available models."""
        ...

    @abstractmethod
    async def health_check(self) -> ProviderHealth:
        """Check provider health."""
        ...

    def set_health(self, healthy: bool, latency_ms: float | None = None) -> None:
        """Update provider health status."""
        self._healthy = healthy
        if latency_ms is not None:
            self._latency_ms = latency_ms
