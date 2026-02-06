"""
Abstract base transport interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional


class AsyncTransport(ABC):
    """Abstract transport interface for sending/receiving raw bytes.
    
    This provides a clean abstraction over the underlying transport mechanism
    (TCP, WebSocket, etc.), making the protocol layer transport-agnostic.
    """
    
    @abstractmethod
    async def connect(self, host: str, port: int, *, timeout: Optional[float] = None, ssl: object | None = None) -> None:
        """Establish connection to the server.
        
        Args:
            host: Server hostname or IP address
            port: Server port number
            timeout: Connection timeout in seconds
            
        Raises:
            ConnectionError: If connection fails
            TimeoutError: If connection timeout exceeded
        """
        pass
    
    @abstractmethod
    async def send(self, data: bytes) -> None:
        """Send raw bytes to the server.
        
        Args:
            data: Raw bytes to send
            
        Raises:
            ConnectionError: If not connected or send fails
        """
        pass
    
    @abstractmethod
    async def receive(self) -> AsyncIterator[bytes]:
        """Async iterator yielding received message frames.
        
        Yields:
            Complete message frames as bytes
            
        Raises:
            ConnectionError: If connection is lost
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close connection gracefully.
        
        This should clean up all resources and can be called multiple times.
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if transport is currently connected.
        
        Returns:
            True if connected, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def remote_address(self) -> Optional[tuple[str, int]]:
        """Get remote address if connected.
        
        Returns:
            Tuple of (host, port) or None if not connected
        """
        pass
