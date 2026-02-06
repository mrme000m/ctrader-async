"""
Custom exceptions for cTrader async client.
"""

from __future__ import annotations
from typing import Optional


class CTraderError(Exception):
    """Base exception for all cTrader client errors."""
    
    def __init__(self, message: str, code: Optional[str] = None):
        """Initialize error.
        
        Args:
            message: Error message
            code: Optional error code
        """
        super().__init__(message)
        self.message = message
        self.code = code


class ConnectionError(CTraderError):
    """Connection-related errors."""
    pass


class AuthenticationError(CTraderError):
    """Authentication failures."""
    
    def __init__(self, message: str, code: Optional[str] = None, attempts: int = 0):
        """Initialize authentication error.
        
        Args:
            message: Error message
            code: Optional error code
            attempts: Number of authentication attempts made
        """
        super().__init__(message, code)
        self.attempts = attempts


class TradingError(CTraderError):
    """Trading operation errors."""
    
    def __init__(self, message: str, code: Optional[str] = None, description: Optional[str] = None):
        """Initialize trading error.
        
        Args:
            message: Error message
            code: Error code from server
            description: Detailed description from server
        """
        super().__init__(message, code)
        self.description = description


class MarketClosedError(TradingError):
    """Market is closed for trading."""
    
    def __init__(self, message: str = "Market is closed"):
        super().__init__(message, code="MARKET_CLOSED")


class RateLimitError(CTraderError):
    """Rate limit exceeded."""
    
    def __init__(self, message: str, retry_after: float = 1.0):
        """Initialize rate limit error.
        
        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
        """
        super().__init__(message, code="RATE_LIMIT")
        self.retry_after = retry_after


class SymbolNotFoundError(CTraderError):
    """Symbol not found in catalog."""
    
    def __init__(self, symbol: str):
        super().__init__(f"Symbol not found: {symbol}", code="SYMBOL_NOT_FOUND")
        self.symbol = symbol


class OrderError(TradingError):
    """Order-specific errors."""
    pass


class PositionError(TradingError):
    """Position-specific errors."""
    pass


class TimeoutError(CTraderError):
    """Operation timed out."""
    
    def __init__(self, message: str, timeout: float):
        super().__init__(message, code="TIMEOUT")
        self.timeout = timeout


class ProtocolError(CTraderError):
    """Protocol-level errors (malformed messages, etc.)."""
    pass


class ConfigurationError(CTraderError):
    """Configuration errors."""
    pass
