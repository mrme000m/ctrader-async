"""
Request/response correlation with timeout management.
"""

from __future__ import annotations

import asyncio
import uuid
import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PendingRequest:
    """A pending request awaiting response.
    
    Attributes:
        future: Asyncio future to resolve when response arrives
        created_at: When the request was created
        timeout: Timeout in seconds
        request_type: Type of request (for debugging)
    """
    
    future: asyncio.Future
    created_at_monotonic: float
    timeout: float
    request_type: Optional[str] = None


class RequestCorrelator:
    """Manage request/response correlation using client message IDs.
    
    This class handles:
    - Generating unique client message IDs
    - Tracking pending requests
    - Resolving futures when responses arrive
    - Cleaning up timed-out requests
    
    Example:
        >>> correlator = RequestCorrelator()
        >>> await correlator.start()
        >>> 
        >>> # Send request and wait for response
        >>> msg_id, future = correlator.create_request(timeout=30.0)
        >>> await transport.send(encode_message(request, msg_id))
        >>> response = await future
        >>> 
        >>> await correlator.stop()
    """
    
    def __init__(self, *, cleanup_interval: float = 5.0):
        """Initialize request correlator.
        
        Args:
            cleanup_interval: Interval for cleanup task (seconds)
        """
        self._pending: Dict[str, PendingRequest] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_interval = cleanup_interval
        self._stopped = False
    
    async def start(self):
        """Start background cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            logger.warning("Cleanup task already running")
            return
        
        self._stopped = False
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.debug("Request correlator started")
    
    async def stop(self):
        """Stop cleanup task and cancel all pending requests."""
        self._stopped = True
        
        # Cancel cleanup task
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Cancel all pending requests
        async with self._lock:
            for msg_id, pending in self._pending.items():
                if not pending.future.done():
                    pending.future.cancel()
            
            self._pending.clear()
        
        logger.debug("Request correlator stopped")
    
    async def create_request(
        self,
        timeout: float = 30.0,
        request_type: Optional[str] = None
    ) -> tuple[str, asyncio.Future]:
        """Create a new pending request.
        
        Args:
            timeout: Request timeout in seconds
            request_type: Optional request type name for debugging
            
        Returns:
            Tuple of (client_msg_id, future)
            
        Example:
            >>> msg_id, future = await correlator.create_request(timeout=30.0)
            >>> await send_request(msg_id)
            >>> response = await asyncio.wait_for(future, timeout=30.0)
        """
        msg_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        future: asyncio.Future = loop.create_future()

        pending = PendingRequest(
            future=future,
            created_at_monotonic=time.monotonic(),
            timeout=timeout,
            request_type=request_type,
        )

        async with self._lock:
            self._pending[msg_id] = pending
        
        logger.debug(
            f"Created request: id={msg_id}, type={request_type}, timeout={timeout}s"
        )
        
        return msg_id, future
    
    async def resolve_response(self, msg_id: str, response: Any) -> bool:
        """Resolve a pending request with a response.

        Args:
            msg_id: Client message ID
            response: Response payload

        Returns:
            True if request was found and resolved, False otherwise
        """
        async with self._lock:
            pending = self._pending.pop(msg_id, None)

        if pending is None:
            logger.warning(f"No pending request found for msg_id: {msg_id}")
            return False
        
        if pending.future.done():
            logger.warning(f"Future already resolved for msg_id: {msg_id}")
            return False
        
        pending.future.set_result(response)
        
        elapsed = time.monotonic() - pending.created_at_monotonic
        logger.debug(
            f"Resolved request: id={msg_id}, "
            f"type={pending.request_type}, elapsed={elapsed:.2f}s"
        )
        
        return True
    
    async def reject_request(self, msg_id: str, error: Exception) -> bool:
        """Reject a pending request with an error.

        Args:
            msg_id: Client message ID
            error: Exception to set on the future

        Returns:
            True if request was found and rejected, False otherwise
        """
        async with self._lock:
            pending = self._pending.pop(msg_id, None)

        if pending is None:
            logger.warning(f"No pending request found for msg_id: {msg_id}")
            return False
        
        if pending.future.done():
            logger.warning(f"Future already resolved for msg_id: {msg_id}")
            return False
        
        pending.future.set_exception(error)
        
        logger.debug(f"Rejected request: id={msg_id}, error={error}")
        
        return True
    
    def get_pending_count(self) -> int:
        """Get number of pending requests.
        
        Returns:
            Number of pending requests
        """
        return len(self._pending)
    
    async def _cleanup_loop(self):
        """Background task to clean up timed-out requests."""
        logger.debug("Cleanup loop started")
        
        try:
            while not self._stopped:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_timed_out()
        except asyncio.CancelledError:
            logger.debug("Cleanup loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Cleanup loop error: {e}", exc_info=True)
    
    async def _cleanup_timed_out(self):
        """Clean up timed-out requests."""
        now = time.monotonic()
        timed_out: list[tuple[str, float, Optional[str]]] = []

        async with self._lock:
            for msg_id, pending in list(self._pending.items()):
                elapsed = now - pending.created_at_monotonic
                if elapsed > pending.timeout:
                    # Pop under the lock so resolve_response can't win the race.
                    self._pending.pop(msg_id, None)
                    timed_out.append((msg_id, pending))

        # Reject timed-out requests outside the lock
        for msg_id, pending in timed_out:
            if pending.future.done():
                continue

            error = asyncio.TimeoutError(
                f"Request timed out after {pending.timeout}s (type={pending.request_type})"
            )
            try:
                pending.future.set_exception(error)
            except Exception:
                # best-effort: future might already be resolved/cancelled
                pass

            logger.warning(
                f"Request timed out: id={msg_id}, type={pending.request_type}, timeout={pending.timeout}s"
            )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<RequestCorrelator pending={len(self._pending)}>"
