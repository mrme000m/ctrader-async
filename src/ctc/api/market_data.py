"""
Market data API with streaming support.
"""

from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING, AsyncIterator
from datetime import datetime, timezone

from ..models import Tick, Candle
from ..enums import TimeFrame

if TYPE_CHECKING:
    from ..protocol import ProtocolHandler
    from ..config import ClientConfig
    from .symbols import SymbolCatalog

logger = logging.getLogger(__name__)


class MarketDataAPI:
    """High-level API for market data operations.
    
    Example:
        >>> market_data = MarketDataAPI(protocol, config, symbols)
        >>> candles = await market_data.get_candles("EURUSD", TimeFrame.H1, count=100)
        >>> async with market_data.stream_ticks("EURUSD") as stream:
        ...     async for tick in stream:
        ...         print(f"Tick: {tick.bid}/{tick.ask}")
    """
    
    def __init__(
        self,
        protocol: ProtocolHandler,
        config: ClientConfig,
        symbols: SymbolCatalog,
        *,
        client: object | None = None,
    ):
        """Initialize market data API.
        
        Args:
            protocol: Protocol handler
            config: Client configuration
            symbols: Symbol catalog
        """
        self.protocol = protocol
        self.config = config
        self.symbols = symbols
        self._client = client
    
    async def get_candles(
        self,
        symbol: str,
        timeframe: TimeFrame | str,
        count: int = 100,
        from_timestamp: Optional[int] = None,
        to_timestamp: Optional[int] = None,
    ) -> list[Candle]:
        """Get historical candlestick data.
        
        Args:
            symbol: Symbol name
            timeframe: Timeframe (e.g., TimeFrame.H1 or "H1")
            count: Number of candles to retrieve
            from_timestamp: Start timestamp in milliseconds (optional)
            to_timestamp: End timestamp in milliseconds (optional)
            
        Returns:
            List of candles
        """
        try:
            from ..messages.OpenApiMessages_pb2 import ProtoOAGetTrendbarsReq
            from ..enums import to_proto_timeframe
            
            # Get symbol info
            symbol_info = await self.symbols.get_symbol(symbol)
            if not symbol_info:
                raise ValueError(f"Symbol not found: {symbol}")
            
            # Convert timeframe
            if isinstance(timeframe, str):
                timeframe = TimeFrame(timeframe)
            
            # Build request
            req = ProtoOAGetTrendbarsReq()
            req.ctidTraderAccountId = self.config.account_id
            req.symbolId = symbol_info.id
            req.period = to_proto_timeframe(timeframe)
            req.count = count

            # The protobuf schema requires both fromTimestamp and toTimestamp.
            # If not provided, request the last `count` bars up to now.
            import time as _time
            now_ms = int(_time.time() * 1000)
            if to_timestamp is None:
                to_timestamp = now_ms
            if from_timestamp is None:
                # Rough window: timeframe seconds * count
                from_timestamp = to_timestamp - (timeframe.seconds * max(1, count) * 1000)

            req.fromTimestamp = int(from_timestamp)
            req.toTimestamp = int(to_timestamp)
            
            response = await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="GetTrendbars"
            )
            
            # Parse candles
            candles = []
            for bar in getattr(response, 'trendbar', []):
                candle = self._parse_candle(bar, symbol_info, timeframe)
                candles.append(candle)
            
            return candles
        
        except Exception as e:
            logger.error(f"Failed to get candles: {e}", exc_info=True)
            raise
    
    def stream_ticks(self, symbol: str):
        """Stream real-time tick data.
        
        Args:
            symbol: Symbol name
            
        Returns:
            Async context manager that yields ticks
            
        Example:
            >>> async with market_data.stream_ticks("EURUSD") as stream:
            ...     async for tick in stream:
            ...         print(f"Tick: {tick.bid}/{tick.ask}")
        """
        from ..streams import TickStream
        s = TickStream(self.protocol, self.config, self.symbols, symbol)
        # Attach client for reconnect recovery (best-effort)
        if self._client is not None:
            setattr(s, "_client", self._client)
        return s

    def stream_ticks_multi(self, symbols: list[str] | tuple[str, ...], *, coalesce_latest: bool = True):
        """Stream real-time tick data for multiple symbols.

        Args:
            symbols: Iterable of symbol names
            coalesce_latest: If True, keep only latest tick per symbol when under load

        Returns:
            Async context manager yielding Tick objects
        """
        from ..streams import MultiTickStream

        s = MultiTickStream(
            self.protocol,
            self.config,
            self.symbols,
            symbols,
            coalesce_latest=coalesce_latest,
        )
        if self._client is not None:
            setattr(s, "_client", self._client)
        return s
    
    def _parse_candle(self, bar: any, symbol_info: any, timeframe: TimeFrame) -> Candle:
        """Parse candle from protobuf data."""
        # cTrader uses deltas for OHLC
        scale = 100000.0
        base = (bar.low or 0) / scale
        
        return Candle(
            timestamp=datetime.fromtimestamp(bar.utcTimestampInMinutes * 60, tz=timezone.utc),
            open=round(base + (getattr(bar, 'deltaOpen', 0) / scale), symbol_info.digits),
            high=round(base + (getattr(bar, 'deltaHigh', 0) / scale), symbol_info.digits),
            low=round(base, symbol_info.digits),
            close=round(base + (getattr(bar, 'deltaClose', 0) / scale), symbol_info.digits),
            volume=getattr(bar, 'volume', 0),
            symbol_name=symbol_info.name,
            timeframe=timeframe.name,
        )
