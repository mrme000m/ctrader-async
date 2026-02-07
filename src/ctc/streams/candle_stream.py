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
                ProtoOASubscribeLiveTrendbarRes,
            )
            from ..messages.OpenApiModelMessages_pb2 import ProtoOATrendbar
            
            # Get symbol ID
            symbol_info = await self.symbols.get_symbol(self.symbol)
            if not symbol_info:
                raise ValueError(f"Symbol not found: {self.symbol}")
            
            self._symbol_id = symbol_info.id
            
            # Register handler for trendbar events
            def trendbar_handler(msg):
                # Check if this is a ProtoOATrendbar or a response
                if isinstance(msg, ProtoOATrendbar):
                    # This is a trendbar update
                    if hasattr(msg, 'symbolId') and msg.symbolId == self._symbol_id:
                        # Check if period matches
                        msg_period = getattr(msg, 'period', None)
                        if msg_period == self.timeframe.value:
                            try:
                                candle = self._parse_trendbar(msg, symbol_info)
                                if candle and self._active:
                                    try:
                                        self._queue.put_nowait(candle)
                                    except asyncio.QueueFull:
                                        logger.warning(f"Candle queue full for {self.symbol}, dropping update")
                            except Exception as e:
                                logger.error(f"Error parsing trendbar: {e}", exc_info=True)
            
            # Add handler for trendbar updates
            self.protocol.add_handler(ProtoOATrendbar, trendbar_handler)
            
            # Send subscription request
            req = ProtoOASubscribeLiveTrendbarReq()
            req.ctidTraderAccountId = self.config.account_id
            req.symbolId = self._symbol_id
            req.period = self.timeframe.value
            
            response = await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="SubscribeLiveTrendbar"
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
                ProtoOAUnsubscribeLiveTrendbarRes,
            )
            from ..messages.OpenApiModelMessages_pb2 import ProtoOATrendbar
            
            # Remove handler
            self.protocol.remove_handler(ProtoOATrendbar)
            
            # Send unsubscribe request
            req = ProtoOAUnsubscribeLiveTrendbarReq()
            req.ctidTraderAccountId = self.config.account_id
            req.symbolId = self._symbol_id
            
            await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="UnsubscribeLiveTrendbar"
            )
            
            self._subscribed = False
            logger.info(f"Unsubscribed from live candles for {self.symbol}")
        
        except Exception as e:
            logger.error(f"Failed to unsubscribe from live candles: {e}", exc_info=True)
    
    def _parse_trendbar(self, trendbar, symbol_info) -> Candle:
        """Parse trendbar into Candle.
        
        Args:
            trendbar: ProtoOATrendbar message
            symbol_info: Symbol information
            
        Returns:
            Candle object
        """
        # Get the scale for price conversion
        scale = 10 ** symbol_info.digits
        
        # Parse OHLC prices
        open_price = getattr(trendbar, 'open', None)
        high_price = getattr(trendbar, 'high', None)
        low_price = getattr(trendbar, 'low', None)
        close_price = getattr(trendbar, 'close', None)
        
        # Convert from protocol units to actual prices
        open_val = open_price / scale if open_price else None
        high_val = high_price / scale if high_price else None
        low_val = low_price / scale if low_price else None
        close_val = close_price / scale if close_price else None
        
        # Parse volume
        volume = getattr(trendbar, 'volume', None)
        
        # Parse timestamp (UTC timestamp in milliseconds)
        timestamp = getattr(trendbar, 'utcTimestampInMinutes', None)
        if timestamp:
            # Convert from minutes to milliseconds
            timestamp = timestamp * 60 * 1000
        
        return Candle(
            timestamp=timestamp,
            open=open_val,
            high=high_val,
            low=low_val,
            close=close_val,
            volume=volume,
            symbol_name=self.symbol,
            timeframe=self.timeframe.name
        )
    
    async def resubscribe(self):
        """Resubscribe after reconnection."""
        if self._active:
            self._subscribed = False
            await self._subscribe()
    
    def __aiter__(self):
        """Return async iterator."""
        return self
    
    async def __anext__(self) -> Candle:
        """Get next candle update."""
        if not self._active:
            raise StopAsyncIteration
        
        try:
            # Wait for next candle with timeout
            candle = await asyncio.wait_for(
                self._queue.get(),
                timeout=300.0  # 5 minutes timeout (longer than tick timeout)
            )
            return candle
        except asyncio.TimeoutError:
            if self._active:
                # Still active but no data - continue waiting
                return await self.__anext__()
            raise StopAsyncIteration
        except Exception as e:
            logger.error(f"Error in candle stream: {e}", exc_info=True)
            raise StopAsyncIteration
