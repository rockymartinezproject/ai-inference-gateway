"""Prometheus metrics instrumentation."""

from __future__ import annotations

from prometheus_client import Counter, Histogram, Info, generate_latest

# Gateway info
GATEWAY_INFO = Info("gateway", "AI Inference Gateway metadata")

# Request counters
REQUESTS_TOTAL = Counter(
    "gateway_requests_total",
    "Total requests by provider, model, and status",
    ["provider", "model", "status"],
)

REQUESTS_STREAMING_TOTAL = Counter(
    "gateway_requests_streaming_total",
    "Total streaming requests by provider and model",
    ["provider", "model"],
)

TOKENS_TOTAL = Counter(
    "gateway_tokens_total",
    "Total tokens by provider, model, and type",
    ["provider", "model", "type"],
)

COST_TOTAL = Counter(
    "gateway_cost_usd_total",
    "Total cost in USD by provider and model",
    ["provider", "model"],
)

CACHE_HITS_TOTAL = Counter(
    "gateway_cache_hits_total",
    "Total cache hits",
    ["cache_type"],
)

CACHE_MISSES_TOTAL = Counter(
    "gateway_cache_misses_total",
    "Total cache misses",
    ["cache_type"],
)

# Latency histograms
REQUEST_DURATION = Histogram(
    "gateway_request_duration_seconds",
    "Request duration in seconds",
    ["provider", "model"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

PROVIDER_HEALTH = Counter(
    "gateway_provider_health_checks_total",
    "Provider health check results",
    ["provider", "status"],
)

FALLBACK_TOTAL = Counter(
    "gateway_fallback_total",
    "Total fallback attempts by provider",
    ["from_provider", "to_provider"],
)


def metrics_response() -> bytes:
    """Generate Prometheus exposition format response."""
    return generate_latest()


def record_request(
    provider: str,
    model: str,
    status_code: int,
    duration_s: float,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    cost_usd: float = 0.0,
) -> None:
    """Record metrics for a completed request."""
    status = str(status_code)
    REQUESTS_TOTAL.labels(provider=provider, model=model, status=status).inc()
    REQUEST_DURATION.labels(provider=provider, model=model).observe(duration_s)
    if prompt_tokens:
        TOKENS_TOTAL.labels(provider=provider, model=model, type="prompt").inc(prompt_tokens)
    if completion_tokens:
        TOKENS_TOTAL.labels(provider=provider, model=model, type="completion").inc(
            completion_tokens
        )
    if cost_usd:
        COST_TOTAL.labels(provider=provider, model=model).inc(cost_usd)


def record_fallback(from_provider: str, to_provider: str) -> None:
    """Record a fallback event."""
    FALLBACK_TOTAL.labels(from_provider=from_provider, to_provider=to_provider).inc()


def record_cache_hit(cache_type: str = "semantic") -> None:
    CACHE_HITS_TOTAL.labels(cache_type=cache_type).inc()


def record_cache_miss(cache_type: str = "semantic") -> None:
    CACHE_MISSES_TOTAL.labels(cache_type=cache_type).inc()
