"""
High-level protocol handler combining transport, correlation, and dispatch.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, Any

from ..utils.events import EventBus

from ..transport import AsyncTransport, ProtocolFraming
from .correlation import RequestCorrelator
from .dispatcher import MessageDispatcher
from ..utils.errors import ProtocolError, ConnectionError as CTraderConnectionError

logger = logging.getLogger(__name__)


class ProtocolHandler:
    """High-level protocol handler for cTrader messages.
    
    This class combines:
    - Transport (TCP)
    - Message framing/encoding
    - Request/response correlation
    - Message dispatching
    
    It provides a clean interface for sending requests and receiving responses.
    
    Example:
        >>> handler = ProtocolHandler(transport)
        >>> await handler.start()
        >>> 
        >>> # Send request and wait for response
        >>> response = await handler.send_request(request, timeout=30.0)
        >>> 
        >>> # Register event handler
        >>> @handler.dispatcher.register(ProtoOASpotEvent().payloadType)
        >>> async def handle_tick(message):
        ...     print("Tick received")
        >>> 
        >>> await handler.stop()
    """
    
    def __init__(self, transport: AsyncTransport, *, config: Any | None = None):
        """Initialize protocol handler.
        
        Args:
            transport: Transport instance for sending/receiving
        """
        self.transport = transport
        self.correlator = RequestCorrelator()
        self.dispatcher = MessageDispatcher()
        self.events = EventBus()

        # Inbound processing pipeline (backpressure)
        self._config = config
        inbound_queue_size = getattr(config, "inbound_queue_size", 1000) if config else 1000
        self._drop_inbound_when_full = bool(getattr(config, "drop_inbound_when_full", False)) if config else False
        self._inbound_queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=inbound_queue_size)
        self._worker_count = int(getattr(config, "inbound_workers", 1)) if config else 1
        self._worker_tasks: list[asyncio.Task] = []

        self._receive_task: Optional[asyncio.Task] = None
        self._stopped = False
    
    async def start(self):
        """Start the protocol handler.
        
        This starts the correlator and message receive loop.
        """
        await self.correlator.start()

        self._stopped = False

        # Start worker tasks first so receive loop can enqueue immediately
        self._worker_tasks = [
            asyncio.create_task(self._worker_loop(i)) for i in range(max(1, self._worker_count))
        ]
        self._receive_task = asyncio.create_task(self._receive_loop())
        
        logger.info("Protocol handler started")
    
    async def stop(self):
        """Stop the protocol handler.
        
        This stops the receive loop and correlator.
        """
        self._stopped = True
        
        # Cancel receive task
        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        # Cancel workers
        for task in self._worker_tasks:
            if not task.done():
                task.cancel()
        for task in self._worker_tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._worker_tasks = []

        # Stop correlator
        await self.correlator.stop()
        
        logger.info("Protocol handler stopped")
    
    async def send_request(
        self,
        request: Any,
        *,
        timeout: float = 30.0,
        request_type: Optional[str] = None,
        hooks: Any | None = None,
    ) -> Any:
        """Send a request and wait for response.
        
        This is the primary method for making correlated requests.
        
        Args:
            request: Protobuf request message
            timeout: Request timeout in seconds
            request_type: Optional request type name for debugging
            
        Returns:
            Response payload (already extracted from envelope)
            
        Raises:
            TimeoutError: If request times out
            ConnectionError: If connection fails
            
        Example:
            >>> req = ProtoOAApplicationAuthReq()
            >>> req.clientId = "12345"
            >>> response = await handler.send_request(req, timeout=30.0)
        """
        if not self.transport.is_connected():
            raise CTraderConnectionError("Transport not connected")
        
        if hooks is not None:
            # Hook point for request shaping / risk gates
            await hooks.run(
                "protocol.pre_send_request",
                request=request,
                request_type=request_type or type(request).__name__,
                timeout=timeout,
            )

        # Create pending request
        msg_id, future = await self.correlator.create_request(
            timeout=timeout,
            request_type=request_type or type(request).__name__
        )
        
        # Encode and send message
        try:
            data = ProtocolFraming.encode(request, client_msg_id=msg_id)
            await self.transport.send(data)

            if hooks is not None:
                await hooks.run(
                    "protocol.post_send_request",
                    request=request,
                    request_type=request_type or type(request).__name__,
                    client_msg_id=msg_id,
                    bytes_sent=len(data),
                )

            logger.debug(f"Sent request: {type(request).__name__}, id={msg_id}")
        
        except Exception as e:
            # Remove pending request if send fails
            await self.correlator.reject_request(msg_id, e)
            raise
        
        # Wait for response
        try:
            response = await asyncio.wait_for(future, timeout=timeout)
            if hooks is not None:
                await hooks.run(
                    "protocol.post_response",
                    request=request,
                    request_type=request_type or type(request).__name__,
                    response=response,
                    client_msg_id=msg_id,
                )
            return response
        
        except asyncio.TimeoutError:
            logger.warning(f"Request timed out: {type(request).__name__}, id={msg_id}")
            raise
    
    async def send_message(self, message: Any):
        """Send a message without expecting a response.
        
        This is used for messages that don't require correlation
        (e.g., heartbeats).
        
        Args:
            message: Protobuf message
            
        Raises:
            ConnectionError: If connection fails
        """
        if not self.transport.is_connected():
            raise CTraderConnectionError("Transport not connected")
        
        data = ProtocolFraming.encode(message)
        await self.transport.send(data)
        
        logger.debug(f"Sent message: {type(message).__name__}")
    
    async def _receive_loop(self):
        """Background task to receive and process messages.
        
        This loops continuously, receiving messages from the transport
        and either resolving correlated requests or dispatching to handlers.
        """
        logger.debug("Receive loop started")
        
        try:
            async for message_bytes in self.transport.receive():
                if self._stopped:
                    break

                if self._drop_inbound_when_full:
                    try:
                        self._inbound_queue.put_nowait(message_bytes)
                    except asyncio.QueueFull:
                        # Drop oldest to keep more recent messages
                        try:
                            _ = self._inbound_queue.get_nowait()
                        except asyncio.QueueEmpty:
                            pass
                        try:
                            self._inbound_queue.put_nowait(message_bytes)
                        except asyncio.QueueFull:
                            pass
                else:
                    await self._inbound_queue.put(message_bytes)
        
        except asyncio.CancelledError:
            logger.debug("Receive loop cancelled")
            raise
        
        except Exception as e:
            logger.error(f"Receive loop error: {e}", exc_info=True)
            if not self._stopped:
                raise
    
    async def _worker_loop(self, worker_id: int):
        """Process inbound messages from the queue."""
        logger.debug(f"Inbound worker started: {worker_id}")
        try:
            while not self._stopped:
                message_bytes = await self._inbound_queue.get()
                try:
                    await self._handle_message(message_bytes)
                finally:
                    self._inbound_queue.task_done()
        except asyncio.CancelledError:
            raise

    async def _handle_message(self, message_bytes: bytes):
        """Handle a received message.
        
        Args:
            message_bytes: Raw message bytes (without length prefix)
        """
        try:
            # Decode ProtoMessage envelope
            proto_msg = ProtocolFraming.decode(message_bytes)
            
            # Check if this is a correlated response
            msg_id = getattr(proto_msg, 'clientMsgId', None)
            
            if msg_id:
                # Extract payload and resolve the pending request
                payload = ProtocolFraming.extract_payload(proto_msg)
                resolved = await self.correlator.resolve_response(msg_id, payload)
                
                if resolved:
                    logger.debug(f"Resolved correlated response: id={msg_id}")
                    # Don't dispatch correlated responses to handlers
                    return
            
            # Dispatch non-correlated messages (or unmatched responses) to handlers
            await self.dispatcher.dispatch(proto_msg)
            await self.events.emit("protobuf.envelope", proto_msg)
        
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
    
    @property
    def is_running(self) -> bool:
        """Check if protocol handler is running.
        
        Returns:
            True if running, False otherwise
        """
        return not self._stopped and self._receive_task is not None
    
    @property
    def pending_requests(self) -> int:
        """Get number of pending requests.
        
        Returns:
            Number of pending requests
        """
        return self.correlator.get_pending_count()
    
    def __repr__(self) -> str:
        """String representation."""
        status = "running" if self.is_running else "stopped"
        return f"<ProtocolHandler {status}, pending={self.pending_requests}>"
