"""Async job queue using Redis Streams."""

from __future__ import annotations

import json
import time
from typing import Any

import redis.asyncio as redis

from app.config import settings


class JobQueue:
    """Redis Streams-based job queue."""

    STREAM_KEY = "gateway:queue:jobs"
    DLQ_KEY = "gateway:queue:dead_letter"
    CONSUMER_GROUP = "gateway-workers"

    def __init__(self, redis_client: redis.Redis | None = None) -> None:
        self._redis = redis_client or redis.from_url(settings.redis_url)

    async def ensure_group(self) -> None:
        """Create consumer group if it doesn't exist."""
        try:
            await self._redis.xgroup_create(
                self.STREAM_KEY, self.CONSUMER_GROUP, id="0", mkstream=True
            )
        except redis.ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    async def enqueue(
        self,
        job_type: str,
        payload: dict[str, Any],
        max_retries: int = 3,
    ) -> str:
        """Add a job to the queue. Returns job ID."""
        job_id = f"{job_type}:{int(time.time() * 1000)}"
        message = {
            "job_id": job_id,
            "job_type": job_type,
            "payload": json.dumps(payload),
            "retries": 0,
            "max_retries": max_retries,
            "created_at": time.time(),
        }
        await self._redis.xadd(self.STREAM_KEY, message)
        return job_id

    async def claim_pending(
        self,
        consumer_name: str,
        count: int = 10,
        idle_time_ms: int = 60000,
    ) -> list[dict[str, Any]]:
        """Claim pending messages from idle consumers."""
        pending = await self._redis.xpending_range(
            self.STREAM_KEY,
            self.CONSUMER_GROUP,
            min="-",
            max="+",
            count=count,
        )
        if not pending:
            return []

        message_ids = [p["message_id"] for p in pending if p["time_since_delivered"] > idle_time_ms]
        if not message_ids:
            return []

        claimed = await self._redis.xclaim(
            self.STREAM_KEY,
            self.CONSUMER_GROUP,
            consumer_name,
            min_idle_time=idle_time_ms,
            message_ids=message_ids,
        )
        return self._decode_messages(claimed)

    async def read(
        self,
        consumer_name: str,
        count: int = 10,
        block_ms: int = 5000,
    ) -> list[dict[str, Any]]:
        """Read jobs from the stream."""
        await self.ensure_group()
        messages = await self._redis.xreadgroup(
            groupname=self.CONSUMER_GROUP,
            consumername=consumer_name,
            streams={self.STREAM_KEY: ">"},
            count=count,
            block=block_ms,
        )
        return self._decode_messages(messages)

    async def ack(self, message_id: str) -> None:
        """Acknowledge a completed job."""
        await self._redis.xack(self.STREAM_KEY, self.CONSUMER_GROUP, message_id)

    async def retry_or_dlq(
        self,
        message_id: str,
        job: dict[str, Any],
        error: str,
    ) -> None:
        """Retry a job or move it to the dead letter queue."""
        retries = int(job.get("retries", 0)) + 1
        max_retries = int(job.get("max_retries", 3))

        if retries >= max_retries:
            await self._redis.xadd(
                self.DLQ_KEY,
                {
                    "original_id": message_id,
                    "error": error,
                    "payload": job.get("payload", ""),
                    "failed_at": time.time(),
                },
            )
            await self.ack(message_id)
        else:
            # Re-queue with incremented retry count
            await self._redis.xadd(
                self.STREAM_KEY,
                {
                    **{k: v for k, v in job.items() if k != "id"},
                    "retries": retries,
                },
            )
            await self.ack(message_id)

    def _decode_messages(self, raw: list) -> list[dict[str, Any]]:
        """Decode Redis stream messages."""
        results = []
        for item in raw:
            if isinstance(item, tuple) and len(item) == 2:
                # xreadgroup format: (stream_name, [(msg_id, fields), ...])
                for msg_id, fields in item[1]:
                    results.append(self._decode_one(msg_id, fields))
            elif isinstance(item, tuple) and len(item) == 2:
                # xclaim format
                msg_id, fields = item
                results.append(self._decode_one(msg_id, fields))
        return results

    def _decode_one(self, msg_id: bytes | str, fields: dict) -> dict[str, Any]:
        decoded: dict[str, Any] = {"id": msg_id.decode() if isinstance(msg_id, bytes) else msg_id}
        for k, v in fields.items():
            key = k.decode() if isinstance(k, bytes) else k
            val = v.decode() if isinstance(v, bytes) else v
            decoded[key] = val
        return decoded
