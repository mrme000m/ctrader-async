"""Lightweight performance metrics for ctc.

Design goals:
- dependency-free
- safe in production (never raises from hooks)
- works without integration tests / server connectivity

Metrics are collected via:
- HookManager hook points (`protocol.post_send_request`, `protocol.post_response`)
- EventBus topics emitted by protocol/streams for drop/backpressure signals

This module intentionally provides a *snapshot* style API (pull) rather than
requiring Prometheus/etc.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MetricsSnapshot:
    requests_sent: int = 0
    responses_received: int = 0
    request_timeouts: int = 0
    request_errors: int = 0
    bytes_sent: int = 0

    # latency stats (seconds)
    latency_count: int = 0
    latency_sum: float = 0.0
    latency_min: float | None = None
    latency_max: float | None = None

    # backpressure / drops
    inbound_dropped: int = 0
    tick_dropped: int = 0

    # reconnect
    reconnect_attempts: int = 0
    reconnect_successes: int = 0


@dataclass
class MetricsCollector:
    """Collects metrics from hooks/events.

    Intended usage:
        collector = MetricsCollector()
        collector.attach(client)
        ...
        snap = collector.snapshot()
    """

    _started_at: float = field(default_factory=time.time)
    _inflight: dict[str, float] = field(default_factory=dict)  # msg_id -> perf_counter start

    _requests_sent: int = 0
    _responses_received: int = 0
    _request_timeouts: int = 0
    _request_errors: int = 0
    _bytes_sent: int = 0

    _latency_count: int = 0
    _latency_sum: float = 0.0
    _latency_min: float | None = None
    _latency_max: float | None = None

    _inbound_dropped: int = 0
    _tick_dropped: int = 0

    _reconnect_attempts: int = 0
    _reconnect_successes: int = 0

    def snapshot(self) -> MetricsSnapshot:
        return MetricsSnapshot(
            requests_sent=self._requests_sent,
            responses_received=self._responses_received,
            request_timeouts=self._request_timeouts,
            request_errors=self._request_errors,
            bytes_sent=self._bytes_sent,
            latency_count=self._latency_count,
            latency_sum=self._latency_sum,
            latency_min=self._latency_min,
            latency_max=self._latency_max,
            inbound_dropped=self._inbound_dropped,
            tick_dropped=self._tick_dropped,
            reconnect_attempts=self._reconnect_attempts,
            reconnect_successes=self._reconnect_successes,
        )

    # Maximum age (seconds) for an inflight entry before it is evicted.
    # This matches the default request_timeout so stale entries from timed-out
    # requests are cleaned up automatically without requiring a separate task.
    _INFLIGHT_MAX_AGE: float = 35.0

    # ---- hook handlers ----
    async def on_post_send_request(self, ctx) -> None:
        try:
            msg_id = str(ctx.data.get("client_msg_id") or "")
            if msg_id:
                self._inflight[msg_id] = time.perf_counter()
            self._requests_sent += 1
            self._bytes_sent += int(ctx.data.get("bytes_sent") or 0)
            # Opportunistically trim stale inflight entries on every send
            self._trim_inflight()
        except Exception:
            return

    async def on_post_response(self, ctx) -> None:
        try:
            self._responses_received += 1
            msg_id = str(ctx.data.get("client_msg_id") or "")
            if msg_id and msg_id in self._inflight:
                dt = time.perf_counter() - self._inflight.pop(msg_id)
                self._latency_count += 1
                self._latency_sum += dt
                self._latency_min = dt if self._latency_min is None else min(self._latency_min, dt)
                self._latency_max = dt if self._latency_max is None else max(self._latency_max, dt)
        except Exception:
            return

    def _trim_inflight(self) -> None:
        """Remove inflight entries older than _INFLIGHT_MAX_AGE seconds.

        Called opportunistically on each send so no background task is needed.
        """
        now = time.perf_counter()
        cutoff = now - self._INFLIGHT_MAX_AGE
        stale = [mid for mid, t in self._inflight.items() if t < cutoff]
        for mid in stale:
            self._inflight.pop(mid, None)
        if stale:
            self._request_timeouts += len(stale)

    # ---- event handlers ----
    async def on_inbound_dropped(self, _evt: Any) -> None:
        self._inbound_dropped += 1

    async def on_tick_dropped(self, _evt: Any) -> None:
        self._tick_dropped += 1

    async def on_reconnect_attempt(self, _evt: Any) -> None:
        self._reconnect_attempts += 1

    async def on_reconnect_success(self, _evt: Any) -> None:
        self._reconnect_successes += 1
