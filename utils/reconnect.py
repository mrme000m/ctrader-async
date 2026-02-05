"""
Reconnection logic with exponential backoff.
"""

from __future__ import annotations

import asyncio
import random
from typing import Optional, Callable, Awaitable
from dataclasses import dataclass


@dataclass
class ReconnectConfig:
    """Configuration for reconnection behavior.
    
    Attributes:
        enabled: Whether reconnection is enabled
        max_attempts: Maximum number of reconnection attempts (0 = infinite)
        base_delay: Initial delay between attempts (seconds)
        max_delay: Maximum delay between attempts (seconds)
        exponential_base: Base for exponential backoff (typically 2)
        jitter: Whether to add random jitter to delays
        jitter_factor: Jitter randomization factor (0-1)
    """
    
    enabled: bool = True
    max_attempts: int = 10
    base_delay: float = 1.0
    max_delay: float = 300.0
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_factor: float = 0.2


class ReconnectManager:
    """Manage reconnection attempts with exponential backoff.
    
    Example:
        >>> async def connect():
        ...     # Connection logic
        ...     pass
        >>> 
        >>> manager = ReconnectManager(ReconnectConfig())
        >>> await manager.connect_with_retry(connect)
    """
    
    def __init__(self, config: ReconnectConfig):
        """Initialize reconnect manager.
        
        Args:
            config: Reconnection configuration
        """
        self.config = config
        self._attempts = 0
        self._connected = False
        self._reconnecting = False
        self._reconnect_task: Optional[asyncio.Task] = None
    
    @property
    def attempts(self) -> int:
        """Get number of reconnection attempts made."""
        return self._attempts
    
    @property
    def is_connected(self) -> bool:
        """Check if currently connected."""
        return self._connected
    
    @property
    def is_reconnecting(self) -> bool:
        """Check if currently attempting to reconnect."""
        return self._reconnecting
    
    def reset(self):
        """Reset reconnection state (call after successful connection)."""
        self._attempts = 0
        self._connected = True
        self._reconnecting = False
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number.
        
        Args:
            attempt: Attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        # Exponential backoff
        delay = min(
            self.config.base_delay * (self.config.exponential_base ** attempt),
            self.config.max_delay
        )
        
        # Add jitter if enabled
        if self.config.jitter:
            jitter_amount = delay * self.config.jitter_factor
            jitter = random.uniform(-jitter_amount, jitter_amount)
            delay = max(0.0, delay + jitter)
        
        return delay
    
    async def connect_with_retry(
        self,
        connect_func: Callable[[], Awaitable[None]],
        *,
        on_attempt: Optional[Callable[[int], Awaitable[None]]] = None,
        on_failure: Optional[Callable[[int, Exception], Awaitable[None]]] = None,
    ) -> bool:
        """Attempt connection with automatic retries.
        
        Args:
            connect_func: Async function that performs the connection
            on_attempt: Optional callback called before each attempt
            on_failure: Optional callback called after each failed attempt
            
        Returns:
            True if connected successfully, False if all attempts failed
        """
        if not self.config.enabled:
            await connect_func()
            self._connected = True
            return True
        
        self._attempts = 0
        self._reconnecting = True
        
        while True:
            # Check if we've exceeded max attempts
            if self.config.max_attempts > 0 and self._attempts >= self.config.max_attempts:
                self._reconnecting = False
                return False
            
            # Call attempt callback
            if on_attempt:
                await on_attempt(self._attempts)
            
            # Attempt connection
            try:
                await connect_func()
                self._connected = True
                self._reconnecting = False
                self._attempts = 0
                return True
            
            except Exception as e:
                self._attempts += 1
                
                # Call failure callback
                if on_failure:
                    await on_failure(self._attempts, e)
                
                # Check if we should retry
                if self.config.max_attempts > 0 and self._attempts >= self.config.max_attempts:
                    self._reconnecting = False
                    raise
                
                # Calculate and wait for backoff delay
                delay = self.calculate_delay(self._attempts - 1)
                await asyncio.sleep(delay)
    
    async def start_reconnect_loop(
        self,
        connect_func: Callable[[], Awaitable[None]],
        *,
        on_attempt: Optional[Callable[[int], Awaitable[None]]] = None,
        on_failure: Optional[Callable[[int, Exception], Awaitable[None]]] = None,
        on_success: Optional[Callable[[], Awaitable[None]]] = None,
    ):
        """Start a background reconnection loop.
        
        This is useful for maintaining persistent connections.
        
        Args:
            connect_func: Async function that performs the connection
            on_attempt: Optional callback called before each attempt
            on_failure: Optional callback called after each failed attempt
            on_success: Optional callback called after successful reconnection
        """
        if self._reconnect_task and not self._reconnect_task.done():
            return  # Already running
        
        async def reconnect_loop():
            while self.config.enabled:
                success = await self.connect_with_retry(
                    connect_func,
                    on_attempt=on_attempt,
                    on_failure=on_failure,
                )
                
                if success:
                    if on_success:
                        await on_success()
                    break
                
                # All attempts failed
                await asyncio.sleep(self.config.max_delay)
        
        self._reconnect_task = asyncio.create_task(reconnect_loop())
    
    async def stop_reconnect_loop(self):
        """Stop the background reconnection loop."""
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
        
        self._reconnecting = False
