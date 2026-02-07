from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Dict, Optional

from ..models import Tick


@dataclass
class TickStore:
    """In-memory last-tick store.

    Used for best-effort conversions (e.g., asset conversion rates).
    """

    _ticks: Dict[str, Tick]
    _lock: asyncio.Lock

    def __init__(self):
        self._ticks = {}
        self._lock = asyncio.Lock()

    async def set(self, tick: Tick) -> None:
        async with self._lock:
            self._ticks[tick.symbol_name.upper()] = tick

    async def get(self, symbol_name: str) -> Optional[Tick]:
        async with self._lock:
            return self._ticks.get(symbol_name.upper())

    async def mid(self, symbol_name: str) -> Optional[float]:
        t = await self.get(symbol_name)
        if t is None:
            return None
        bid = float(t.bid)
        ask = float(t.ask)
        if bid > 0 and ask > 0:
            return (bid + ask) / 2.0
        if ask > 0:
            return ask
        if bid > 0:
            return bid
        return None
