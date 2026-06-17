"""Background workers for async job processing."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from app.config import settings
from app.core.logging import configure_logging
from app.providers.registry import get_registry
from app.queue.redis_streams import JobQueue


class Worker:
    """Async worker that processes jobs from Redis Streams."""

    def __init__(
        self,
        name: str,
        queue: JobQueue | None = None,
        poll_interval: float = 1.0,
    ) -> None:
        self.name = name
        self.queue = queue or JobQueue()
        self.poll_interval = poll_interval
        self._running = False

    async def start(self) -> None:
        """Start the worker loop."""
        configure_logging(settings.gateway_env)
        self._running = True
        await self.queue.ensure_group()

        while self._running:
            try:
                jobs = await self.queue.read(
                    consumer_name=self.name,
                    count=10,
                    block_ms=5000,
                )
                if not jobs:
                    continue

                for job in jobs:
                    await self._process_job(job)
            except Exception as exc:
                # Log and continue — don't crash the worker
                import structlog

                logger = structlog.get_logger()
                logger.error("worker_error", error=str(exc), worker=self.name)
                await asyncio.sleep(self.poll_interval)

    async def stop(self) -> None:
        """Signal the worker to stop."""
        self._running = False

    async def _process_job(self, job: dict[str, Any]) -> None:
        job_type = job.get("job_type", "unknown")
        payload = json.loads(job.get("payload", "{}"))

        try:
            if job_type == "chat_completion_retry":
                await self._handle_chat_completion_retry(payload)
            elif job_type == "shadow_traffic":
                await self._handle_shadow_traffic(payload)
            else:
                raise ValueError(f"Unknown job type: {job_type}")

            await self.queue.ack(job["id"])
        except Exception as exc:
            await self.queue.retry_or_dlq(job["id"], job, str(exc))

    async def _handle_chat_completion_retry(self, payload: dict[str, Any]) -> None:
        """Retry a failed chat completion request."""
        from app.core.models import ChatCompletionRequest, ChatMessage
        from app.router.engine import SmartRouter

        registry = get_registry()
        router = SmartRouter(registry)

        request = ChatCompletionRequest(
            model=payload["model"],
            messages=[ChatMessage(**m) for m in payload["messages"]],
            temperature=payload.get("temperature"),
            max_tokens=payload.get("max_tokens"),
        )
        await router.route_chat_completion(request)

    async def _handle_shadow_traffic(self, payload: dict[str, Any]) -> None:
        """Send shadow traffic to a provider without returning results."""
        from app.core.models import ChatCompletionRequest, ChatMessage

        registry = get_registry()
        provider = registry.get(payload.get("provider", "ollama"))
        if not provider:
            return

        request = ChatCompletionRequest(
            model=payload["model"],
            messages=[ChatMessage(**m) for m in payload["messages"]],
            temperature=payload.get("temperature"),
            max_tokens=payload.get("max_tokens"),
        )
        await provider.chat_completion(request)
