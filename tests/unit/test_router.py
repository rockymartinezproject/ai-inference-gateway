"""Tests for smart routing engine."""

from __future__ import annotations

import pytest

from app.core.errors import ModelNotFound
from app.core.models import (
    ChatCompletionRequest,
    ChatMessage,
    ModelInfo,
    ProviderHealth,
    ProviderStatus,
)
from app.providers.base import BaseProvider
from app.providers.registry import ProviderRegistry
from app.router.engine import RoutingStrategy, SmartRouter


class FakeProvider(BaseProvider):
    """Fake provider for routing tests."""

    def __init__(self, name: str, models: list[ModelInfo], latency: float | None = None) -> None:
        super().__init__(name, "http://fake")
        self._models = models
        self._latency_ms = latency
        self.call_count = 0

    async def chat_completion(self, request):  # noqa: ARG002
        self.call_count += 1
        from app.core.models import ChatCompletionResponse, Usage

        return ChatCompletionResponse(
            id=f"{self.name}-123",
            created=1,
            model=request.model,
            choices=[],
            usage=Usage(),
        )

    async def chat_completion_stream(self, request):  # noqa: ARG002
        self.call_count += 1
        return
        yield  # type: ignore[unreachable]

    async def embedding(self, request):  # noqa: ARG002
        raise NotImplementedError

    async def list_models(self):
        return self._models

    def list_models_sync(self):
        return self._models

    async def health_check(self):
        return ProviderHealth(provider=self.name, status=ProviderStatus.HEALTHY)


@pytest.fixture
def router() -> SmartRouter:
    reg = ProviderRegistry()
    reg.register(
        FakeProvider(
            "cheap",
            [
                ModelInfo(
                    id="gpt-4", owned_by="openai", cost_per_1k_input=1.0, cost_per_1k_output=2.0
                )
            ],
            latency=100.0,
        )
    )
    reg.register(
        FakeProvider(
            "expensive",
            [
                ModelInfo(
                    id="gpt-4", owned_by="openai", cost_per_1k_input=10.0, cost_per_1k_output=20.0
                )
            ],
            latency=10.0,
        )
    )
    reg.register(
        FakeProvider(
            "local",
            [
                ModelInfo(
                    id="llama3.1", owned_by="meta", cost_per_1k_input=0.0, cost_per_1k_output=0.0
                )
            ],
            latency=50.0,
        )
    )
    return SmartRouter(reg)


def test_select_provider_default(router: SmartRouter) -> None:
    req = ChatCompletionRequest(model="gpt-4", messages=[ChatMessage(role="user", content="hi")])
    provider = router.select_provider(req)
    assert provider.name in ("cheap", "expensive")


def test_select_provider_low_cost(router: SmartRouter) -> None:
    req = ChatCompletionRequest(model="gpt-4", messages=[ChatMessage(role="user", content="hi")])
    provider = router.select_provider(req, RoutingStrategy.LOW_COST)
    assert provider.name == "cheap"


def test_select_provider_low_latency(router: SmartRouter) -> None:
    req = ChatCompletionRequest(model="gpt-4", messages=[ChatMessage(role="user", content="hi")])
    provider = router.select_provider(req, RoutingStrategy.LOW_LATENCY)
    assert provider.name == "expensive"


def test_select_provider_not_found(router: SmartRouter) -> None:
    req = ChatCompletionRequest(model="unknown", messages=[ChatMessage(role="user", content="hi")])
    with pytest.raises(ModelNotFound):
        router.select_provider(req)


def test_fallback_chain_uses_fallback_models(router: SmartRouter) -> None:
    req = ChatCompletionRequest(
        model="missing",
        messages=[ChatMessage(role="user", content="hi")],
        fallback_models=["gpt-4"],
    )
    chain = router.build_fallback_chain(req)
    assert len(chain) > 0
    assert req.model == "gpt-4"  # model was updated to fallback


def test_fallback_chain_raises_when_nothing_found(router: SmartRouter) -> None:
    req = ChatCompletionRequest(model="missing", messages=[ChatMessage(role="user", content="hi")])
    with pytest.raises(ModelNotFound):
        router.build_fallback_chain(req)


def test_request_hints_override_strategy(router: SmartRouter) -> None:
    req = ChatCompletionRequest(
        model="gpt-4",
        messages=[ChatMessage(role="user", content="hi")],
        prefer_low_cost=True,
    )
    provider = router.select_provider(req, RoutingStrategy.DEFAULT)
    assert provider.name == "cheap"
