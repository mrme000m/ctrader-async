"""Multi-symbol real-time tick streaming with batched subscribe/unsubscribe.

This is designed for bot/agent workloads where many symbols are streamed
concurrently.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Iterable

from ..models import Tick
from ..transport import ProtocolFraming

if TYPE_CHECKING:
    from ..protocol import ProtocolHandler
    from ..config import ClientConfig
    from ..api.symbols import SymbolCatalog

logger = logging.getLogger(__name__)


class MultiTickStream:
    """Async iterator yielding ticks for multiple symbols.

    Features:
    - Batched subscribe/unsubscribe requests.
    - Bounded queue to prevent unbounded memory growth.
    - Optional per-symbol coalescing: keep only latest tick per symbol when under load.

    Yields:
        Tick objects (symbol_name populated when possible)
    """

    def __init__(
        self,
        protocol: ProtocolHandler,
        config: ClientConfig,
        symbols: SymbolCatalog,
        symbol_names: Iterable[str],
        *,
        coalesce_latest: bool = True,
    ):
        self.protocol = protocol
        self.config = config
        self.symbols = symbols
        self.symbol_names = [s for s in symbol_names]
        self.coalesce_latest = coalesce_latest

        maxsize = getattr(config, "tick_queue_size", 1000)
        self._queue: asyncio.Queue[Tick] = asyncio.Queue(maxsize=maxsize)
        self._subscribed = False

        self._symbol_ids: dict[int, str] = {}
        self._latest_by_symbol: dict[int, Tick] = {}
        self._flush_task: asyncio.Task | None = None
        self._flush_event = asyncio.Event()

    async def __aenter__(self):
        await self._subscribe()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._unsubscribe()

    def __aiter__(self):
        return self

    async def __anext__(self) -> Tick:
        if not self._subscribed:
            raise StopAsyncIteration
        return await self._queue.get()

    def fanout_by_symbol(self, *, maxsize: int = 1000, drop_oldest: bool = True):
        """Create a per-symbol fanout helper for this stream.

        Example:
            async with client.market_data.stream_ticks_multi(["EURUSD", "GBPUSD"]) as s:
                f = s.fanout_by_symbol()
                await f.start()
                eur_q = f.queue("EURUSD")
                tick = await eur_q.get()
        """
        from .fanout import Fanout

        return Fanout(self, key=lambda t: (t.symbol_name or str(t.symbol_id)).upper(), maxsize=maxsize, drop_oldest=drop_oldest)

    async def _subscribe(self) -> None:
        from ..messages.OpenApiMessages_pb2 import ProtoOASubscribeSpotsReq, ProtoOASpotEvent

        # Resolve ids for all symbols
        for name in self.symbol_names:
            info = await self.symbols.get_symbol(name)
            if not info:
                raise ValueError(f"Symbol not found: {name}")
            self._symbol_ids[int(info.id)] = info.name

        # Register one handler for all spot events
        self.protocol.dispatcher.register(ProtoOASpotEvent().payloadType, self._on_spot)

        req = ProtoOASubscribeSpotsReq()
        req.ctidTraderAccountId = self.config.account_id
        req.symbolId.extend(list(self._symbol_ids.keys()))

        await self.protocol.send_request(req, timeout=10.0, request_type="SubscribeSpots")

        self._subscribed = True
        if self.coalesce_latest:
            self._flush_task = asyncio.create_task(self._flush_loop())

        logger.info(f"Subscribed to {len(self._symbol_ids)} symbols ticks")

    async def _unsubscribe(self) -> None:
        if not self._subscribed:
            return

        from ..messages.OpenApiMessages_pb2 import ProtoOAUnsubscribeSpotsReq, ProtoOASpotEvent

        # Unregister handler
        self.protocol.dispatcher.unregister(ProtoOASpotEvent().payloadType, self._on_spot)

        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        self._flush_task = None

        req = ProtoOAUnsubscribeSpotsReq()
        req.ctidTraderAccountId = self.config.account_id
        req.symbolId.extend(list(self._symbol_ids.keys()))

        try:
            await self.protocol.send_request(req, timeout=10.0, request_type="UnsubscribeSpots")
        finally:
            self._subscribed = False
            self._symbol_ids.clear()
            self._latest_by_symbol.clear()

        logger.info("Unsubscribed multi tick stream")

    async def _on_spot(self, envelope) -> None:
        payload = ProtocolFraming.extract_payload(envelope)
        sid = int(getattr(payload, "symbolId", 0))
        if sid not in self._symbol_ids:
            return

        tick = Tick(
            symbol_id=sid,
            symbol_name=self._symbol_ids.get(sid, str(sid)),
            bid=getattr(payload, "bid", 0) / 100000.0,
            ask=getattr(payload, "ask", 0) / 100000.0,
            timestamp=getattr(payload, "timestamp", 0),
        )

        if not self.coalesce_latest:
            self._put_tick_drop_oldest(tick)
            return

        # coalescing mode
        self._latest_by_symbol[sid] = tick
        self._flush_event.set()

    def _put_tick_drop_oldest(self, tick: Tick) -> None:
        try:
            self._queue.put_nowait(tick)
        except asyncio.QueueFull:
            try:
                _ = self._queue.get_nowait()
                self._queue.task_done()
            except asyncio.QueueEmpty:
                pass

            # Best-effort metrics/event emission (do not block tick handler)
            try:
                asyncio.create_task(
                    self.protocol.events.emit(
                        "stream.tick_dropped",
                        {"stream": "MultiTickStream", "reason": "queue_full"},
                    )
                )
            except Exception:
                pass

            try:
                self._queue.put_nowait(tick)
            except asyncio.QueueFull:
                pass

    async def _flush_loop(self) -> None:
        """Flush latest ticks from coalescing buffer into queue."""
        try:
            while self._subscribed:
                await self._flush_event.wait()
                self._flush_event.clear()

                if not self._latest_by_symbol:
                    continue

                # drain snapshot
                items = list(self._latest_by_symbol.values())
                self._latest_by_symbol.clear()

                for tick in items:
                    self._put_tick_drop_oldest(tick)

                # Yield control
                await asyncio.sleep(0)
        except asyncio.CancelledError:
            raise
