"""
Rate limiting utilities using token bucket algorithm.
"""

from __future__ import annotations

import asyncio
import time
from typing import Optional


class TokenBucketRateLimiter:
    """Token bucket rate limiter for async operations.
    
    This implements a token bucket algorithm that allows bursts up to
    the bucket capacity while maintaining an average rate.
    
    Attributes:
        rate: Maximum requests per second
        capacity: Bucket capacity (max burst size)
    """
    
    def __init__(self, rate: float, capacity: Optional[float] = None):
        """Initialize rate limiter.
        
        Args:
            rate: Maximum requests per second
            capacity: Maximum burst size (defaults to rate)
        """
        if rate <= 0:
            raise ValueError("Rate must be positive")
        
        self.rate = float(rate)
        self.capacity = float(capacity if capacity is not None else rate)
        self._tokens = self.capacity
        self._last_update = time.monotonic()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: float = 1.0, *, timeout: Optional[float] = None) -> bool:
        """Acquire tokens from the bucket.
        
        Args:
            tokens: Number of tokens to acquire
            timeout: Maximum time to wait (None = wait forever)
            
        Returns:
            True if tokens acquired, False if timeout
            
        Raises:
            asyncio.TimeoutError: If timeout exceeded
        """
        if tokens <= 0:
            return True
        
        deadline = None if timeout is None else time.monotonic() + timeout
        
        while True:
            async with self._lock:
                # Refill tokens based on elapsed time
                now = time.monotonic()
                elapsed = now - self._last_update
                self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
                self._last_update = now
                
                # Check if we have enough tokens
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True
                
                # Calculate wait time for next token
                tokens_needed = tokens - self._tokens
                wait_time = tokens_needed / self.rate
            
            # Check timeout
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise asyncio.TimeoutError("Rate limiter acquire timeout")
                wait_time = min(wait_time, remaining)
            
            # Wait for tokens to be available
            await asyncio.sleep(wait_time)
    
    async def try_acquire(self, tokens: float = 1.0) -> bool:
        """Try to acquire tokens without waiting.
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            True if tokens acquired, False otherwise
        """
        if tokens <= 0:
            return True
        
        async with self._lock:
            # Refill tokens
            now = time.monotonic()
            elapsed = now - self._last_update
            self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
            self._last_update = now
            
            # Check if we have enough tokens
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            
            return False
    
    @property
    def available_tokens(self) -> float:
        """Get number of currently available tokens."""
        now = time.monotonic()
        elapsed = now - self._last_update
        return min(self.capacity, self._tokens + elapsed * self.rate)
    
    async def reset(self):
        """Reset the rate limiter to full capacity."""
        async with self._lock:
            self._tokens = self.capacity
            self._last_update = time.monotonic()


class MultiRateLimiter:
    """Multiple rate limiters for different operation types.
    
    Useful when different operations have different rate limits
    (e.g., trading vs. historical data requests).
    """
    
    def __init__(self, limiters: dict[str, TokenBucketRateLimiter]):
        """Initialize with multiple named rate limiters.
        
        Args:
            limiters: Dictionary of limiter_name -> TokenBucketRateLimiter
        """
        self._limiters = limiters
    
    async def acquire(self, limiter_name: str, tokens: float = 1.0, *, timeout: Optional[float] = None) -> bool:
        """Acquire tokens from a specific limiter.
        
        Args:
            limiter_name: Name of the rate limiter to use
            tokens: Number of tokens to acquire
            timeout: Maximum time to wait
            
        Returns:
            True if tokens acquired
            
        Raises:
            KeyError: If limiter_name not found
            asyncio.TimeoutError: If timeout exceeded
        """
        limiter = self._limiters.get(limiter_name)
        if limiter is None:
            raise KeyError(f"Rate limiter not found: {limiter_name}")
        
        return await limiter.acquire(tokens, timeout=timeout)
    
    async def try_acquire(self, limiter_name: str, tokens: float = 1.0) -> bool:
        """Try to acquire tokens without waiting.
        
        Args:
            limiter_name: Name of the rate limiter to use
            tokens: Number of tokens to acquire
            
        Returns:
            True if tokens acquired
        """
        limiter = self._limiters.get(limiter_name)
        if limiter is None:
            raise KeyError(f"Rate limiter not found: {limiter_name}")
        
        return await limiter.try_acquire(tokens)
    
    def get_limiter(self, name: str) -> Optional[TokenBucketRateLimiter]:
        """Get a specific rate limiter by name."""
        return self._limiters.get(name)
    
    async def reset_all(self):
        """Reset all rate limiters."""
        for limiter in self._limiters.values():
            await limiter.reset()
