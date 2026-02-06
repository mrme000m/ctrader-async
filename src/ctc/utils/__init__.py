"""
Utility modules for cTrader async client.
"""

from .errors import (
    CTraderError,
    ConnectionError,
    AuthenticationError,
    TradingError,
    MarketClosedError,
    RateLimitError,
    SymbolNotFoundError,
    OrderError,
    PositionError,
    TimeoutError,
    ProtocolError,
    ConfigurationError,
)
from .rate_limiter import TokenBucketRateLimiter, MultiRateLimiter
from .reconnect import ReconnectManager, ReconnectConfig
from .events import EventBus, HookManager, HookContext
from .reliability import retry_async, RetryPolicy, CircuitBreaker
from .concurrency import gather_limited
from .normalization import normalize_order_update, normalize_position_update
from .model_bridge import (
    ModelEventBridge,
    NormalizedDeal,
    NormalizedExecutionError,
)
from .state_cache import TradingStateCacheUpdater
from .typed_events import (
    TickEvent,
    ExecutionEvent,
    ExecutionErrorEvent,
    OrderUpdateEvent,
    PositionUpdateEvent,
    DealEvent,
)
from .metrics import MetricsCollector, MetricsSnapshot
from .stream_registry import StreamRegistry
from .debug import connection_debug_enabled

__all__ = [
    # Errors
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
    
    # Rate limiting
    "TokenBucketRateLimiter",
    "MultiRateLimiter",
    
    # Reconnection
    "ReconnectManager",
    "ReconnectConfig",

    # Events / hooks
    "EventBus",
    "HookManager",
    "HookContext",

    # Reliability
    "retry_async",
    "RetryPolicy",
    "CircuitBreaker",
    "gather_limited",
    "normalize_order_update",
    "normalize_position_update",
    "ModelEventBridge",
    "NormalizedDeal",
    "NormalizedExecutionError",
    "TradingStateCacheUpdater",

    # Typed events
    "TickEvent",
    "ExecutionEvent",
    "ExecutionErrorEvent",
    "OrderUpdateEvent",
    "PositionUpdateEvent",
    "DealEvent",

    # Metrics
    "MetricsCollector",
    "MetricsSnapshot",

    # Stream recovery
    "StreamRegistry",

    # Debug flags
    "connection_debug_enabled",
]



