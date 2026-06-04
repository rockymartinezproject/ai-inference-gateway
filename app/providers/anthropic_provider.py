"""Anthropic provider adapter."""

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


class AnthropicProvider(BaseProvider):
    """Anthropic API provider."""

    def __init__(self, name: str, base_url: str, api_key: str | None = None) -> None:
        super().__init__(name, base_url, api_key)
        self._models = [
            ModelInfo(
                id="claude-3-5-sonnet-20241022",
                owned_by="anthropic",
                context_length=200000,
                cost_per_1k_input=3.0,
                cost_per_1k_output=15.0,
                capabilities=["chat", "vision", "function_calling"],
            ),
            ModelInfo(
                id="claude-3-haiku-20240307",
                owned_by="anthropic",
                context_length=200000,
                cost_per_1k_input=0.25,
                cost_per_1k_output=1.25,
                capabilities=["chat", "vision"],
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
