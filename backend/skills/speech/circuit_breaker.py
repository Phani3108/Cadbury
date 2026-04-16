"""Minimal circuit breaker for external service calls.

Pattern borrowed from Rose: 5 consecutive failures → open for 60s. While open,
all calls fast-fail with CircuitOpenError so we don't pile up latency on a
known-bad dependency.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field


class CircuitOpenError(Exception):
    """Raised when a circuit is open and a call is rejected pre-flight."""


@dataclass
class _State:
    failures: int = 0
    opened_at: float = 0.0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class CircuitBreaker:
    """One instance per downstream service."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        reset_seconds: float = 60.0,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_seconds = reset_seconds
        self._state = _State()

    def is_open(self) -> bool:
        s = self._state
        if s.failures < self.failure_threshold:
            return False
        if time.monotonic() - s.opened_at >= self.reset_seconds:
            # Half-open: allow the next call through.
            s.failures = self.failure_threshold - 1
            s.opened_at = 0.0
            return False
        return True

    def record_success(self) -> None:
        self._state.failures = 0
        self._state.opened_at = 0.0

    def record_failure(self) -> None:
        s = self._state
        s.failures += 1
        if s.failures >= self.failure_threshold and s.opened_at == 0.0:
            s.opened_at = time.monotonic()

    async def call(self, coro):
        if self.is_open():
            raise CircuitOpenError(f"Circuit '{self.name}' is open")
        try:
            result = await coro
        except Exception:
            self.record_failure()
            raise
        self.record_success()
        return result
