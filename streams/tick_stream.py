"""
Real-time tick data streaming.
"""

from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator, TYPE_CHECKING

from ..models import Tick
from ..transport import ProtocolFraming

if TYPE_CHECKING:
    from ..protocol import ProtocolHandler
    from ..config import ClientConfig
    from ..api.symbols import SymbolCatalog

logger = logging.getLogger(__name__)


class TickStream:
    """Async iterator for real-time tick data.
    
    Example:
        >>> async with TickStream(protocol, config, symbols, "EURUSD") as stream:
        ...     async for tick in stream:
        ...         print(f"Tick: {tick.bid}/{tick.ask}")
    """
    
    def __init__(
        self,
        protocol: ProtocolHandler,
        config: ClientConfig,
        symbols: SymbolCatalog,
        symbol: str
    ):
        """Initialize tick stream.
        
        Args:
            protocol: Protocol handler
            config: Client configuration
            symbols: Symbol catalog
            symbol: Symbol name to stream
        """
        self.protocol = protocol
        self.config = config
        self.symbols = symbols
        self.symbol = symbol
        
        # Bounded queue for backpressure (prevents unbounded memory growth)
        maxsize = getattr(config, "tick_queue_size", 1000)
        self._queue: asyncio.Queue[Tick] = asyncio.Queue(maxsize=maxsize)
        # _active controls iterator lifetime (context manager).
        # _subscribed controls whether we've sent SubscribeSpots.
        self._active = False
        self._subscribed = False
        self._symbol_id: int = 0
    
    async def __aenter__(self):
        """Enter async context manager."""
        self._active = True
        await self._subscribe()
        # Register for reconnect recovery (if constructed via client.market_data)
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
        # Unregister first so reconnect doesn't race with unsubscribe
        client = getattr(self, "_client", None)
        if client is not None and hasattr(client, "_stream_registry"):
            try:
                client._stream_registry.unregister(self)
            except Exception:
                pass
        await self._unsubscribe()
    
    async def _subscribe(self):
        """Subscribe to tick updates."""
        try:
            from ..messages.OpenApiMessages_pb2 import (
                ProtoOASubscribeSpotsReq,
                ProtoOASpotEvent,
            )
            
            # Get symbol ID
            symbol_info = await self.symbols.get_symbol(self.symbol)
            if not symbol_info:
                raise ValueError(f"Symbol not found: {self.symbol}")
            
            self._symbol_id = symbol_info.id
            
            # Register handler for spot events
            self.protocol.dispatcher.register(
                ProtoOASpotEvent().payloadType,
                self._on_tick
            )
            
            # Send subscription request
            req = ProtoOASubscribeSpotsReq()
            req.ctidTraderAccountId = self.config.account_id
            req.symbolId.append(self._symbol_id)
            
            await self.protocol.send_request(
                req,
                timeout=10.0,
                request_type="SubscribeSpots"
            )
            
            self._subscribed = True
            logger.info(f"Subscribed to {self.symbol} ticks")
        
        except Exception as e:
            logger.error(f"Failed to subscribe to ticks: {e}", exc_info=True)
            raise
    
    async def resubscribe(self, protocol, symbols) -> None:
        """Resubscribe after reconnect (best-effort).

        Keeps the same queue; consumers can continue reading.
        """
        if not self._subscribed:
            return

        try:
            await self._unsubscribe()
        except Exception:
            pass

        self.protocol = protocol
        self.symbols = symbols
        await self._subscribe()

    async def _unsubscribe(self):
        """Unsubscribe from tick updates."""
        if not self._subscribed:
            return
        
        try:
            from ..messages.OpenApiMessages_pb2 import (
                ProtoOAUnsubscribeSpotsReq,
                ProtoOASpotEvent,
            )
            
            # Unregister handler
            self.protocol.dispatcher.unregister(
                ProtoOASpotEvent().payloadType,
                self._on_tick
            )
            
            # Send unsubscription request
            req = ProtoOAUnsubscribeSpotsReq()
            req.ctidTraderAccountId = self.config.account_id
            req.symbolId.append(self._symbol_id)
            
            await self.protocol.send_request(
                req,
                timeout=10.0,
                request_type="UnsubscribeSpots"
            )
            
            self._subscribed = False
            logger.info(f"Unsubscribed from {self.symbol} ticks")
        
        except Exception as e:
            logger.error(f"Failed to unsubscribe from ticks: {e}", exc_info=True)
    
    async def _on_tick(self, message):
        """Handle incoming tick event."""
        try:
            payload = ProtocolFraming.extract_payload(message)
            
            # Filter for our symbol
            if payload.symbolId != self._symbol_id:
                return
            
            # Create tick object
            tick = Tick(
                symbol_id=payload.symbolId,
                symbol_name=self.symbol,
                bid=getattr(payload, 'bid', 0) / 100000.0,
                ask=getattr(payload, 'ask', 0) / 100000.0,
                timestamp=getattr(payload, 'timestamp', 0),
            )
            
            try:
                self._queue.put_nowait(tick)
            except asyncio.QueueFull:
                # Drop oldest tick to keep latest updates
                try:
                    _ = self._queue.get_nowait()
                    self._queue.task_done()
                except asyncio.QueueEmpty:
                    pass

                try:
                    asyncio.create_task(
                        self.protocol.events.emit(
                            "stream.tick_dropped",
                            {"stream": "TickStream", "symbol": self.symbol, "reason": "queue_full"},
                        )
                    )
                except Exception:
                    pass

                try:
                    self._queue.put_nowait(tick)
                except asyncio.QueueFull:
                    pass
        
        except Exception as e:
            logger.error(f"Error processing tick: {e}", exc_info=True)
    
    def __aiter__(self):
        """Make this an async iterator."""
        return self
    
    async def __anext__(self) -> Tick:
        """Get next tick."""
        if not self._active:
            raise StopAsyncIteration

        # During reconnect resubscribe, we may be temporarily unsubscribed.
        # Keep the iterator alive and wait for new ticks.
        return await self._queue.get()
