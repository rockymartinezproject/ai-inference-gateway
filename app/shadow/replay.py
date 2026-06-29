"""Shadow mode and request replay for safe provider testing."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from app.core.models import ChatCompletionRequest, ChatCompletionResponse
from app.providers.registry import ProviderRegistry


@dataclass
class ShadowResult:
    """Result of a shadow traffic comparison."""

    provider: str
    model: str
    latency_ms: float
    success: bool
    tokens_used: int
    error: str | None = None
    response_preview: str | None = None


class ShadowMode:
    """Duplicates production traffic to test providers without affecting responses."""

    def __init__(self, registry: ProviderRegistry) -> None:
        self.registry = registry
        self.enabled = False
        self.target_providers: list[str] = []
        self.results: list[ShadowResult] = []

    def enable(self, target_providers: list[str]) -> None:
        """Enable shadow mode for specific providers."""
        self.enabled = True
        self.target_providers = target_providers

    def disable(self) -> None:
        """Disable shadow mode."""
        self.enabled = False
        self.target_providers = []

    async def send_shadow(
        self,
        request: ChatCompletionRequest,
        primary_response: ChatCompletionResponse,
    ) -> list[ShadowResult]:
        """Send shadow traffic and compare results."""
        if not self.enabled:
            return []

        results = []
        tasks = []

        for provider_name in self.target_providers:
            provider = self.registry.get(provider_name)
            if not provider or not provider.healthy:
                continue
            tasks.append(self._shadow_request(provider, request))

        if tasks:
            shadow_results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in shadow_results:
                if isinstance(result, ShadowResult):
                    results.append(result)

        self.results.extend(results)
        return results

    async def _shadow_request(
        self,
        provider,
        request: ChatCompletionRequest,
    ) -> ShadowResult:
        import time

        start = time.perf_counter()
        try:
            response = await provider.chat_completion(request)
            latency_ms = (time.perf_counter() - start) * 1000
            content = response.choices[0].message.content if response.choices else ""
            return ShadowResult(
                provider=provider.name,
                model=request.model,
                latency_ms=round(latency_ms, 2),
                success=True,
                tokens_used=response.usage.total_tokens,
                response_preview=content[:200] if content else None,
            )
        except Exception as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            return ShadowResult(
                provider=provider.name,
                model=request.model,
                latency_ms=round(latency_ms, 2),
                success=False,
                tokens_used=0,
                error=str(exc),
            )

    def get_comparison_report(self, limit: int = 100) -> dict[str, Any]:
        """Generate a comparison report of shadow traffic results."""
        recent = self.results[-limit:]
        by_provider: dict[str, list[ShadowResult]] = {}
        for r in recent:
            by_provider.setdefault(r.provider, []).append(r)

        report = {}
        for provider, results in by_provider.items():
            successes = [r for r in results if r.success]
            report[provider] = {
                "total_requests": len(results),
                "success_rate": len(successes) / len(results) if results else 0,
                "avg_latency_ms": (
                    round(sum(r.latency_ms for r in successes) / len(successes), 2)
                    if successes
                    else 0
                ),
                "avg_tokens": (
                    sum(r.tokens_used for r in successes) // len(successes) if successes else 0
                ),
            }
        return report


class RequestReplay:
    """Replay saved requests against providers for testing."""

    def __init__(self, registry: ProviderRegistry) -> None:
        self.registry = registry
        self._saved_requests: list[ChatCompletionRequest] = []

    def save(self, request: ChatCompletionRequest) -> None:
        """Save a request for later replay."""
        self._saved_requests.append(request)

    async def replay(
        self,
        provider_name: str,
        count: int | None = None,
    ) -> list[dict[str, Any]]:
        """Replay saved requests against a specific provider."""
        provider = self.registry.get(provider_name)
        if not provider:
            raise ValueError(f"Provider {provider_name} not found")

        requests = self._saved_requests[-count:] if count else self._saved_requests
        results = []

        for req in requests:
            import time

            start = time.perf_counter()
            try:
                response = await provider.chat_completion(req)
                latency_ms = (time.perf_counter() - start) * 1000
                results.append(
                    {
                        "model": req.model,
                        "success": True,
                        "latency_ms": round(latency_ms, 2),
                        "tokens": response.usage.total_tokens,
                        "response": (
                            response.choices[0].message.content[:200] if response.choices else ""
                        ),
                    }
                )
            except Exception as exc:
                latency_ms = (time.perf_counter() - start) * 1000
                results.append(
                    {
                        "model": req.model,
                        "success": False,
                        "latency_ms": round(latency_ms, 2),
                        "error": str(exc),
                    }
                )

        return results
