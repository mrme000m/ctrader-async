from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Iterable, Optional

from ..models import Tick
from ..utils.tick_store import TickStore

logger = logging.getLogger(__name__)


@dataclass
class ConversionSubscriptionManager:
    """Keeps tick subscriptions alive for a set of symbols.

    This is intended for enabling deposit_notional conversions that depend on
    a few FX symbols (e.g., EURUSD, USDJPY).

    It starts background tasks that consume ticks (and therefore keep streams alive)
    and stores last ticks into the client's TickStore.
    """

    market_data: any
    tick_store: TickStore

    _tasks: dict[str, asyncio.Task]

    def __init__(self, *, market_data: any, tick_store: TickStore):
        self.market_data = market_data
        self.tick_store = tick_store
        self._tasks = {}

    def ensure(self, symbols: Iterable[str]) -> None:
        for s in symbols:
            sym = str(s).upper()
            if sym in self._tasks and not self._tasks[sym].done():
                continue
            self._tasks[sym] = asyncio.create_task(self._run(sym))

    async def stop(self) -> None:
        for t in list(self._tasks.values()):
            if not t.done():
                t.cancel()
        for t in list(self._tasks.values()):
            try:
                await t
            except Exception:
                pass
        self._tasks.clear()

    async def _run(self, symbol: str) -> None:
        try:
            async with self.market_data.stream_ticks(symbol) as stream:
                async for tick in stream:
                    try:
                        await self.tick_store.set(tick)
                    except Exception:
                        pass
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.warning("conversion_tick_stream_failed symbol=%s err=%s", symbol, e)
