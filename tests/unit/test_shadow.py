"""Tests for shadow mode and request replay."""

from __future__ import annotations

import pytest

from app.core.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    Choice,
    Usage,
)
from app.providers.base import BaseProvider
from app.shadow.replay import RequestReplay, ShadowMode


class FakeProvider(BaseProvider):
    def __init__(self, name: str, response_text: str = "ok") -> None:
        super().__init__(name, "http://fake")
        self.response_text = response_text
        self.calls = 0

    async def chat_completion(self, request):  # noqa: ARG002
        self.calls += 1
        return ChatCompletionResponse(
            id="fake",
            created=1,
            model="gpt-4",
            choices=[Choice(message={"role": "assistant", "content": self.response_text})],
            usage=Usage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        )

    async def chat_completion_stream(self, request):  # noqa: ARG002
        return
        yield  # type: ignore[unreachable]

    async def embedding(self, request):  # noqa: ARG002
        raise NotImplementedError

    async def list_models(self):
        return []

    def list_models_sync(self):
        return []

    async def health_check(self):
        from app.core.models import ProviderHealth, ProviderStatus

        return ProviderHealth(provider=self.name, status=ProviderStatus.HEALTHY)


class FakeRegistry:
    def __init__(self, providers: list[BaseProvider]) -> None:
        self._providers = {p.name: p for p in providers}

    def get(self, name: str):
        return self._providers.get(name)

    def all(self):
        return list(self._providers.values())


def test_shadow_mode_disabled_by_default() -> None:
    reg = FakeRegistry([FakeProvider("p1")])
    shadow = ShadowMode(reg)
    assert shadow.enabled is False


def test_shadow_mode_enable_disable() -> None:
    reg = FakeRegistry([FakeProvider("p1")])
    shadow = ShadowMode(reg)
    shadow.enable(["p1"])
    assert shadow.enabled is True
    assert shadow.target_providers == ["p1"]
    shadow.disable()
    assert shadow.enabled is False


@pytest.mark.anyio
async def test_shadow_mode_sends_traffic() -> None:
    p1 = FakeProvider("p1", "response1")
    reg = FakeRegistry([p1])
    shadow = ShadowMode(reg)
    shadow.enable(["p1"])

    request = ChatCompletionRequest(
        model="gpt-4", messages=[ChatMessage(role="user", content="hi")]
    )
    primary = ChatCompletionResponse(
        id="primary",
        created=1,
        model="gpt-4",
        choices=[Choice(message={"role": "assistant", "content": "primary"})],
        usage=Usage(),
    )

    results = await shadow.send_shadow(request, primary)
    assert len(results) == 1
    assert results[0].provider == "p1"
    assert results[0].success is True
    assert p1.calls == 1


@pytest.mark.anyio
async def test_shadow_mode_disabled_returns_empty() -> None:
    reg = FakeRegistry([FakeProvider("p1")])
    shadow = ShadowMode(reg)

    request = ChatCompletionRequest(
        model="gpt-4", messages=[ChatMessage(role="user", content="hi")]
    )
    primary = ChatCompletionResponse(
        id="primary", created=1, model="gpt-4", choices=[], usage=Usage()
    )

    results = await shadow.send_shadow(request, primary)
    assert results == []


def test_shadow_report() -> None:
    from app.shadow.replay import ShadowResult

    reg = FakeRegistry([FakeProvider("p1")])
    shadow = ShadowMode(reg)
    shadow.results = [
        ShadowResult(provider="p1", model="gpt-4", latency_ms=100, success=True, tokens_used=10),
        ShadowResult(provider="p1", model="gpt-4", latency_ms=200, success=True, tokens_used=20),
    ]
    report = shadow.get_comparison_report()
    assert "p1" in report
    assert report["p1"]["total_requests"] == 2
    assert report["p1"]["success_rate"] == 1.0


@pytest.mark.anyio
async def test_request_replay() -> None:
    p1 = FakeProvider("p1", "replayed")
    reg = FakeRegistry([p1])
    replay = RequestReplay(reg)

    request = ChatCompletionRequest(
        model="gpt-4", messages=[ChatMessage(role="user", content="hi")]
    )
    replay.save(request)

    results = await replay.replay("p1")
    assert len(results) == 1
    assert results[0]["success"] is True
    assert p1.calls == 1
