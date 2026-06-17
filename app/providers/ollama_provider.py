"""Ollama/local model provider adapter."""

from __future__ import annotations

import time
from collections.abc import AsyncIterator

import httpx

from app.core.errors import ProviderError
from app.core.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionStreamChunk,
    Choice,
    EmbeddingRequest,
    EmbeddingResponse,
    ModelInfo,
    ProviderHealth,
    ProviderStatus,
    Usage,
)
from app.providers.base import BaseProvider


class OllamaProvider(BaseProvider):
    """Ollama local model provider."""

    def __init__(self, name: str, base_url: str, api_key: str | None = None) -> None:
        super().__init__(name, base_url, api_key)
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(120.0, connect=5.0),
        )
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

    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        payload = {
            "model": request.model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "stream": False,
            "options": {},
        }
        if request.temperature is not None:
            payload["options"]["temperature"] = request.temperature
        if request.max_tokens is not None:
            payload["options"]["num_predict"] = request.max_tokens

        try:
            resp = await self._client.post("/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                f"Ollama error: {exc.response.status_code} {exc.response.text}",
                provider=self.name,
            ) from exc
        except httpx.RequestError as exc:
            raise ProviderError(f"Ollama request failed: {exc}", provider=self.name) from exc

        message = data.get("message", {})
        # Ollama doesn't return token counts, estimate roughly
        prompt_tokens = sum(len(m.content.split()) for m in request.messages)
        completion_tokens = len(message.get("content", "").split())

        return ChatCompletionResponse(
            id=f"ollama-{int(time.time() * 1000)}",
            created=int(time.time()),
            model=request.model,
            choices=[
                Choice(
                    index=0,
                    message={
                        "role": message.get("role", "assistant"),
                        "content": message.get("content", ""),
                    },
                    finish_reason="stop" if data.get("done") else None,
                )
            ],
            usage=Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )

    async def chat_completion_stream(
        self, request: ChatCompletionRequest
    ) -> AsyncIterator[ChatCompletionStreamChunk]:
        payload = {
            "model": request.model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "stream": True,
            "options": {},
        }
        if request.temperature is not None:
            payload["options"]["temperature"] = request.temperature

        try:
            async with self._client.stream("POST", "/api/chat", json=payload) as resp:
                resp.raise_for_status()
                import json as _json

                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    chunk_data = _json.loads(line)
                    message = chunk_data.get("message", {})
                    yield ChatCompletionStreamChunk(
                        id=f"ollama-{int(time.time() * 1000)}",
                        created=int(time.time()),
                        model=request.model,
                        choices=[
                            Choice(
                                index=0,
                                delta={
                                    "role": message.get("role"),
                                    "content": message.get("content"),
                                },
                                finish_reason="stop" if chunk_data.get("done") else None,
                            )
                        ],
                    )
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                f"Ollama stream error: {exc.response.status_code}",
                provider=self.name,
            ) from exc
        except httpx.RequestError as exc:
            raise ProviderError(f"Ollama stream failed: {exc}", provider=self.name) from exc

    async def embedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        payload = {
            "model": request.model,
            "prompt": request.input if isinstance(request.input, str) else request.input[0],
        }

        try:
            resp = await self._client.post("/api/embeddings", json=payload)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                f"Ollama embedding error: {exc.response.status_code}",
                provider=self.name,
            ) from exc
        except httpx.RequestError as exc:
            raise ProviderError(
                f"Ollama embedding request failed: {exc}", provider=self.name
            ) from exc

        embedding = data.get("embedding", [])
        # Some Ollama versions return embedding as a list of floats,
        # others as a nested structure
        if embedding and isinstance(embedding[0], list):
            embedding = embedding[0]

        return EmbeddingResponse(
            data=[
                {
                    "object": "embedding",
                    "embedding": embedding,
                    "index": 0,
                }
            ],
            model=request.model,
            usage=Usage(prompt_tokens=0, total_tokens=0),
        )

    async def list_models(self) -> list[ModelInfo]:
        return self._models

    def list_models_sync(self) -> list[ModelInfo]:
        return self._models

    async def health_check(self) -> ProviderHealth:
        start = time.perf_counter()
        try:
            resp = await self._client.get("/api/tags", timeout=5.0)
            resp.raise_for_status()
            latency_ms = (time.perf_counter() - start) * 1000
            self.set_health(True, latency_ms)
            return ProviderHealth(
                provider=self.name,
                status=ProviderStatus.HEALTHY,
                latency_ms=round(latency_ms, 2),
            )
        except Exception as exc:
            self.set_health(False)
            return ProviderHealth(
                provider=self.name,
                status=ProviderStatus.UNHEALTHY,
                error=str(exc),
            )

    async def close(self) -> None:
        await self._client.aclose()
