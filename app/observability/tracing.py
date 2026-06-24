"""OpenTelemetry tracing setup."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from app.config import settings


class NoopTracer:
    """Fallback tracer when OpenTelemetry is not configured."""

    @asynccontextmanager
    async def start_span(self, name: str, attributes: dict | None = None) -> AsyncIterator[None]:
        yield

    def add_event(self, name: str, attributes: dict | None = None) -> None:
        pass


def get_tracer():
    """Get a tracer — noop if OTel is not configured."""
    if not settings.otel_exporter_endpoint:
        return NoopTracer()

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource(attributes={SERVICE_NAME: "ai-inference-gateway"})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        return trace.get_tracer("ai-inference-gateway")
    except ImportError:
        return NoopTracer()


tracer = get_tracer()
