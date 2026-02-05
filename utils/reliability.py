"""Reliability utilities: retry + circuit breaker.

These utilities are intentionally minimal and dependency-free.
They are designed for async trading automation workloads.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 5
    base_delay: float = 0.2
    max_delay: float = 5.0
    exponential_base: float = 2.0
    jitter: float = 0.1


async def retry_async(
    func: Callable[[], Awaitable[T]],
    *,
    policy: RetryPolicy = RetryPolicy(),
    is_retriable: Optional[Callable[[Exception], bool]] = None,
    on_retry: Optional[Callable[[int, Exception, float], None]] = None,
) -> T:
    """Retry an async function with exponential backoff + jitter."""

    attempt = 0
    while True:
        try:
            return await func()
        except Exception as exc:
            attempt += 1
            if is_retriable is not None and not is_retriable(exc):
                raise
            if policy.max_attempts > 0 and attempt >= policy.max_attempts:
                raise

            delay = min(policy.max_delay, policy.base_delay * (policy.exponential_base ** (attempt - 1)))
            if policy.jitter:
                delay = max(0.0, delay + random.uniform(-delay * policy.jitter, delay * policy.jitter))

            if on_retry:
                try:
                    on_retry(attempt, exc, delay)
                except Exception:
                    pass
            logger.warning(f"Retrying after error (attempt {attempt}): {exc}. sleeping {delay:.2f}s")
            await asyncio.sleep(delay)


@dataclass
class CircuitBreaker:
    """Simple circuit breaker.

    Opens after `failure_threshold` failures in a rolling time window.
    """

    failure_threshold: int = 5
    window_seconds: float = 30.0
    cooldown_seconds: float = 10.0

    _failures: list[float] = None  # monotonic timestamps
    _opened_at: Optional[float] = None

    def __post_init__(self):
        if self._failures is None:
            self._failures = []

    def is_open(self) -> bool:
        if self._opened_at is None:
            return False
        if (time.monotonic() - self._opened_at) >= self.cooldown_seconds:
            # allow half-open trial
            self._opened_at = None
            self._failures.clear()
            return False
        return True

    def record_success(self) -> None:
        # on success, we can slowly forget failures
        self._trim()

    def record_failure(self) -> None:
        now = time.monotonic()
        self._failures.append(now)
        self._trim(now)
        if len(self._failures) >= self.failure_threshold:
            self._opened_at = now

    def _trim(self, now: Optional[float] = None) -> None:
        if now is None:
            now = time.monotonic()
        cutoff = now - self.window_seconds
        # keep only recent failures
        self._failures[:] = [t for t in self._failures if t >= cutoff]
