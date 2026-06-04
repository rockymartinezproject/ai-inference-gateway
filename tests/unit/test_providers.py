"""Tests for provider registry and factory."""

from __future__ import annotations

import asyncio

import pytest

from app.core.models import ModelInfo, ProviderHealth, ProviderStatus
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.base import BaseProvider
from app.providers.ollama_provider import OllamaProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.registry import ProviderRegistry, get_registry, set_registry


class FakeProvider(BaseProvider):
    """Fake provider for testing."""

    def __init__(self, name: str = "fake") -> None:
        super().__init__(name, "http://fake")
        self._models = [
            ModelInfo(id="fake-model", owned_by="test"),
        ]

    async def chat_completion(self, request):  # noqa: ARG002
        raise NotImplementedError

    async def chat_completion_stream(self, request):  # noqa: ARG002
        raise NotImplementedError

    async def embedding(self, request):  # noqa: ARG002
        raise NotImplementedError

    async def list_models(self):
        return self._models

    def list_models_sync(self):
        return self._models

    async def health_check(self):
        return ProviderHealth(
            provider=self.name,
            status=ProviderStatus.HEALTHY,
        )


@pytest.fixture
def registry() -> ProviderRegistry:
    return ProviderRegistry()


def test_register_and_get(registry: ProviderRegistry) -> None:
    provider = FakeProvider("alpha")
    registry.register(provider)
    assert registry.get("alpha") is provider
    assert registry.get("beta") is None


def test_all_providers(registry: ProviderRegistry) -> None:
    registry.register(FakeProvider("a"))
    registry.register(FakeProvider("b"))
    assert len(registry.all()) == 2


def test_healthy_providers(registry: ProviderRegistry) -> None:
    healthy = FakeProvider("good")
    unhealthy = FakeProvider("bad")
    unhealthy.set_health(False)
    registry.register(healthy)
    registry.register(unhealthy)
    assert len(registry.healthy()) == 1


def test_find_by_model(registry: ProviderRegistry) -> None:
    provider = FakeProvider("searchable")
    registry.register(provider)
    found = registry.find_by_model("fake-model")
    assert found is provider
    assert registry.find_by_model("missing") is None


def test_list_all_models_dedup(registry: ProviderRegistry) -> None:
    p1 = FakeProvider("p1")
    p2 = FakeProvider("p2")
    p2._models = [ModelInfo(id="fake-model", owned_by="test")]  # same ID
    registry.register(p1)
    registry.register(p2)
    models = registry.list_all_models()
    assert len(models) == 1


def test_global_registry() -> None:
    reg = ProviderRegistry()
    set_registry(reg)
    assert get_registry() is reg


def test_global_registry_not_initialized() -> None:
    set_registry(None)  # type: ignore[arg-type]
    with pytest.raises(RuntimeError, match="not initialized"):
        get_registry()


def test_health_checks(registry: ProviderRegistry) -> None:
    registry.register(FakeProvider("h1"))
    results = asyncio.run(registry.health_checks())
    assert len(results) == 1
    assert results[0].provider == "h1"
    assert results[0].status == ProviderStatus.HEALTHY


def test_openai_provider_models() -> None:
    provider = OpenAIProvider("openai", "https://api.openai.com/v1", api_key="sk-test")
    models = provider.list_models_sync()
    assert len(models) >= 2
    assert any(m.id == "gpt-4o" for m in models)


def test_anthropic_provider_disabled_without_key() -> None:
    provider = AnthropicProvider("anthropic", "https://api.anthropic.com")
    models = provider.list_models_sync()
    assert len(models) >= 1


def test_ollama_provider_free() -> None:
    provider = OllamaProvider("ollama", "http://localhost:11434")
    models = provider.list_models_sync()
    assert len(models) >= 1
    assert all(m.cost_per_1k_input == 0.0 for m in models)
