"""Tests for analytics and cost tracking."""

from __future__ import annotations

import pytest

from app.analytics.tracker import CostTracker
from app.core.models import ChatCompletionResponse, Choice, Usage


@pytest.fixture
def tracker() -> CostTracker:
    t = CostTracker()
    t.register_pricing("gpt-4o", 5.0, 15.0)
    t.register_pricing("gpt-4o-mini", 0.15, 0.6)
    return t


def test_calculate_cost_chat(tracker: CostTracker) -> None:
    usage = Usage(prompt_tokens=1000, completion_tokens=500, total_tokens=1500)
    cost = tracker.calculate_cost("gpt-4o", usage)
    expected = (1000 / 1000 * 5.0) + (500 / 1000 * 15.0)
    assert cost == pytest.approx(expected, 0.001)


def test_calculate_cost_unknown_model(tracker: CostTracker) -> None:
    usage = Usage(prompt_tokens=1000, completion_tokens=500)
    cost = tracker.calculate_cost("unknown", usage)
    assert cost == 0.0


def test_track_creates_tracked_request(tracker: CostTracker) -> None:
    class FakeRequest:
        state = type("State", (), {"user_id": "user_123", "request_id": "req-abc"})()

    response = ChatCompletionResponse(
        id="chatcmpl-123",
        created=1,
        model="gpt-4o",
        choices=[Choice(message={"role": "assistant", "content": "hi"})],
        usage=Usage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )

    tracked = tracker.track(FakeRequest(), "openai", "gpt-4o", response, duration_ms=100.0)
    assert tracked.user_id == "user_123"
    assert tracked.provider == "openai"
    assert tracked.model == "gpt-4o"
    assert tracked.duration_ms == 100.0
    assert tracked.cost_usd > 0
    assert tracked.request_id == "req-abc"


def test_track_error(tracker: CostTracker) -> None:
    class FakeRequest:
        state = type("State", (), {"user_id": "user_123", "request_id": "req-abc"})()

    tracked = tracker.track_error(FakeRequest(), "openai", "gpt-4o", "ProviderError")
    assert tracked.error_type == "ProviderError"
    assert tracked.cost_usd == 0.0
    assert tracked.status_code == 500
