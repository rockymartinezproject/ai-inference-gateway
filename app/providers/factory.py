"""Factory for creating provider instances from configuration."""

from __future__ import annotations

from app.config import settings
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.base import BaseProvider
from app.providers.ollama_provider import OllamaProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.registry import ProviderRegistry


def build_registry() -> ProviderRegistry:
    """Build and populate the provider registry from environment config."""
    registry = ProviderRegistry()

    if settings.openai_api_key:
        registry.register(
            OpenAIProvider(
                name="openai",
                base_url=settings.openai_base_url,
                api_key=settings.openai_api_key,
            )
        )

    if settings.anthropic_api_key:
        registry.register(
            AnthropicProvider(
                name="anthropic",
                base_url=settings.anthropic_base_url,
                api_key=settings.anthropic_api_key,
            )
        )

    registry.register(
        OllamaProvider(
            name="ollama",
            base_url=settings.ollama_base_url,
        )
    )

    return registry
