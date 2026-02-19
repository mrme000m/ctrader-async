"""
Market data API with streaming support.
"""

from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING, AsyncIterator
from datetime import datetime, timezone

from ..models import Tick, Candle
from ..enums import TimeFrame
from ..utils.rate_limiter import TokenBucketRateLimiter

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
        # Separate rate limiters: historical data has lower limits than trading operations
        # Historical data: 5 req/s per connection (per spec)
        self._historical_rate_limiter = TokenBucketRateLimiter(
            rate=config.rate_limit_historical,
            capacity=config.rate_limit_historical,
        )
        # Trading/non-historical operations: 50 req/s per connection (per spec)
        self._trading_rate_limiter = TokenBucketRateLimiter(
            rate=config.rate_limit_trading,
            capacity=config.rate_limit_trading,
        )
    
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
        # Historical data requests use lower rate limit (5 req/s)
        await self._historical_rate_limiter.acquire()
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
    
    def stream_ticks(self, symbol: str, *, subscribe_to_timestamp: bool = False):
        """Stream real-time tick data.
        
        Args:
            symbol: Symbol name
            subscribe_to_timestamp: Request server-side spot timestamps in
                subscribe payload (``subscribeToSpotTimestamp``)
            
        Returns:
            Async context manager that yields ticks
            
        Example:
            >>> async with market_data.stream_ticks("EURUSD") as stream:
            ...     async for tick in stream:
            ...         print(f"Tick: {tick.bid}/{tick.ask}")
        """
        from ..streams import TickStream
        s = TickStream(
            self.protocol,
            self.config,
            self.symbols,
            symbol,
            subscribe_to_timestamp=subscribe_to_timestamp,
        )
        # Attach client for reconnect recovery (best-effort)
        if self._client is not None:
            setattr(s, "_client", self._client)
        return s

    def stream_ticks_multi(
        self,
        symbols: list[str] | tuple[str, ...],
        *,
        coalesce_latest: bool = True,
        subscribe_to_timestamp: bool = False,
    ):
        """Stream real-time tick data for multiple symbols.

        Args:
            symbols: Iterable of symbol names
            coalesce_latest: If True, keep only latest tick per symbol when under load
            subscribe_to_timestamp: Request server-side spot timestamps in
                subscribe payload (``subscribeToSpotTimestamp``)

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
            subscribe_to_timestamp=subscribe_to_timestamp,
        )
        if self._client is not None:
            setattr(s, "_client", self._client)
        return s
    
    def stream_depth(self, symbol: str, depth: int = 10):
        """Stream real-time order book depth (Level II market data).
        
        Args:
            symbol: Symbol name
            depth: Number of price levels to receive (default: 10)
            
        Returns:
            Async context manager that yields DepthSnapshot objects
            
        Example:
            >>> async with market_data.stream_depth("EURUSD", depth=10) as stream:
            ...     async for snapshot in stream:
            ...         print(f"Best bid: {snapshot.best_bid.price} ({snapshot.best_bid.volume} lots)")
            ...         print(f"Best ask: {snapshot.best_ask.price} ({snapshot.best_ask.volume} lots)")
            ...         print(f"Spread: {snapshot.spread}")
            ...         print(f"Total bid volume (5 levels): {snapshot.total_bid_volume(5)}")
        """
        from ..streams import DepthStream
        
        s = DepthStream(self.protocol, self.config, self.symbols, symbol, depth)
        # Attach client for reconnect recovery
        if self._client is not None:
            setattr(s, "_client", self._client)
        return s
    
    def stream_candles(self, symbol: str, timeframe: "TimeFrame"):
        """Stream real-time candlestick data as candles form.
        
        Streams live candle updates as they develop. Each update provides
        the current OHLC values for the forming candle.
        
        Args:
            symbol: Symbol name
            timeframe: Candle timeframe (e.g., TimeFrame.M1, TimeFrame.H1)
            
        Returns:
            Async context manager that yields Candle objects
            
        Example:
            >>> from ctc.enums import TimeFrame
            >>> async with market_data.stream_candles("EURUSD", TimeFrame.M5) as stream:
            ...     async for candle in stream:
            ...         print(f"Candle: O={candle.open:.5f} H={candle.high:.5f} "
            ...               f"L={candle.low:.5f} C={candle.close:.5f} V={candle.volume}")
            ...         
            ...         # Check for bullish/bearish candle
            ...         if candle.close > candle.open:
            ...             print("  → Bullish candle")
            ...         elif candle.close < candle.open:
            ...             print("  → Bearish candle")
        """
        from ..streams import CandleStream
        
        s = CandleStream(self.protocol, self.config, self.symbols, symbol, timeframe)
        # Attach client for reconnect recovery
        if self._client is not None:
            setattr(s, "_client", self._client)
        return s
    
    async def get_tick_data(
        self,
        symbol: str,
        quote_type: str = "BID",
        from_timestamp: Optional[int] = None,
        to_timestamp: Optional[int] = None,
        count: int = 1000,
    ) -> list[dict]:
        """Get historical raw tick data for a symbol.

        Fetches tick-by-tick price history using `ProtoOAGetTickDataReq`.
        Useful for backtesting, tick-level analysis, and custom charting.

        Args:
            symbol: Symbol name (e.g., "EURUSD")
            quote_type: "BID" or "ASK" (default: "BID")
            from_timestamp: Start time in milliseconds (optional)
            to_timestamp: End time in milliseconds (optional)
            count: Maximum number of ticks to return (default: 1000)

        Returns:
            List of dicts with keys: ``timestamp``, ``price``, ``type``

        Example:
            >>> ticks = await market_data.get_tick_data("EURUSD", quote_type="BID", count=500)
            >>> for tick in ticks:
            ...     print(f"{tick['timestamp']}: {tick['price']}")
        """
        # Historical tick data uses lower rate limit (5 req/s)
        await self._historical_rate_limiter.acquire()
        try:
            from ..messages.OpenApiMessages_pb2 import ProtoOAGetTickDataReq
            from ..messages.OpenApiModelMessages_pb2 import ProtoOAQuoteType

            symbol_info = await self.symbols.get_symbol(symbol)
            if not symbol_info:
                raise ValueError(f"Symbol not found: {symbol}")

            import time as _time
            now_ms = int(_time.time() * 1000)
            if to_timestamp is None:
                to_timestamp = now_ms
            if from_timestamp is None:
                from_timestamp = to_timestamp - 3600_000  # 1 hour default window

            qt = ProtoOAQuoteType.BID if quote_type.upper() == "BID" else ProtoOAQuoteType.ASK

            req = ProtoOAGetTickDataReq()
            req.ctidTraderAccountId = self.config.account_id
            req.symbolId = symbol_info.id
            req.type = qt
            req.fromTimestamp = int(from_timestamp)
            req.toTimestamp = int(to_timestamp)

            response = await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="GetTickData",
            )

            scale = 10 ** symbol_info.digits
            ticks = []
            tick_data_list = list(getattr(response, "tickData", []) or [])

            # cTrader tick data uses cumulative timestamps and delta prices
            cumulative_timestamp = int(from_timestamp)
            cumulative_price = 0

            for td in tick_data_list:
                cumulative_timestamp += int(getattr(td, "timestamp", 0))
                cumulative_price += int(getattr(td, "tick", 0))
                ticks.append({
                    "timestamp": cumulative_timestamp,
                    "price": round(cumulative_price / scale, symbol_info.digits),
                    "type": quote_type.upper(),
                })

            has_more = bool(getattr(response, "hasMore", False))
            logger.info(
                f"Retrieved {len(ticks)} {quote_type} ticks for {symbol}"
                + (" (more available)" if has_more else "")
            )
            return ticks

        except Exception as e:
            logger.error(f"Failed to get tick data: {e}", exc_info=True)
            raise

    def _parse_candle(self, bar: any, symbol_info: any, timeframe: TimeFrame) -> Candle:
        """Parse candle from protobuf data.

        ProtoOATrendbar fields:
          low                 (int64)  — absolute low price * 10^digits
          deltaOpen           (uint32) — open - low (in same units)
          deltaHigh           (uint32) — high - low (in same units)
          deltaClose          (uint32) — close - low (in same units)
          volume              (uint64) — tick volume
          utcTimestampInMinutes (uint32)
          period              (ProtoOATrendbarPeriod enum)

        Scale = 10^digits (NOT hardcoded 100000).
        """
        scale = 10 ** int(symbol_info.digits)
        raw_low = int(getattr(bar, 'low', 0) or 0)
        base = raw_low / scale

        return Candle(
            timestamp=datetime.fromtimestamp(
                int(bar.utcTimestampInMinutes) * 60, tz=timezone.utc
            ),
            open=round(base + int(getattr(bar, 'deltaOpen', 0) or 0) / scale, symbol_info.digits),
            high=round(base + int(getattr(bar, 'deltaHigh', 0) or 0) / scale, symbol_info.digits),
            low=round(base, symbol_info.digits),
            close=round(base + int(getattr(bar, 'deltaClose', 0) or 0) / scale, symbol_info.digits),
            volume=int(getattr(bar, 'volume', 0) or 0),
            symbol_name=symbol_info.name,
            timeframe=timeframe.name,
        )
