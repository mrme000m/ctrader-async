"""
cTrader Async Client
~~~~~~~~~~~~~~~~~~~

A modern, pure Python asyncio client library for the cTrader Open API.

Basic usage:

    >>> import asyncio
    >>> import ctc
    >>> from ctc import CTraderClient, TradeSide
    >>> 
    >>> async def main():
    ...     async with CTraderClient(
    ...         client_id="YOUR_ID",
    ...         client_secret="YOUR_SECRET",
    ...         access_token="YOUR_TOKEN",
    ...         account_id=12345
    ...     ) as client:
    ...         position = await client.trading.place_market_order(
    ...             symbol="EURUSD",
    ...             side=TradeSide.BUY,
    ...             volume=0.01
    ...         )
    ...         print(f"Position: {position.id}")
    >>> 
    >>> asyncio.run(main())

:copyright: (c) 2024 by cTrader Async Contributors.
:license: MIT, see LICENSE for more details.
"""

__version__ = "0.1.0"
__author__ = "cTrader Async Contributors"
__license__ = "MIT"

from .client import CTraderClient  # noqa
from .config import ClientConfig
from .models import (
    Position,
    Order,
    Deal,
    Symbol,
    AccountInfo,
    Tick,
    Candle,
    DepthQuote,
    DepthSnapshot,
    MarginInfo,
    PositionPnL,
    MarginCall,
)

from .streams import MultiTickStream, Fanout, DepthStream, CandleStream
from .enums import (
    TradeSide,
    OrderType,
    TimeFrame,
    TimeInForce,
    OrderTriggerMethod,
)

# Import exceptions for easy access
from .utils.errors import (
    CTraderError,
    ConnectionError,
    AuthenticationError,
    TradingError,
    MarketClosedError,
    RateLimitError,
    SymbolNotFoundError,
    OrderError,
)

# Bot/agent utilities
from .utils import (
    EventBus,
    HookManager,
    HookContext,
    retry_async,
    RetryPolicy,
    CircuitBreaker,
    TickEvent,
    ExecutionEvent,
    ExecutionErrorEvent,
    OrderUpdateEvent,
    PositionUpdateEvent,
    DealEvent,
    gather_limited,
    normalize_order_update,
    normalize_position_update,
    ModelEventBridge,
    NormalizedDeal,
    NormalizedExecutionError,
    TradingStateCacheUpdater,
    MetricsCollector,
    MetricsSnapshot,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__license__",
    
    # Main client
    "CTraderClient",
    "ClientConfig",
    
    # Data models
    "Position",
    "Order",
    "Deal",
    "Symbol",
    "AccountInfo",
    "Tick",
    "Candle",
    "DepthQuote",
    "DepthSnapshot",
    "MarginInfo",
    "PositionPnL",
    "MarginCall",
    "MultiTickStream",
    "Fanout",
    "DepthStream",
    "CandleStream",
    
    # Enums
    "TradeSide",
    "OrderType",
    "TimeFrame",
    "TimeInForce",
    "OrderTriggerMethod",
    
    # Exceptions
    "CTraderError",
    "ConnectionError",
    "AuthenticationError",
    "TradingError",
    "MarketClosedError",
    "RateLimitError",
    "SymbolNotFoundError",
    "OrderError",

    # Bot/agent utilities
    "EventBus",
    "HookManager",
    "HookContext",
    "retry_async",
    "RetryPolicy",
    "CircuitBreaker",
    "TickEvent",
    "ExecutionEvent",
    "ExecutionErrorEvent",
    "OrderUpdateEvent",
    "PositionUpdateEvent",
    "DealEvent",
    "gather_limited",
    "normalize_order_update",
    "normalize_position_update",
    "ModelEventBridge",
    "NormalizedDeal",
    "NormalizedExecutionError",
    "TradingStateCacheUpdater",
    "MetricsCollector",
    "MetricsSnapshot",
]
