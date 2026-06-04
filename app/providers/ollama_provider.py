"""Ollama/local model provider adapter."""

from __future__ import annotations

from typing import AsyncIterator

from app.core.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionStreamChunk,
    EmbeddingRequest,
    EmbeddingResponse,
    ModelInfo,
    ProviderHealth,
    ProviderStatus,
)
from app.providers.base import BaseProvider


class OllamaProvider(BaseProvider):
    """Ollama local model provider."""

    def __init__(self, name: str, base_url: str, api_key: str | None = None) -> None:
        super().__init__(name, base_url, api_key)
        self._models = [
            ModelInfo(
                id="llama3.1",
                owned_by="meta",
                context_length=128000,
                cost_per_1k_input=0.0,
                cost_per_1k_output=0.0,
                capabilities=["chat"],
            ),
            ModelInfo(
                id="mistral",
                owned_by="mistralai",
                context_length=32768,
                cost_per_1k_input=0.0,
                cost_per_1k_output=0.0,
                capabilities=["chat"],
            ),
            ModelInfo(
                id="nomic-embed-text",
                owned_by="nomic",
                context_length=8192,
                cost_per_1k_input=0.0,
                cost_per_1k_output=0.0,
                capabilities=["embeddings"],
            ),
        ]

    async def chat_completion(
        self, request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        raise NotImplementedError

    async def chat_completion_stream(
        self, request: ChatCompletionRequest
    ) -> AsyncIterator[ChatCompletionStreamChunk]:
        raise NotImplementedError

    async def embedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        raise NotImplementedError

    async def list_models(self) -> list[ModelInfo]:
        return self._models

    def list_models_sync(self) -> list[ModelInfo]:
        return self._models

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider=self.name,
            status=ProviderStatus.HEALTHY,
            latency_ms=self.latency_ms,
        )
