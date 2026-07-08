"""Real-provider integration tests.

These tests are skipped unless the corresponding provider API key or base URL
is set in the environment. They validate the gateway provider adapters against
live endpoints and are intended to be run manually or via workflow_dispatch.
"""

from __future__ import annotations

import os

import pytest

from app.providers.anthropic_provider import AnthropicProvider
from app.providers.ollama_provider import OllamaProvider
from app.providers.openai_provider import OpenAIProvider


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)
@pytest.mark.anyio
async def test_openai_chat_completions() -> None:
    provider = OpenAIProvider(
        name="openai-real",
        base_url="https://api.openai.com/v1",
        api_key=os.environ["OPENAI_API_KEY"],
    )
    response = await provider.chat_completion(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say 'hello' and nothing else."}],
        temperature=0.0,
    )
    assert "choices" in response
    assert len(response["choices"]) > 0
    content = response["choices"][0].get("message", {}).get("content", "")
    assert "hello" in content.lower()


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)
@pytest.mark.anyio
async def test_anthropic_chat_completions() -> None:
    provider = AnthropicProvider(
        name="anthropic-real",
        base_url="https://api.anthropic.com/v1",
        api_key=os.environ["ANTHROPIC_API_KEY"],
    )
    response = await provider.chat_completion(
        model="claude-3-haiku-20240307",
        messages=[{"role": "user", "content": "Say 'hello' and nothing else."}],
        temperature=0.0,
    )
    assert "choices" in response
    assert len(response["choices"]) > 0
    content = response["choices"][0].get("message", {}).get("content", "")
    assert "hello" in content.lower()


@pytest.mark.skipif(
    not os.environ.get("OLLAMA_BASE_URL"),
    reason="OLLAMA_BASE_URL not set",
)
@pytest.mark.anyio
async def test_ollama_chat_completions() -> None:
    provider = OllamaProvider(
        name="ollama-real",
        base_url=os.environ["OLLAMA_BASE_URL"],
    )
    models = await provider.list_models()
    assert isinstance(models, list)
    if not models:
        pytest.skip("No Ollama models available")
    response = await provider.chat_completion(
        model=models[0]["id"],
        messages=[{"role": "user", "content": "Say 'hello' and nothing else."}],
        temperature=0.0,
    )
    assert "choices" in response
    assert len(response["choices"]) > 0
    content = response["choices"][0].get("message", {}).get("content", "")
    assert "hello" in content.lower()
