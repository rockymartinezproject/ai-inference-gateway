"""OpenAI provider adapter."""

from __future__ import annotations

import time
from typing import AsyncIterator

import httpx

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
from app.core.errors import ProviderError
from app.providers.base import BaseProvider


class OpenAIProvider(BaseProvider):
    """OpenAI API provider."""

    def __init__(self, name: str, base_url: str, api_key: str | None = None) -> None:
        super().__init__(name, base_url, api_key)
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
            timeout=httpx.Timeout(60.0, connect=5.0),
        )
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
        payload = {
            "model": request.model,
            "messages": [
                {"role": m.role, "content": m.content} for m in request.messages
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "stream": False,
            "user": request.user,
        }
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        try:
            resp = await self._client.post("/v1/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                f"OpenAI error: {exc.response.status_code} {exc.response.text}",
                provider=self.name,
            ) from exc
        except httpx.RequestError as exc:
            raise ProviderError(f"OpenAI request failed: {exc}", provider=self.name) from exc

        return ChatCompletionResponse(
            id=data["id"],
            created=data["created"],
            model=data["model"],
            choices=[
                Choice(
                    index=c["index"],
                    message={"role": c["message"]["role"], "content": c["message"]["content"]},
                    finish_reason=c.get("finish_reason"),
                )
                for c in data["choices"]
            ],
            usage=Usage(
                prompt_tokens=data["usage"]["prompt_tokens"],
                completion_tokens=data["usage"]["completion_tokens"],
                total_tokens=data["usage"]["total_tokens"],
            ),
        )

    async def chat_completion_stream(
        self, request: ChatCompletionRequest
    ) -> AsyncIterator[ChatCompletionStreamChunk]:
        payload = {
            "model": request.model,
            "messages": [
                {"role": m.role, "content": m.content} for m in request.messages
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "stream": True,
            "user": request.user,
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        try:
            async with self._client.stream(
                "POST", "/v1/chat/completions", json=payload
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        import json as _json

                        chunk_data = _json.loads(data_str)
                        yield ChatCompletionStreamChunk(
                            id=chunk_data["id"],
                            created=chunk_data["created"],
                            model=chunk_data["model"],
                            choices=[
                                Choice(
                                    index=c["index"],
                                    delta={
                                        "role": c["delta"].get("role"),
                                        "content": c["delta"].get("content"),
                                    },
                                    finish_reason=c.get("finish_reason"),
                                )
                                for c in chunk_data["choices"]
                            ],
                        )
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                f"OpenAI stream error: {exc.response.status_code}",
                provider=self.name,
            ) from exc
        except httpx.RequestError as exc:
            raise ProviderError(f"OpenAI stream failed: {exc}", provider=self.name) from exc

    async def embedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        payload = {
            "model": request.model,
            "input": request.input,
            "user": request.user,
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        try:
            resp = await self._client.post("/v1/embeddings", json=payload)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                f"OpenAI embedding error: {exc.response.status_code}",
                provider=self.name,
            ) from exc
        except httpx.RequestError as exc:
            raise ProviderError(
                f"OpenAI embedding request failed: {exc}", provider=self.name
            ) from exc

        return EmbeddingResponse(
            data=[
                {
                    "object": "embedding",
                    "embedding": d["embedding"],
                    "index": d["index"],
                }
                for d in data["data"]
            ],
            model=data["model"],
            usage=Usage(
                prompt_tokens=data["usage"]["prompt_tokens"],
                total_tokens=data["usage"]["total_tokens"],
            ),
        )

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
        start = time.perf_counter()
        try:
            resp = await self._client.get("/v1/models", timeout=5.0)
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
