"""Smart routing engine for provider selection and fallback."""

from __future__ import annotations

import random
from enum import Enum
from typing import Callable

from app.core.errors import ModelNotFound, ProviderError
from app.core.models import ChatCompletionRequest
from app.providers.base import BaseProvider
from app.providers.registry import ProviderRegistry


class RoutingStrategy(str, Enum):
    """Available routing strategies."""

    DEFAULT = "default"
    LOW_COST = "low_cost"
    LOW_LATENCY = "low_latency"
    CAPABILITY = "capability"
    RANDOM = "random"


class SmartRouter:
    """Routes requests to providers based on strategy and handles fallback."""

    def __init__(self, registry: ProviderRegistry) -> None:
        self.registry = registry

    def _get_providers_for_model(self, model: str) -> list[BaseProvider]:
        """Find all providers that support the given model."""
        providers = []
        for provider in self.registry.healthy():
            model_ids = [m.id for m in provider.list_models_sync()]
            if model in model_ids:
                providers.append(provider)
        return providers

    def _score_cost(self, provider: BaseProvider, model: str) -> float:
        """Lower score = cheaper."""
        for m in provider.list_models_sync():
            if m.id == model:
                total_cost = (m.cost_per_1k_input or 0) + (m.cost_per_1k_output or 0)
                return total_cost
        return float("inf")

    def _score_latency(self, provider: BaseProvider) -> float:
        """Lower score = faster."""
        return provider.latency_ms or 9999.0

    def _score_capability(self, provider: BaseProvider, required: list[str]) -> int:
        """Higher score = more capabilities matched."""
        for m in provider.list_models_sync():
            caps = set(m.capabilities or [])
            return len(caps.intersection(set(required)))
        return 0

    def select_provider(
        self,
        request: ChatCompletionRequest,
        strategy: RoutingStrategy = RoutingStrategy.DEFAULT,
    ) -> BaseProvider:
        """Select the best provider for a request."""
        candidates = self._get_providers_for_model(request.model)
        if not candidates:
            raise ModelNotFound(request.model)

        if strategy == RoutingStrategy.LOW_COST or request.prefer_low_cost:
            candidates.sort(key=lambda p: self._score_cost(p, request.model))

        elif strategy == RoutingStrategy.LOW_LATENCY or request.prefer_low_latency:
            candidates.sort(key=self._score_latency)

        elif strategy == RoutingStrategy.RANDOM:
            random.shuffle(candidates)

        return candidates[0]

    def build_fallback_chain(
        self,
        request: ChatCompletionRequest,
        strategy: RoutingStrategy = RoutingStrategy.DEFAULT,
    ) -> list[BaseProvider]:
        """Build an ordered list of providers to try."""
        candidates = self._get_providers_for_model(request.model)
        if not candidates:
            # Try fallback models if primary model not found
            if request.fallback_models:
                for fallback_model in request.fallback_models:
                    candidates = self._get_providers_for_model(fallback_model)
                    if candidates:
                        request.model = fallback_model
                        break
            if not candidates:
                raise ModelNotFound(request.model)

        if strategy == RoutingStrategy.LOW_COST or request.prefer_low_cost:
            candidates.sort(key=lambda p: self._score_cost(p, request.model))
        elif strategy == RoutingStrategy.LOW_LATENCY or request.prefer_low_latency:
            candidates.sort(key=self._score_latency)

        return candidates

    async def route_chat_completion(
        self,
        request: ChatCompletionRequest,
        strategy: RoutingStrategy = RoutingStrategy.DEFAULT,
    ):
        """Route a chat completion request with fallback support."""
        chain = self.build_fallback_chain(request, strategy)
        last_error = None

        for provider in chain:
            try:
                return await provider.chat_completion(request)
            except ProviderError as exc:
                last_error = exc
                provider.set_health(False)
                continue

        raise last_error or ProviderError(
            f"All providers failed for model {request.model}"
        )

    async def route_chat_completion_stream(
        self,
        request: ChatCompletionRequest,
        strategy: RoutingStrategy = RoutingStrategy.DEFAULT,
    ):
        """Route a streaming chat completion request with fallback support."""
        chain = self.build_fallback_chain(request, strategy)
        last_error = None

        for provider in chain:
            try:
                async for chunk in provider.chat_completion_stream(request):
                    yield chunk
                return
            except ProviderError as exc:
                last_error = exc
                provider.set_health(False)
                continue

        raise last_error or ProviderError(
            f"All providers failed for model {request.model}"
        )

    async def route_embedding(self, request, strategy: RoutingStrategy = RoutingStrategy.DEFAULT):
        """Route an embedding request with fallback support."""
        chain = self.build_fallback_chain(request, strategy)
        last_error = None

        for provider in chain:
            try:
                return await provider.embedding(request)
            except ProviderError as exc:
                last_error = exc
                provider.set_health(False)
                continue

        raise last_error or ProviderError(
            f"All providers failed for model {request.model}"
        )
