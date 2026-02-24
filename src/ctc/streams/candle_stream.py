"""
Real-time live candlestick streaming.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from ..models import Candle
from ..enums import TimeFrame

if TYPE_CHECKING:
    from ..protocol import ProtocolHandler
    from ..config import ClientConfig
    from ..api.symbols import SymbolCatalog

logger = logging.getLogger(__name__)


class CandleStream:
    """Async iterator for real-time candlestick data.
    
    Streams live candles as they form in real-time. Each candle update
    includes the current OHLC values for the forming candle.
    
    Example:
        >>> async with CandleStream(protocol, config, symbols, "EURUSD", TimeFrame.M1) as stream:
        ...     async for candle in stream:
        ...         print(f"Candle: O={candle.open} H={candle.high} L={candle.low} C={candle.close}")
    """
    
    def __init__(
        self,
        protocol: ProtocolHandler,
        config: ClientConfig,
        symbols: SymbolCatalog,
        symbol: str,
        timeframe: TimeFrame
    ):
        """Initialize candle stream.
        
        Args:
            protocol: Protocol handler
            config: Client configuration
            symbols: Symbol catalog
            symbol: Symbol name to stream
            timeframe: Candle timeframe (e.g., TimeFrame.M1, TimeFrame.H1)
        """
        self.protocol = protocol
        self.config = config
        self.symbols = symbols
        self.symbol = symbol
        self.timeframe = timeframe
        
        # Bounded queue for backpressure
        maxsize = getattr(config, "candle_queue_size", 100)
        self._queue: asyncio.Queue[Candle] = asyncio.Queue(maxsize=maxsize)
        self._active = False
        self._subscribed = False
        self._symbol_id: int = 0
    
    async def __aenter__(self):
        """Enter async context manager."""
        self._active = True
        await self._subscribe()
        # Register for reconnect recovery
        client = getattr(self, "_client", None)
        if client is not None and hasattr(client, "_stream_registry"):
            try:
                client._stream_registry.register(self)
            except Exception:
                pass
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        self._active = False
        # Unregister from reconnect registry
        client = getattr(self, "_client", None)
        if client is not None and hasattr(client, "_stream_registry"):
            try:
                client._stream_registry.unregister(self)
            except Exception:
                pass
        await self._unsubscribe()
    
    async def _subscribe(self):
        """Subscribe to live candle updates."""
        try:
            from ..messages.OpenApiMessages_pb2 import (
                ProtoOASubscribeLiveTrendbarReq,
                # live candle updates are delivered in the generic spot event
                # message; the payload contains a `trendbar` field when the
                # server pushes candle data.
                ProtoOASpotEvent,
            )
            from ..transport import ProtocolFraming

            # Get symbol ID
            symbol_info = await self.symbols.get_symbol(self.symbol)
            if not symbol_info:
                raise ValueError(f"Symbol not found: {self.symbol}")

            self._symbol_id = symbol_info.id
            self._symbol_info = symbol_info

            # Register handler using the dispatcher API (same pattern as TickStream)
            # use a spot event sentinel since that's what the server actually
            # sends for live trendbar updates (it nests them inside
            # ProtoOASpotEvent.trendbar)
            _sentinel = ProtoOASpotEvent()
            self._payload_type = _sentinel.payloadType

            self.protocol.dispatcher.register(
                self._payload_type,
                self._on_trendbar,
            )

            # Send subscription request
            req = ProtoOASubscribeLiveTrendbarReq()
            req.ctidTraderAccountId = self.config.account_id
            req.symbolId = self._symbol_id
            req.period = self.timeframe.value

            await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="SubscribeLiveTrendbar",
            )

            self._subscribed = True
            logger.info(f"Subscribed to live candles for {self.symbol} {self.timeframe.name}")

        except Exception as e:
            logger.error(f"Failed to subscribe to live candles: {e}", exc_info=True)
            raise

    async def _unsubscribe(self):
        """Unsubscribe from live candle updates."""
        if not self._subscribed:
            return

        try:
            from ..messages.OpenApiMessages_pb2 import (
                ProtoOAUnsubscribeLiveTrendbarReq,
            )

            # Unregister dispatcher handler
            self.protocol.dispatcher.unregister(
                self._payload_type,
                self._on_trendbar,
            )

            # Send unsubscribe request
            req = ProtoOAUnsubscribeLiveTrendbarReq()
            req.ctidTraderAccountId = self.config.account_id
            req.symbolId = self._symbol_id

            await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="UnsubscribeLiveTrendbar",
            )

            self._subscribed = False
            logger.info(f"Unsubscribed from live candles for {self.symbol}")

        except Exception as e:
            logger.error(f"Failed to unsubscribe from live candles: {e}", exc_info=True)

    async def _on_trendbar(self, envelope):
        """Handle incoming live trendbar payloads embedded in a
        ProtoOASpotEvent."""
        try:
            from ..transport import ProtocolFraming
            payload = ProtocolFraming.extract_payload(envelope)

            # Filter for our symbol and period
            if getattr(payload, "symbolId", None) != self._symbol_id:
                return
            trendbar = getattr(payload, "trendbar", None)
            if trendbar is None:
                return
            if getattr(trendbar, "period", None) != self.timeframe.value:
                return

            candle = self._parse_trendbar(trendbar, self._symbol_info)
            if candle and self._active:
                try:
                    self._queue.put_nowait(candle)
                except asyncio.QueueFull:
                    # Drop oldest, keep latest
                    try:
                        self._queue.get_nowait()
                        self._queue.task_done()
                    except asyncio.QueueEmpty:
                        pass
                    try:
                        self._queue.put_nowait(candle)
                    except asyncio.QueueFull:
                        logger.warning(f"Candle queue full for {self.symbol}, dropping update")
        except Exception as e:
            logger.error(f"Error processing trendbar event: {e}", exc_info=True)

    def _parse_trendbar(self, trendbar, symbol_info) -> Candle:
        """Parse trendbar into Candle using correct delta encoding.

        The cTrader protocol stores trendbar prices as:
          low  = absolute price * 10^digits
          open = low + delta_open
          high = low + delta_high
          close= low + delta_close

        Args:
            trendbar: ProtoOATrendbar message (from LiveTrendbarEvent)
            symbol_info: Symbol information

        Returns:
            Candle object
        """
        scale = 10 ** int(symbol_info.digits)

        # low is the absolute baseline; open/high/close are deltas above low
        raw_low   = getattr(trendbar, "low",   None)
        raw_open  = getattr(trendbar, "deltaOpen",  None)
        raw_high  = getattr(trendbar, "deltaHigh",  None)
        raw_close = getattr(trendbar, "deltaClose", None)

        if raw_low is None:
            return None

        low_val   = raw_low / scale
        open_val  = (raw_low + (raw_open  or 0)) / scale
        high_val  = (raw_low + (raw_high  or 0)) / scale
        close_val = (raw_low + (raw_close or 0)) / scale

        volume = getattr(trendbar, "volume", 0) or 0

        # utcTimestampInMinutes → datetime (UTC)
        ts_minutes = getattr(trendbar, "utcTimestampInMinutes", None)
        from datetime import datetime, timezone
        if ts_minutes:
            ts_dt = datetime.fromtimestamp(int(ts_minutes) * 60, tz=timezone.utc)
        else:
            ts_dt = datetime.now(tz=timezone.utc)

        return Candle(
            timestamp=ts_dt,
            open=open_val,
            high=high_val,
            low=low_val,
            close=close_val,
            volume=int(volume),
            symbol_name=self.symbol,
            timeframe=self.timeframe.name,
        )

    async def resubscribe(self, protocol, symbols) -> None:
        """Resubscribe after reconnect (best-effort, matching StreamRegistry protocol)."""
        if not self._subscribed:
            return
        try:
            await self._unsubscribe()
        except Exception:
            pass
        self.protocol = protocol
        self.symbols = symbols
        await self._subscribe()
    
    def __aiter__(self):
        """Return async iterator."""
        return self
    
    async def __anext__(self) -> Candle:
        """Get next candle update."""
        while self._active:
            try:
                # Wait for next candle with timeout
                return await asyncio.wait_for(
                    self._queue.get(),
                    timeout=300.0  # 5 minutes timeout (longer than tick timeout)
                )
            except asyncio.TimeoutError:
                # Timeout - continue waiting if still active
                continue
        raise StopAsyncIteration
