"""Provider registry for capability-based discovery and routing."""

from __future__ import annotations

from collections.abc import Iterator

from app.core.models import ModelInfo, ProviderHealth
from app.providers.base import BaseProvider


class ProviderRegistry:
    """Registry of all configured LLM providers."""

    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}

    def register(self, provider: BaseProvider) -> None:
        """Register a provider."""
        self._providers[provider.name] = provider

    def get(self, name: str) -> BaseProvider | None:
        """Get a provider by name."""
        return self._providers.get(name)

    def all(self) -> list[BaseProvider]:
        """Return all registered providers."""
        return list(self._providers.values())

    def healthy(self) -> list[BaseProvider]:
        """Return only healthy providers."""
        return [p for p in self._providers.values() if p.healthy]

    def find_by_model(self, model_id: str) -> BaseProvider | None:
        """Find a provider that supports a given model ID."""
        for provider in self._providers.values():
            models = [m.id for m in provider.list_models_sync()]
            if model_id in models:
                return provider
        return None

    def list_all_models(self) -> list[ModelInfo]:
        """Aggregate models from all providers."""
        models: list[ModelInfo] = []
        seen: set[str] = set()
        for provider in self._providers.values():
            for model in provider.list_models_sync():
                if model.id not in seen:
                    models.append(model)
                    seen.add(model.id)
        return models

    async def health_checks(self) -> list[ProviderHealth]:
        """Run health checks on all providers."""
        results: list[ProviderHealth] = []
        for provider in self._providers.values():
            health = await provider.health_check()
            results.append(health)
        return results

    def __iter__(self) -> Iterator[BaseProvider]:
        return iter(self._providers.values())

    def __len__(self) -> int:
        return len(self._providers)


# Global registry instance — populated at startup
_registry: ProviderRegistry | None = None


def get_registry() -> ProviderRegistry:
    """Return the global provider registry."""
    if _registry is None:
        raise RuntimeError("Provider registry not initialized")
    return _registry


def set_registry(registry: ProviderRegistry) -> None:
    """Set the global provider registry."""
    global _registry
    _registry = registry
