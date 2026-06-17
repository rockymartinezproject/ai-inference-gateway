"""Anthropic provider adapter."""

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


class AnthropicProvider(BaseProvider):
    """Anthropic API provider."""

    def __init__(self, name: str, base_url: str, api_key: str | None = None) -> None:
        super().__init__(name, base_url, api_key)
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "x-api-key": self.api_key or "",
                "anthropic-version": "2023-06-01",
            },
            timeout=httpx.Timeout(60.0, connect=5.0),
        )
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

    def _to_anthropic_messages(self, messages: list) -> tuple[list[dict], str | None]:
        """Convert OpenAI-style messages to Anthropic format.

        Anthropic uses a single 'system' parameter and 'user'/'assistant' messages.
        """
        system_prompt = None
        chat_messages = []
        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                chat_messages.append({"role": msg.role, "content": msg.content})
        return chat_messages, system_prompt

    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        messages, system = self._to_anthropic_messages(request.messages)
        payload: dict = {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_tokens or 1024,
        }
        if system:
            payload["system"] = system
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.top_p is not None:
            payload["top_p"] = request.top_p

        try:
            resp = await self._client.post("/v1/messages", json=payload)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                f"Anthropic error: {exc.response.status_code} {exc.response.text}",
                provider=self.name,
            ) from exc
        except httpx.RequestError as exc:
            raise ProviderError(f"Anthropic request failed: {exc}", provider=self.name) from exc

        content_text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content_text += block.get("text", "")

        return ChatCompletionResponse(
            id=data["id"],
            created=int(time.time()),
            model=data["model"],
            choices=[
                Choice(
                    index=0,
                    message={"role": "assistant", "content": content_text},
                    finish_reason=data.get("stop_reason"),
                )
            ],
            usage=Usage(
                prompt_tokens=data["usage"]["input_tokens"],
                completion_tokens=data["usage"]["output_tokens"],
                total_tokens=data["usage"]["input_tokens"] + data["usage"]["output_tokens"],
            ),
        )

    async def chat_completion_stream(
        self, request: ChatCompletionRequest
    ) -> AsyncIterator[ChatCompletionStreamChunk]:
        messages, system = self._to_anthropic_messages(request.messages)
        payload: dict = {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_tokens or 1024,
            "stream": True,
        }
        if system:
            payload["system"] = system
        if request.temperature is not None:
            payload["temperature"] = request.temperature

        try:
            async with self._client.stream("POST", "/v1/messages", json=payload) as resp:
                resp.raise_for_status()
                import json as _json

                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    event = _json.loads(data_str)
                    event_type = event.get("type")

                    if event_type == "content_block_delta":
                        delta = event.get("delta", {})
                        if delta.get("type") == "text_delta":
                            yield ChatCompletionStreamChunk(
                                id=event.get("message", {}).get("id", "anthropic-stream"),
                                created=int(time.time()),
                                model=request.model,
                                choices=[
                                    Choice(
                                        index=0,
                                        delta={"role": None, "content": delta.get("text")},
                                    )
                                ],
                            )
                    elif event_type == "message_stop":
                        break
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                f"Anthropic stream error: {exc.response.status_code}",
                provider=self.name,
            ) from exc
        except httpx.RequestError as exc:
            raise ProviderError(f"Anthropic stream failed: {exc}", provider=self.name) from exc

    async def embedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        raise ProviderError("Anthropic does not support embeddings", provider=self.name)

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
            # Anthropic doesn't have a simple ping endpoint; use models or a minimal request
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
