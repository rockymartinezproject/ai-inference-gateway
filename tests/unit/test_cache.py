"""Tests for semantic caching."""

from __future__ import annotations

import sys

import pytest

from app.cache.backends import ExactMatchBackend, SentenceTransformerBackend
from app.cache.semantic import SemanticCache


class FakeRedis:
    """In-memory fake Redis for testing."""

    def __init__(self) -> None:
        self._data: dict[str, str] = {}
        self._zsets: dict[str, list[tuple[float, str]]] = {}

    async def get(self, key: str) -> str | None:
        return self._data.get(key)

    async def setex(self, key: str, ttl: int, value: str) -> None:
        self._data[key] = value

    async def zadd(self, key: str, mapping: dict[str, float]) -> None:
        if key not in self._zsets:
            self._zsets[key] = []
        for member, score in mapping.items():
            self._zsets[key].append((score, member))

    async def zrange(self, key: str, start: int, end: int, withscores: bool = False) -> list:
        items = self._zsets.get(key, [])
        return [m for _, m in items]

    async def expire(self, key: str, ttl: int) -> None:
        pass

    async def delete(self, *keys: str) -> None:
        for k in keys:
            self._data.pop(k, None)
            self._zsets.pop(k, None)

    async def hset(self, key: str, mapping: dict) -> None:
        pass

    async def hmget(self, key: str, fields: list[str]) -> list:
        return [None, None]

    def scan_iter(self, match: str):
        return iter([])


@pytest.fixture
def fake_redis():
    return FakeRedis()


def test_exact_match_backend() -> None:
    backend = ExactMatchBackend()
    a = backend.embed("hello")
    b = backend.embed("hello")
    c = backend.embed("world")
    assert backend.similarity(a, b) == 1.0
    assert backend.similarity(a, c) == 0.0


def test_sentence_transformer_backend_missing_dep(monkeypatch) -> None:
    # Simulate the optional dependency being unavailable.
    monkeypatch.setitem(sys.modules, "sentence_transformers", None)
    with pytest.raises(ImportError):
        SentenceTransformerBackend()


@pytest.mark.anyio
async def test_cache_store_and_lookup(fake_redis) -> None:
    cache = SemanticCache(redis_client=fake_redis, backend=ExactMatchBackend(), threshold=1.0)
    await cache.store("What is AI?", "gpt-4", {"answer": "AI is..."})
    result = await cache.lookup("What is AI?", "gpt-4")
    assert result is not None
    assert result["response"]["answer"] == "AI is..."


@pytest.mark.anyio
async def test_cache_miss(fake_redis) -> None:
    cache = SemanticCache(redis_client=fake_redis, backend=ExactMatchBackend(), threshold=1.0)
    result = await cache.lookup("unseen query", "gpt-4")
    assert result is None


@pytest.mark.anyio
async def test_cache_stats(fake_redis) -> None:
    cache = SemanticCache(redis_client=fake_redis, backend=ExactMatchBackend(), threshold=1.0)
    await cache.store("q1", "m1", {"r": 1})
    await cache.lookup("q1", "m1")
    await cache.lookup("q2", "m1")
    assert cache.stats["hits"] == 1
    assert cache.stats["misses"] == 1
