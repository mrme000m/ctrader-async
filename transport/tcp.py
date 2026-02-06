"""
Pure asyncio TCP transport implementation.
"""

from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator, Optional

from .base import AsyncTransport
from ..utils.errors import ConnectionError as CTraderConnectionError

logger = logging.getLogger(__name__)

from ..utils.debug import connection_debug_enabled


class TCPTransport(AsyncTransport):
    """Pure asyncio TCP transport for cTrader protocol.
    
    This implementation uses asyncio.open_connection() for a clean,
    native async TCP connection without any Twisted dependencies.
    
    Example:
        >>> transport = TCPTransport()
        >>> await transport.connect("demo.ctraderapi.com", 5035)
        >>> await transport.send(b"...")
        >>> async for message in transport.receive():
        ...     print(f"Received: {len(message)} bytes")
        >>> await transport.close()
    """
    
    def __init__(self, *, message_max_size: int = 10 * 1024 * 1024):
        """Initialize TCP transport.
        
        Args:
            message_max_size: Maximum message size in bytes (default 10MB)
        """
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected = False
        self._remote_address: Optional[tuple[str, int]] = None
        self._message_max_size = message_max_size
        self._receive_task: Optional[asyncio.Task] = None
        self._closed = False
    
    async def connect(self, host: str, port: int, *, timeout: Optional[float] = None, ssl: object | None = None) -> None:
        """Establish TCP connection to the server.
        
        Args:
            host: Server hostname or IP address
            port: Server port number
            timeout: Connection timeout in seconds
            
        Raises:
            ConnectionError: If connection fails
            TimeoutError: If connection timeout exceeded
        """
        if self._connected:
            logger.warning("Already connected, closing existing connection")
            await self.close()
        
        try:
            if connection_debug_enabled():
                logger.info(f"Connecting to {host}:{port} (tls={bool(ssl)})...")
            else:
                logger.info(f"Connecting to {host}:{port}...")
            
            # Open TCP connection with optional timeout
            if timeout:
                self._reader, self._writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port, ssl=ssl, server_hostname=host if ssl else None),
                    timeout=timeout
                )
            else:
                self._reader, self._writer = await asyncio.open_connection(host, port, ssl=ssl, server_hostname=host if ssl else None)
            
            self._connected = True
            self._closed = False
            self._remote_address = (host, port)
            
            logger.info(f"Connected to {host}:{port}")
            
        except asyncio.TimeoutError as e:
            logger.error(f"TCP connect timeout to {host}:{port} after {timeout}s")
            raise asyncio.TimeoutError(f"Connection timeout after {timeout}s") from e
        except OSError as e:
            logger.error(f"TCP connect OS error to {host}:{port}: {e}")
            raise CTraderConnectionError(f"Failed to connect to {host}:{port}: {e}") from e
        except Exception as e:
            logger.error(f"TCP connect unexpected error to {host}:{port}: {e}", exc_info=True)
            raise CTraderConnectionError(f"Connection error: {e}") from e
    
    async def send(self, data: bytes) -> None:
        """Send raw bytes to the server.
        
        Args:
            data: Raw bytes to send (already framed with length prefix)
            
        Raises:
            ConnectionError: If not connected or send fails
        """
        if not self._connected or not self._writer:
            raise CTraderConnectionError("Not connected")
        
        if self._closed:
            raise CTraderConnectionError("Connection closed")
        
        try:
            self._writer.write(data)
            await self._writer.drain()
            
            logger.debug(f"Sent {len(data)} bytes")
            
        except ConnectionResetError as e:
            self._connected = False
            logger.error("TCP send failed: connection reset by peer")
            raise CTraderConnectionError("Connection reset by peer") from e
        except BrokenPipeError as e:
            self._connected = False
            logger.error("TCP send failed: broken pipe")
            raise CTraderConnectionError("Broken pipe") from e
        except Exception as e:
            self._connected = False
            logger.error(f"TCP send failed: {e}")
            raise CTraderConnectionError(f"Send error: {e}") from e
    
    async def receive(self) -> AsyncIterator[bytes]:
        """Async iterator yielding received message frames.
        
        The cTrader protocol frames messages with a 4-byte big-endian length prefix,
        followed by the protobuf message payload.
        
        Yields:
            Complete message payloads (without length prefix)
            
        Raises:
            ConnectionError: If connection is lost
        """
        if not self._connected or not self._reader:
            raise CTraderConnectionError("Not connected")
        
        try:
            while self._connected and not self._closed:
                # Read message length (4 bytes, big-endian)
                try:
                    length_bytes = await self._reader.readexactly(4)
                except asyncio.IncompleteReadError as e:
                    # Connection closed by server
                    if len(e.partial) == 0:
                        logger.info("Connection closed by server")
                        self._connected = False
                        break
                    raise CTraderConnectionError(
                        f"Incomplete length header: got {len(e.partial)} bytes"
                    ) from e
                
                # Parse message length
                msg_length = int.from_bytes(length_bytes, byteorder='big', signed=False)
                
                # Validate message size
                if msg_length <= 0:
                    raise CTraderConnectionError(f"Invalid message length: {msg_length}")
                
                if msg_length > self._message_max_size:
                    raise CTraderConnectionError(
                        f"Message too large: {msg_length} bytes (max: {self._message_max_size})"
                    )
                
                # Read message payload
                try:
                    payload = await self._reader.readexactly(msg_length)
                except asyncio.IncompleteReadError as e:
                    raise CTraderConnectionError(
                        f"Incomplete message: expected {msg_length}, got {len(e.partial)} bytes"
                    ) from e
                
                logger.debug(f"Received {len(payload)} bytes")
                
                yield payload
                
        except ConnectionResetError as e:
            self._connected = False
            raise CTraderConnectionError("Connection reset by peer") from e
        except Exception as e:
            self._connected = False
            if not self._closed:  # Don't raise if we're intentionally closing
                raise CTraderConnectionError(f"Receive error: {e}") from e
    
    async def close(self) -> None:
        """Close TCP connection gracefully.
        
        This can be called multiple times safely.
        """
        if self._closed:
            return
        
        self._closed = True
        self._connected = False
        
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception as e:
                logger.debug(f"Error closing writer: {e}")
        
        self._reader = None
        self._writer = None
        self._remote_address = None
        
        logger.info("Connection closed")
    
    def is_connected(self) -> bool:
        """Check if transport is currently connected.
        
        Returns:
            True if connected, False otherwise
        """
        return self._connected and not self._closed
    
    @property
    def remote_address(self) -> Optional[tuple[str, int]]:
        """Get remote address if connected.
        
        Returns:
            Tuple of (host, port) or None if not connected
        """
        return self._remote_address
    
    def __repr__(self) -> str:
        """String representation of transport."""
        status = "connected" if self.is_connected() else "disconnected"
        addr = f" to {self._remote_address[0]}:{self._remote_address[1]}" if self._remote_address else ""
        return f"<TCPTransport {status}{addr}>"
