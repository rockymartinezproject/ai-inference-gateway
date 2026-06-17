"""Cost tracking and request analytics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.core.models import ChatCompletionResponse, EmbeddingResponse, Usage

if TYPE_CHECKING:
    from fastapi import Request


@dataclass
class TrackedRequest:
    """Normalized tracked request data."""

    user_id: str
    provider: str
    model: str
    request_type: str
    usage: Usage
    duration_ms: float | None = None
    cost_usd: float = 0.0
    strategy: str | None = None
    fallback_used: int = 0
    cache_hit: bool = False
    status_code: int | None = None
    error_type: str | None = None
    request_id: str | None = None


class CostTracker:
    """Calculate and record costs for inference requests."""

    def __init__(self) -> None:
        self._model_pricing: dict[str, tuple[float, float]] = {}

    def register_pricing(
        self, model_id: str, cost_per_1k_input: float, cost_per_1k_output: float
    ) -> None:
        """Register pricing for a model."""
        self._model_pricing[model_id] = (cost_per_1k_input, cost_per_1k_output)

    def calculate_cost(self, model_id: str, usage: Usage) -> float:
        """Calculate cost in USD for a request."""
        input_price, output_price = self._model_pricing.get(model_id, (0.0, 0.0))
        input_cost = (usage.prompt_tokens / 1000.0) * input_price
        output_cost = (usage.completion_tokens / 1000.0) * output_price
        return round(input_cost + output_cost, 6)

    def track(
        self,
        request: Request,
        provider: str,
        model: str,
        response: ChatCompletionResponse | EmbeddingResponse,
        duration_ms: float | None = None,
        strategy: str | None = None,
        fallback_used: int = 0,
        cache_hit: bool = False,
    ) -> TrackedRequest:
        """Track a completed request and return tracking data."""
        user_id = getattr(request.state, "user_id", "anonymous")
        request_id = getattr(request.state, "request_id", None)

        request_type = "chat" if isinstance(response, ChatCompletionResponse) else "embedding"
        cost = self.calculate_cost(model, response.usage)

        tracked = TrackedRequest(
            user_id=user_id,
            provider=provider,
            model=model,
            request_type=request_type,
            usage=response.usage,
            duration_ms=duration_ms,
            cost_usd=cost,
            strategy=strategy,
            fallback_used=fallback_used,
            cache_hit=cache_hit,
            request_id=request_id,
        )

        # TODO: Persist to database asynchronously
        return tracked

    def track_error(
        self,
        request: Request,
        provider: str,
        model: str,
        error_type: str,
        duration_ms: float | None = None,
    ) -> TrackedRequest:
        """Track a failed request."""
        user_id = getattr(request.state, "user_id", "anonymous")
        request_id = getattr(request.state, "request_id", None)

        return TrackedRequest(
            user_id=user_id,
            provider=provider,
            model=model,
            request_type="chat",
            usage=Usage(),
            duration_ms=duration_ms,
            cost_usd=0.0,
            status_code=500,
            error_type=error_type,
            request_id=request_id,
        )
