"""Tests for circuit breaker."""

from __future__ import annotations

import time

from app.circuitbreaker.breaker import CircuitBreaker, CircuitState


def test_circuit_starts_closed() -> None:
    cb = CircuitBreaker("test")
    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute() is True


def test_circuit_opens_after_failures() -> None:
    cb = CircuitBreaker("test", failure_threshold=3)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.can_execute() is False


def test_circuit_half_open_after_timeout() -> None:
    cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=0.1)
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    time.sleep(0.15)
    assert cb.state == CircuitState.HALF_OPEN
    assert cb.can_execute() is True


def test_circuit_closes_after_half_open_success() -> None:
    cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=0.1, half_open_max_calls=2)
    cb.record_failure()
    time.sleep(0.15)
    assert cb.state == CircuitState.HALF_OPEN
    cb.record_success()
    cb.record_success()
    assert cb.state == CircuitState.CLOSED


def test_circuit_reopens_on_half_open_failure() -> None:
    cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=0.1, half_open_max_calls=2)
    cb.record_failure()
    time.sleep(0.15)
    assert cb.state == CircuitState.HALF_OPEN
    cb.record_failure()
    assert cb.state == CircuitState.OPEN


def test_registry() -> None:
    from app.circuitbreaker.breaker import CircuitBreakerRegistry

    reg = CircuitBreakerRegistry()
    cb = reg.get("openai")
    assert cb.name == "openai"
    assert reg.health() == {"openai": "closed"}
