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
        """Subscribe to depth quote updates.

        ProtoOASubscribeDepthQuotesReq fields: ctidTraderAccountId, symbolId
        (no 'depth' field — the server sends all available levels).

        ProtoOADepthEvent fields: ctidTraderAccountId, symbolId,
            newQuotes (repeated ProtoOADepthQuote), deletedQuotes (repeated uint64)

        ProtoOADepthQuote fields: id, size, bid, ask
            bid/ask are prices (double); size is volume (uint64 in protocol units).
            A quote with bid>0 is a bid-side quote; ask>0 is an ask-side quote.
        """
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
            self._symbol_info = symbol_info

            # Register handler via dispatcher (same API as TickStream/CandleStream)
            self._depth_payload_type = ProtoOADepthEvent().payloadType
            self.protocol.dispatcher.register(
                self._depth_payload_type,
                self._on_depth_event,
            )

            # Send subscription request
            # NOTE: ProtoOASubscribeDepthQuotesReq has no 'depth' field
            req = ProtoOASubscribeDepthQuotesReq()
            req.ctidTraderAccountId = self.config.account_id
            req.symbolId.append(self._symbol_id)

            await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="SubscribeDepthQuotes",
            )

            self._subscribed = True
            logger.info(f"Subscribed to depth quotes for {self.symbol}")

        except Exception as e:
            logger.error(f"Failed to subscribe to depth quotes: {e}", exc_info=True)
            raise
    
    async def _unsubscribe(self):
        """Unsubscribe from depth quote updates."""
        if not self._subscribed:
            return

        try:
            from ..messages.OpenApiMessages_pb2 import ProtoOAUnsubscribeDepthQuotesReq

            # Unregister dispatcher handler
            if hasattr(self, '_depth_payload_type'):
                self.protocol.dispatcher.unregister(
                    self._depth_payload_type,
                    self._on_depth_event,
                )

            # Send unsubscribe request
            req = ProtoOAUnsubscribeDepthQuotesReq()
            req.ctidTraderAccountId = self.config.account_id
            req.symbolId.append(self._symbol_id)

            await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="UnsubscribeDepthQuotes",
            )

            self._subscribed = False
            logger.info(f"Unsubscribed from depth quotes for {self.symbol}")

        except Exception as e:
            logger.error(f"Failed to unsubscribe from depth quotes: {e}", exc_info=True)

    def _has_quotes(self) -> bool:
        """Return True if the order book has at least one bid or ask level."""
        return bool(self._bids or self._asks)

    async def _on_depth_event(self, envelope) -> None:
        """Handle incoming ProtoOADepthEvent from dispatcher."""
        try:
            from ..transport import ProtocolFraming
            payload = ProtocolFraming.extract_payload(envelope)

            if int(getattr(payload, 'symbolId', 0)) != self._symbol_id:
                return

            snapshot = self._parse_depth_event(payload)
            # Only enqueue if the order book has real quotes — the server
            # typically sends an empty initial ProtoOADepthEvent to
            # acknowledge the subscription before real quotes arrive.
            if snapshot and self._active and self._has_quotes():
                try:
                    self._queue.put_nowait(snapshot)
                except asyncio.QueueFull:
                    # Drop oldest, keep latest
                    try:
                        self._queue.get_nowait()
                        self._queue.task_done()
                    except asyncio.QueueEmpty:
                        pass
                    try:
                        self._queue.put_nowait(snapshot)
                    except asyncio.QueueFull:
                        logger.warning(f"Depth queue full for {self.symbol}, dropping update")
        except Exception as e:
            logger.error(f"Error processing depth event: {e}", exc_info=True)

    def _parse_depth_event(self, event) -> DepthSnapshot:
        """Parse depth event into snapshot.

        ProtoOADepthEvent incremental update structure:
          newQuotes    (repeated ProtoOADepthQuote): new/updated levels
          deletedQuotes (repeated uint64): quote IDs to remove

        ProtoOADepthQuote fields:
          id   (uint64) — unique quote identifier
          size (uint64) — volume in protocol units (divide by lot_size to get lots)
          bid  (double) — bid price (>0 when this is a bid-side level, else 0)
          ask  (double) — ask price (>0 when this is an ask-side level, else 0)

        NOTE: There is no 'price' or 'side' field. Bid/ask side is determined by
        which price field is non-zero.
        """
        import time

        symbol_info = getattr(self, '_symbol_info', None)
        lot_size_units = float(symbol_info.lot_size_units) if symbol_info and symbol_info.lot_size_units else 100_000.0

        # Process new/updated quotes
        for quote in list(getattr(event, 'newQuotes', []) or []):
            quote_id = int(quote.id)
            size_raw = int(getattr(quote, 'size', 0) or 0)
            bid_price = float(getattr(quote, 'bid', 0.0) or 0.0)
            ask_price = float(getattr(quote, 'ask', 0.0) or 0.0)

            # volume: size is in protocol units (same unit as tradeData.volume)
            volume = (float(size_raw) / 100.0) / lot_size_units if lot_size_units > 0 else 0.0

            if bid_price > 0:
                self._bids[quote_id] = DepthQuote(
                    id=quote_id, price=bid_price, volume=volume, side="BID"
                )
                self._asks.pop(quote_id, None)
            elif ask_price > 0:
                self._asks[quote_id] = DepthQuote(
                    id=quote_id, price=ask_price, volume=volume, side="ASK"
                )
                self._bids.pop(quote_id, None)

        # Process deleted quotes
        for quote_id in list(getattr(event, 'deletedQuotes', []) or []):
            self._bids.pop(int(quote_id), None)
            self._asks.pop(int(quote_id), None)

        # Build sorted snapshot (best bid first = highest price; best ask first = lowest price)
        bids = sorted(self._bids.values(), key=lambda q: q.price, reverse=True)
        asks = sorted(self._asks.values(), key=lambda q: q.price)

        return DepthSnapshot(
            symbol_id=self._symbol_id,
            symbol_name=self.symbol,
            bids=bids,
            asks=asks,
            timestamp=int(time.time() * 1000),
        )
    
    async def resubscribe(self, protocol, symbols) -> None:
        """Resubscribe after reconnection (best-effort)."""
        if not self._active or not self._subscribed:
            return

        try:
            await self._unsubscribe()
        except Exception:
            pass

        self.protocol = protocol
        self.symbols = symbols
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
