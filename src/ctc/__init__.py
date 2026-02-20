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
from .auth import OAuthHelper

# Account-related classes
from .api.account import FullAccountInfo, CashFlowEntry, CashFlowType

# Risk-related classes
from .api.risk import LeverageTier, DynamicLeverage

# Asset catalog
from .api.assets import AssetCatalog

# Utility classes
from .utils.tick_store import TickStore
from .utils.fx_converter import DefaultAssetConverter
from .utils.conversion_subscriptions import ConversionSubscriptionManager

# Additional exceptions
from .utils.errors import PositionError, TimeoutError, ProtocolError, ConfigurationError

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
    # Debug utilities
    debug_mode_enabled,
    connection_debug_enabled,
    set_debug_mode,
    get_debug_status,
    log_calls,
)

# New utilities
from .utils.pip_value import calculate_pip_value
from .utils.position_sizer import size_from_risk, calculate_position_risk
from .utils.symbol_search import resolve_symbol, find_similar_symbols
from .utils.health import HealthStatus, get_health

# Optional integrations (only available if dependencies installed)
try:
    from .integrations import (
        BetterStackHandler,
        BetterStackConfig,
        setup_betterstack_logging,
        betterstack_enabled,
    )
except ImportError:
    BetterStackHandler = None  # type: ignore
    BetterStackConfig = None  # type: ignore
    setup_betterstack_logging = None  # type: ignore
    betterstack_enabled = lambda: False  # type: ignore

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
    "PositionError",
    "TimeoutError",
    "ProtocolError",
    "ConfigurationError",
    "OAuthHelper",
    
    # Account-related classes
    "FullAccountInfo",
    "CashFlowEntry",
    "CashFlowType",
    
    # Risk-related classes
    "LeverageTier",
    "DynamicLeverage",
    
    # Asset catalog
    "AssetCatalog",
    
    # Utility classes
    "TickStore",
    "DefaultAssetConverter",
    "ConversionSubscriptionManager",

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
    
    # Debug utilities
    "debug_mode_enabled",
    "connection_debug_enabled",
    "set_debug_mode",
    "get_debug_status",
    "log_calls",
    
    # New utilities
    "calculate_pip_value",
    "size_from_risk",
    "calculate_position_risk",
    "resolve_symbol",
    "find_similar_symbols",
    "HealthStatus",
    "get_health",
    
    # BetterStack integration (optional)
    "BetterStackHandler",
    "BetterStackConfig",
    "setup_betterstack_logging",
    "betterstack_enabled",
]
