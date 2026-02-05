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
from .typed_events import (
    TickEvent,
    ExecutionEvent,
    ExecutionErrorEvent,
    OrderUpdateEvent,
    PositionUpdateEvent,
    DealEvent,
)

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

    # Typed events
    "TickEvent",
    "ExecutionEvent",
    "ExecutionErrorEvent",
    "OrderUpdateEvent",
    "PositionUpdateEvent",
    "DealEvent",
]
