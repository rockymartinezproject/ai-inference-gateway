"""Semantic caching layer using Redis and embeddings."""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

import redis.asyncio as redis

from app.cache.backends import EmbeddingBackend, ExactMatchBackend
from app.config import settings


class SemanticCache:
    """Cache for LLM responses based on query semantic similarity."""

    def __init__(
        self,
        redis_client: redis.Redis | None = None,
        backend: EmbeddingBackend | None = None,
        threshold: float | None = None,
        ttl_seconds: int | None = None,
    ) -> None:
        self._redis = redis_client or redis.from_url(settings.redis_url)
        self._backend = backend or ExactMatchBackend()
        self._threshold = threshold if threshold is not None else settings.semantic_cache_threshold
        self._ttl = ttl_seconds if ttl_seconds is not None else settings.cache_ttl_seconds
        self._hits = 0
        self._misses = 0

    def _cache_key(self, embedding: list[float]) -> str:
        """Create a deterministic cache key from embedding."""
        embedding_bytes = json.dumps(embedding, sort_keys=True).encode()
        return f"gateway:cache:{hashlib.sha256(embedding_bytes).hexdigest()[:16]}"

    def _index_key(self, model: str) -> str:
        return f"gateway:cache:index:{model}"

    async def lookup(self, query: str, model: str) -> dict[str, Any] | None:
        """Look up a cached response for a semantically similar query."""
        embedding = self._backend.embed(query)
        cache_key = self._cache_key(embedding)

        # Try exact key first
        raw = await self._redis.get(cache_key)
        if raw:
            self._hits += 1
            return json.loads(raw)

        # Try similarity search against indexed embeddings
        index_key = self._index_key(model)
        candidates = await self._redis.zrange(index_key, 0, -1, withscores=False)

        best_score = 0.0
        best_key = None
        for candidate_json in candidates:
            candidate = json.loads(candidate_json)
            score = self._backend.similarity(embedding, candidate["embedding"])
            if score > best_score:
                best_score = score
                best_key = candidate["key"]

        if best_key and best_score >= self._threshold:
            raw = await self._redis.get(best_key)
            if raw:
                self._hits += 1
                return json.loads(raw)

        self._misses += 1
        return None

    async def store(
        self, query: str, model: str, response: dict[str, Any]
    ) -> None:
        """Store a response in the semantic cache."""
        embedding = self._backend.embed(query)
        cache_key = self._cache_key(embedding)
        payload = {
            "response": response,
            "model": model,
            "created_at": time.time(),
        }
        await self._redis.setex(cache_key, self._ttl, json.dumps(payload))

        # Index embedding for similarity search
        index_key = self._index_key(model)
        index_entry = json.dumps({"key": cache_key, "embedding": embedding})
        await self._redis.zadd(index_key, {index_entry: time.time()})
        await self._redis.expire(index_key, self._ttl)

    async def invalidate(self, model: str | None = None) -> int:
        """Invalidate cache entries. Returns number removed."""
        if model:
            index_key = self._index_key(model)
            keys = await self._redis.zrange(index_key, 0, -1)
            count = 0
            for entry_json in keys:
                entry = json.loads(entry_json)
                await self._redis.delete(entry["key"])
                count += 1
            await self._redis.delete(index_key)
            return count
        else:
            pattern = "gateway:cache:*"
            keys = []
            async for key in self._redis.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                await self._redis.delete(*keys)
            return len(keys)

    @property
    def stats(self) -> dict[str, int]:
        return {"hits": self._hits, "misses": self._misses}
