"""
Real-time order book depth streaming (Level II market data).
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from ..models import DepthSnapshot, DepthQuote

if TYPE_CHECKING:
    from ..protocol import ProtocolHandler
    from ..config import ClientConfig
    from ..api.symbols import SymbolCatalog

logger = logging.getLogger(__name__)


class DepthStream:
    """Async iterator for real-time order book depth data.
    
    Streams Level II market data (order book) showing bid and ask prices
    with their respective volumes at different price levels.
    
    Example:
        >>> async with DepthStream(protocol, config, symbols, "EURUSD", depth=10) as stream:
        ...     async for snapshot in stream:
        ...         print(f"Best bid: {snapshot.best_bid.price} ({snapshot.best_bid.volume} lots)")
        ...         print(f"Best ask: {snapshot.best_ask.price} ({snapshot.best_ask.volume} lots)")
        ...         print(f"Spread: {snapshot.spread}")
    """
    
    def __init__(
        self,
        protocol: ProtocolHandler,
        config: ClientConfig,
        symbols: SymbolCatalog,
        symbol: str,
        depth: int = 10
    ):
        """Initialize depth stream.
        
        Args:
            protocol: Protocol handler
            config: Client configuration
            symbols: Symbol catalog
            symbol: Symbol name to stream
            depth: Number of price levels to receive (default: 10)
        """
        self.protocol = protocol
        self.config = config
        self.symbols = symbols
        self.symbol = symbol
        self.depth = depth
        
        # Bounded queue for backpressure
        maxsize = getattr(config, "depth_queue_size", 100)
        self._queue: asyncio.Queue[DepthSnapshot] = asyncio.Queue(maxsize=maxsize)
        self._active = False
        self._subscribed = False
        self._symbol_id: int = 0
        
        # Track current order book state for incremental updates
        self._bids: dict[int, DepthQuote] = {}  # quote_id -> DepthQuote
        self._asks: dict[int, DepthQuote] = {}  # quote_id -> DepthQuote
    
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
        """Subscribe to depth quote updates."""
        try:
            from ..messages.OpenApiMessages_pb2 import (
                ProtoOASubscribeDepthQuotesReq,
                ProtoOADepthEvent,
            )
            
            # Get symbol ID
            symbol_info = await self.symbols.get_symbol(self.symbol)
            if not symbol_info:
                raise ValueError(f"Symbol not found: {self.symbol}")
            
            self._symbol_id = symbol_info.id
            
            # Register handler for depth events
            def depth_handler(msg):
                if hasattr(msg, 'symbolId') and msg.symbolId == self._symbol_id:
                    try:
                        snapshot = self._parse_depth_event(msg, symbol_info)
                        if snapshot and self._active:
                            try:
                                self._queue.put_nowait(snapshot)
                            except asyncio.QueueFull:
                                logger.warning(f"Depth queue full for {self.symbol}, dropping update")
                    except Exception as e:
                        logger.error(f"Error parsing depth event: {e}", exc_info=True)
            
            self.protocol.add_handler(ProtoOADepthEvent, depth_handler)
            
            # Send subscription request
            req = ProtoOASubscribeDepthQuotesReq()
            req.ctidTraderAccountId = self.config.account_id
            req.symbolId = self._symbol_id
            req.depth = self.depth
            
            response = await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="SubscribeDepthQuotes"
            )
            
            self._subscribed = True
            logger.info(f"Subscribed to depth quotes for {self.symbol} (depth={self.depth})")
        
        except Exception as e:
            logger.error(f"Failed to subscribe to depth quotes: {e}", exc_info=True)
            raise
    
    async def _unsubscribe(self):
        """Unsubscribe from depth quote updates."""
        if not self._subscribed:
            return
        
        try:
            from ..messages.OpenApiMessages_pb2 import (
                ProtoOAUnsubscribeDepthQuotesReq,
                ProtoOADepthEvent,
            )
            
            # Remove handler
            self.protocol.remove_handler(ProtoOADepthEvent)
            
            # Send unsubscribe request
            req = ProtoOAUnsubscribeDepthQuotesReq()
            req.ctidTraderAccountId = self.config.account_id
            req.symbolId = self._symbol_id
            
            await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="UnsubscribeDepthQuotes"
            )
            
            self._subscribed = False
            logger.info(f"Unsubscribed from depth quotes for {self.symbol}")
        
        except Exception as e:
            logger.error(f"Failed to unsubscribe from depth quotes: {e}", exc_info=True)
    
    def _parse_depth_event(self, event, symbol_info) -> DepthSnapshot:
        """Parse depth event into snapshot.
        
        The ProtoOADepthEvent contains incremental updates:
        - newQuotes: New price levels added
        - deletedQuotes: Quote IDs removed from the book
        """
        import time
        
        # Get the scale for price conversion
        scale = 10 ** symbol_info.digits
        
        # Process new quotes
        if hasattr(event, 'newQuotes'):
            for quote in event.newQuotes:
                quote_id = quote.id
                price = quote.price / scale
                volume = quote.size / 100_000_000  # Convert from protocol units to lots
                side = "BUY" if quote.side == 1 else "ASK"  # 1=BUY, 2=ASK
                
                depth_quote = DepthQuote(
                    id=quote_id,
                    price=price,
                    volume=volume,
                    side=side
                )
                
                if side == "BUY":
                    self._bids[quote_id] = depth_quote
                else:
                    self._asks[quote_id] = depth_quote
        
        # Process deleted quotes
        if hasattr(event, 'deletedQuotes'):
            for quote_id in event.deletedQuotes:
                self._bids.pop(quote_id, None)
                self._asks.pop(quote_id, None)
        
        # Build snapshot
        # Sort bids by price descending (best bid first)
        bids = sorted(self._bids.values(), key=lambda q: q.price, reverse=True)
        # Sort asks by price ascending (best ask first)
        asks = sorted(self._asks.values(), key=lambda q: q.price)
        
        timestamp = int(time.time() * 1000)
        
        return DepthSnapshot(
            symbol_id=self._symbol_id,
            symbol_name=self.symbol,
            bids=bids,
            asks=asks,
            timestamp=timestamp
        )
    
    async def resubscribe(self):
        """Resubscribe after reconnection."""
        if self._active:
            # Clear existing state
            self._bids.clear()
            self._asks.clear()
            self._subscribed = False
            await self._subscribe()
    
    def __aiter__(self):
        """Return async iterator."""
        return self
    
    async def __anext__(self) -> DepthSnapshot:
        """Get next depth snapshot."""
        if not self._active:
            raise StopAsyncIteration
        
        try:
            # Wait for next snapshot with timeout
            snapshot = await asyncio.wait_for(
                self._queue.get(),
                timeout=30.0
            )
            return snapshot
        except asyncio.TimeoutError:
            if self._active:
                # Still active but no data - continue waiting
                return await self.__anext__()
            raise StopAsyncIteration
        except Exception as e:
            logger.error(f"Error in depth stream: {e}", exc_info=True)
            raise StopAsyncIteration
