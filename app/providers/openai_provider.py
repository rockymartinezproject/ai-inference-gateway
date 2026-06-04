"""OpenAI provider adapter."""

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


class OpenAIProvider(BaseProvider):
    """OpenAI API provider."""

    def __init__(self, name: str, base_url: str, api_key: str | None = None) -> None:
        super().__init__(name, base_url, api_key)
        self._models = [
            ModelInfo(
                id="gpt-4o",
                owned_by="openai",
                context_length=128000,
                cost_per_1k_input=5.0,
                cost_per_1k_output=15.0,
                capabilities=["chat", "vision", "function_calling"],
            ),
            ModelInfo(
                id="gpt-4o-mini",
                owned_by="openai",
                context_length=128000,
                cost_per_1k_input=0.15,
                cost_per_1k_output=0.6,
                capabilities=["chat", "vision"],
            ),
            ModelInfo(
                id="text-embedding-3-small",
                owned_by="openai",
                context_length=8192,
                cost_per_1k_input=0.02,
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
        if not self.api_key:
            return ProviderHealth(
                provider=self.name,
                status=ProviderStatus.DISABLED,
                error="API key not configured",
            )
        return ProviderHealth(
            provider=self.name,
            status=ProviderStatus.HEALTHY,
            latency_ms=self.latency_ms,
        )
