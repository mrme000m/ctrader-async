"""Stream resubscription registry.

Used by CTraderClient to resubscribe long-lived streams (e.g. tick streams)
after reconnect.

Design:
- Streams register themselves on `__aenter__` and unregister on `__aexit__`.
- The registry calls `await stream.resubscribe(protocol, symbols)` after reconnect.

This is best-effort: failures in one stream should not prevent others.
"""

from __future__ import annotations

import asyncio
import logging
import weakref
from typing import Protocol, Any

logger = logging.getLogger(__name__)


class ResubscribableStream(Protocol):
    async def resubscribe(self, protocol: Any, symbols: Any) -> None: ...


class StreamRegistry:
    def __init__(self) -> None:
        self._streams: "weakref.WeakSet[ResubscribableStream]" = weakref.WeakSet()

    def register(self, stream: ResubscribableStream) -> None:
        self._streams.add(stream)

    def unregister(self, stream: ResubscribableStream) -> None:
        try:
            self._streams.remove(stream)
        except KeyError:
            pass

    async def resubscribe_all(self, *, protocol: Any, symbols: Any) -> None:
        streams = list(self._streams)
        if not streams:
            return

        async def _safe(s: ResubscribableStream) -> None:
            try:
                await s.resubscribe(protocol, symbols)
            except Exception as e:
                logger.warning(f"Failed to resubscribe stream {s!r}: {e}")

        await asyncio.gather(*[_safe(s) for s in streams])
