"""
WebSocket transport implementation.

Provides WebSocket connectivity as an alternative to direct TCP for:
- Firewall-friendly environments
- Proxy/tunnel scenarios
- Browser-based trading applications
- Cloud deployment flexibility

Note: cTrader's native protocol is TCP with protobuf messages.
This WebSocket transport wraps the same protocol for compatibility.
"""

from __future__ import annotations

import asyncio
import struct
import logging
from typing import AsyncIterator, Optional
from contextlib import asynccontextmanager

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WebSocketClientProtocol = None

from .base import AsyncTransport

logger = logging.getLogger(__name__)


class AsyncWebSocketTransport(AsyncTransport):
    """WebSocket transport implementation.
    
    Wraps the cTrader protobuf protocol over WebSocket for enhanced
    connectivity options. Maintains the same length-prefixed binary
    message format as TCP transport.
    
    This is particularly useful for:
    - Environments with restrictive firewalls
    - Web-based trading applications
    - Proxy/reverse proxy scenarios
    - Cloud deployments behind load balancers
    
    Example:
        >>> transport = AsyncWebSocketTransport()
        >>> await transport.connect("wss://demo.ctraderapi.com", 5035)
        >>> await transport.send(message_bytes)
        >>> async for data in transport.receive():
        ...     process(data)
    """
    
    def __init__(self, *, ping_interval: float = 20.0, ping_timeout: float = 10.0):
        """Initialize WebSocket transport.
        
        Args:
            ping_interval: WebSocket ping interval in seconds (default: 20)
            ping_timeout: WebSocket ping timeout in seconds (default: 10)
        """
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError(
                "websockets library is required for WebSocket transport. "
                "Install it with: pip install websockets"
            )
        
        self._websocket: Optional[WebSocketClientProtocol] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._queue: asyncio.Queue[bytes] = asyncio.Queue()
        self._connected = False
        self._host: Optional[str] = None
        self._port: Optional[int] = None
        self._ping_interval = ping_interval
        self._ping_timeout = ping_timeout
        self._close_event = asyncio.Event()
    
    async def connect(
        self,
        host: str,
        port: int,
        *,
        timeout: Optional[float] = None,
        ssl: object | None = None,
        extra_headers: Optional[dict] = None,
        subprotocols: Optional[list[str]] = None
    ) -> None:
        """Establish WebSocket connection to server.
        
        Args:
            host: Server hostname or IP address
            port: Server port number
            timeout: Connection timeout in seconds
            ssl: SSL context (if None, inferred from ws:// vs wss://)
            extra_headers: Additional HTTP headers for WebSocket handshake
            subprotocols: WebSocket subprotocols to negotiate
            
        Raises:
            ConnectionError: If connection fails
            TimeoutError: If connection timeout exceeded
        """
        if self._connected:
            raise ConnectionError("Already connected")
        
        # Build WebSocket URL
        # Determine protocol based on SSL or port
        if ssl is not None or port == 443 or host.startswith("wss://"):
            protocol = "wss"
        elif host.startswith("ws://"):
            protocol = "ws"
        else:
            # Default to secure WebSocket
            protocol = "wss"
        
        # Clean host if it includes protocol
        clean_host = host.replace("ws://", "").replace("wss://", "")
        
        uri = f"{protocol}://{clean_host}:{port}"
        
        logger.info(f"Connecting to WebSocket: {uri}")
        
        try:
            # Connect to WebSocket
            self._websocket = await asyncio.wait_for(
                websockets.connect(
                    uri,
                    ssl=ssl,
                    extra_headers=extra_headers,
                    subprotocols=subprotocols,
                    ping_interval=self._ping_interval,
                    ping_timeout=self._ping_timeout,
                    # Use binary frames for protobuf messages
                    # This is critical for proper message handling
                    max_size=10 * 1024 * 1024,  # 10MB max message size
                ),
                timeout=timeout
            )
            
            self._host = clean_host
            self._port = port
            self._connected = True
            self._close_event.clear()
            
            # Start receive task
            self._receive_task = asyncio.create_task(self._receive_loop())
            
            logger.info(f"WebSocket connected to {uri}")
        
        except asyncio.TimeoutError:
            raise TimeoutError(f"WebSocket connection to {uri} timed out")
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}", exc_info=True)
            raise ConnectionError(f"Failed to connect to {uri}: {e}")
    
    async def send(self, data: bytes) -> None:
        """Send raw bytes over WebSocket.
        
        Frames the message with a 4-byte length header (big-endian)
        to match the TCP protocol format.
        
        Args:
            data: Raw bytes to send
            
        Raises:
            ConnectionError: If not connected or send fails
        """
        if not self._connected or self._websocket is None:
            raise ConnectionError("Not connected")
        
        try:
            # Frame message with length header (4 bytes, big-endian)
            # This matches the TCP Int32StringReceiver protocol
            length = len(data)
            frame = struct.pack(">I", length) + data
            
            # Send as binary WebSocket frame
            await self._websocket.send(frame)
            
            logger.debug(f"Sent {length} bytes over WebSocket")
        
        except websockets.exceptions.ConnectionClosed as e:
            self._connected = False
            raise ConnectionError(f"WebSocket connection closed: {e}")
        except Exception as e:
            logger.error(f"WebSocket send failed: {e}", exc_info=True)
            raise ConnectionError(f"Failed to send data: {e}")
    
    async def _receive_loop(self):
        """Background task to receive WebSocket messages."""
        try:
            while self._connected and self._websocket:
                try:
                    # Receive binary WebSocket frame
                    frame = await self._websocket.recv()
                    
                    if isinstance(frame, str):
                        logger.warning("Received text frame, expected binary")
                        continue
                    
                    # Process length-prefixed messages
                    offset = 0
                    while offset < len(frame):
                        # Check if we have enough bytes for length header
                        if len(frame) - offset < 4:
                            logger.warning("Incomplete length header in frame")
                            break
                        
                        # Read message length (4 bytes, big-endian)
                        msg_length = struct.unpack(">I", frame[offset:offset+4])[0]
                        offset += 4
                        
                        # Check if we have the complete message
                        if len(frame) - offset < msg_length:
                            logger.warning(f"Incomplete message: expected {msg_length}, got {len(frame)-offset}")
                            break
                        
                        # Extract message
                        message = frame[offset:offset+msg_length]
                        offset += msg_length
                        
                        # Queue for retrieval
                        await self._queue.put(message)
                        logger.debug(f"Received {msg_length} bytes over WebSocket")
                
                except websockets.exceptions.ConnectionClosed:
                    logger.info("WebSocket connection closed by server")
                    self._connected = False
                    break
                except Exception as e:
                    logger.error(f"Error in WebSocket receive loop: {e}", exc_info=True)
                    self._connected = False
                    break
        
        finally:
            self._close_event.set()
    
    async def receive(self) -> AsyncIterator[bytes]:
        """Async iterator yielding received message frames.
        
        Yields:
            Complete message frames as bytes (length header removed)
            
        Raises:
            ConnectionError: If connection is lost
        """
        while self._connected or not self._queue.empty():
            try:
                # Try to get message with timeout
                message = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=1.0
                )
                yield message
            except asyncio.TimeoutError:
                # Check if still connected
                if not self._connected and self._queue.empty():
                    break
                continue
            except Exception as e:
                logger.error(f"Error receiving from WebSocket: {e}")
                break
        
        if not self._connected:
            raise ConnectionError("WebSocket connection lost")
    
    async def close(self) -> None:
        """Close WebSocket connection gracefully."""
        if not self._connected:
            return
        
        logger.info("Closing WebSocket connection")
        self._connected = False
        
        # Cancel receive task
        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        
        # Close WebSocket
        if self._websocket:
            try:
                await self._websocket.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket: {e}")
        
        # Wait for close to complete
        try:
            await asyncio.wait_for(self._close_event.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("WebSocket close timeout")
        
        self._websocket = None
        self._host = None
        self._port = None
        
        logger.info("WebSocket closed")
    
    def is_connected(self) -> bool:
        """Check if WebSocket is currently connected.
        
        Returns:
            True if connected, False otherwise
        """
        return self._connected and self._websocket is not None
    
    @property
    def remote_address(self) -> Optional[tuple[str, int]]:
        """Get remote address if connected.
        
        Returns:
            Tuple of (host, port) or None if not connected
        """
        if self._connected and self._host and self._port:
            return (self._host, self._port)
        return None


@asynccontextmanager
async def websocket_transport(
    host: str,
    port: int,
    *,
    timeout: Optional[float] = None,
    ping_interval: float = 20.0,
    ping_timeout: float = 10.0
):
    """Context manager for WebSocket transport lifecycle.
    
    Example:
        >>> async with websocket_transport("demo.ctraderapi.com", 5035) as transport:
        ...     await transport.send(data)
        ...     async for msg in transport.receive():
        ...         process(msg)
    """
    transport = AsyncWebSocketTransport(
        ping_interval=ping_interval,
        ping_timeout=ping_timeout
    )
    try:
        await transport.connect(host, port, timeout=timeout)
        yield transport
    finally:
        await transport.close()
