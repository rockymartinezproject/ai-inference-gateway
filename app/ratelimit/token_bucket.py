"""Token bucket rate limiting with Redis."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import redis.asyncio as redis

from app.config import settings
from app.core.errors import RateLimitExceeded

if TYPE_CHECKING:
    from fastapi import Request


class TokenBucket:
    """Redis-backed token bucket for rate limiting."""

    def __init__(
        self,
        redis_client: redis.Redis | None = None,
        requests_per_minute: int | None = None,
        tokens_per_minute: int | None = None,
    ) -> None:
        self._redis = redis_client or redis.from_url(settings.redis_url)
        self._rpm = requests_per_minute or settings.rate_limit_requests_per_minute
        self._tpm = tokens_per_minute or settings.rate_limit_tokens_per_minute

    def _bucket_key(self, identifier: str, bucket_type: str) -> str:
        return f"gateway:ratelimit:{bucket_type}:{identifier}"

    async def check(
        self,
        request: Request,
        requested_tokens: int = 1,
    ) -> None:
        """Check if request is within rate limits. Raises RateLimitExceeded if not."""
        user_id = getattr(request.state, "user_id", "anonymous")

        # Per-user request bucket
        await self._consume_bucket(
            bucket_key=self._bucket_key(user_id, "requests"),
            capacity=self._rpm,
            refill_rate=self._rpm / 60.0,
            requested=1,
            window=60,
        )

        # Per-user token bucket
        await self._consume_bucket(
            bucket_key=self._bucket_key(user_id, "tokens"),
            capacity=self._tpm,
            refill_rate=self._tpm / 60.0,
            requested=requested_tokens,
            window=60,
        )

    async def _consume_bucket(
        self,
        bucket_key: str,
        capacity: float,
        refill_rate: float,
        requested: float,
        window: int,
    ) -> None:
        """Atomically consume tokens from a bucket using Redis."""
        now = time.time()
        pipe = self._redis.pipeline()
        pipe.hmget(bucket_key, ["tokens", "last_update"])
        result = await pipe.execute()

        tokens_str, last_update_str = result[0]
        tokens = float(tokens_str) if tokens_str else capacity
        last_update = float(last_update_str) if last_update_str else now

        # Refill tokens based on elapsed time
        elapsed = now - last_update
        tokens = min(capacity, tokens + elapsed * refill_rate)

        if tokens < requested:
            retry_after = int((requested - tokens) / refill_rate) + 1
            raise RateLimitExceeded(f"Rate limit exceeded. Retry after {retry_after}s")

        tokens -= requested
        await self._redis.hset(
            bucket_key,
            mapping={
                "tokens": tokens,
                "last_update": now,
            },
        )
        await self._redis.expire(bucket_key, window)
