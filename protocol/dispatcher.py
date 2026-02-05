"""
Message dispatcher for routing incoming messages to handlers.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Callable, Dict, List, Any, Awaitable, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


HandlerFunc = Callable[[Any], Awaitable[None] | None]

# Internal representation: (priority, handler)
_PrioritizedHandler = Tuple[int, HandlerFunc]


class MessageDispatcher:
    """Route incoming messages to registered handlers based on payload type.
    
    Handlers can be registered for specific message types and will be
    called asynchronously when messages of that type arrive.
    
    Example:
        >>> dispatcher = MessageDispatcher()
        >>> 
        >>> @dispatcher.register(ProtoOASpotEvent().payloadType)
        >>> async def handle_tick(message):
        ...     tick = extract_payload(message)
        ...     print(f"Tick: {tick.bid}/{tick.ask}")
        >>> 
        >>> await dispatcher.dispatch(incoming_message)
    """
    
    def __init__(self):
        """Initialize message dispatcher."""
        self._handlers: Dict[int, List[_PrioritizedHandler]] = defaultdict(list)
        self._default_handlers: List[_PrioritizedHandler] = []
    
    def register(
        self,
        payload_type: int,
        handler: HandlerFunc | None = None,
        *,
        priority: int = 0
    ):
        """Register a handler for a specific message type.
        
        Args:
            payload_type: Protobuf payload type ID
            handler: Handler function (sync or async)
            priority: Handler priority (higher = earlier, default=0)
            
        Example:
            >>> def handle_execution(msg):
            ...     print("Execution event")
            >>> dispatcher.register(
            ...     ProtoOAExecutionEvent().payloadType,
            ...     handle_execution
            ... )
        """
        # Support decorator usage:
        #
        #   @dispatcher.register(payload_type)
        #   async def handler(msg): ...
        if handler is None:
            def _decorator(h: HandlerFunc) -> HandlerFunc:
                self.register(payload_type, h, priority=priority)
                return h

            return _decorator

        self._handlers[payload_type].append((int(priority), handler))
        # Keep stable ordering within same priority.
        self._handlers[payload_type].sort(key=lambda it: it[0], reverse=True)
        logger.debug(f"Registered handler for payload_type={payload_type}, priority={priority}")
        return None
    
    def register_default(self, handler: HandlerFunc | None = None, *, priority: int = 0):
        """Register a default handler for unhandled message types.
        
        Args:
            handler: Handler function (sync or async)
            
        Example:
            >>> @dispatcher.register_default
            >>> def log_unhandled(msg):
            ...     print(f"Unhandled message type: {msg.payloadType}")
        """
        if handler is None:
            def _decorator(h: HandlerFunc) -> HandlerFunc:
                self.register_default(h, priority=priority)
                return h

            return _decorator

        self._default_handlers.append((int(priority), handler))
        self._default_handlers.sort(key=lambda it: it[0], reverse=True)
        logger.debug(f"Registered default handler, priority={priority}")
        return None
    
    def unregister(self, payload_type: int, handler: HandlerFunc):
        """Unregister a specific handler.
        
        Args:
            payload_type: Protobuf payload type ID
            handler: Handler function to remove
        """
        entries = self._handlers.get(payload_type, [])
        for entry in list(entries):
            if entry[1] is handler:
                entries.remove(entry)
        if not entries and payload_type in self._handlers:
            self._handlers.pop(payload_type, None)
        logger.debug(f"Unregistered handler for payload_type={payload_type}")
    
    def clear_handlers(self, payload_type: Optional[int] = None):
        """Clear handlers for a specific type or all handlers.
        
        Args:
            payload_type: Type to clear (None = clear all)
        """
        if payload_type is None:
            self._handlers.clear()
            self._default_handlers.clear()
            logger.debug("Cleared all handlers")
        else:
            self._handlers[payload_type].clear()
            logger.debug(f"Cleared handlers for payload_type={payload_type}")
    
    async def dispatch(self, message: Any):
        """Dispatch a message to all registered handlers.
        
        Args:
            message: Protobuf message (ProtoMessage envelope)
            
        Example:
            >>> proto_msg = decode_message(data)
            >>> await dispatcher.dispatch(proto_msg)
        """
        payload_type = message.payloadType
        
        # Get handlers for this message type
        handlers = self._handlers.get(payload_type, [])
        
        if not handlers:
            # Use default handlers if no specific handlers registered
            handlers = self._default_handlers
            
            if not handlers:
                logger.debug(f"No handlers for payload_type={payload_type}")
                return
        
        # Dispatch to all handlers concurrently
        tasks = []
        for _prio, handler in handlers:
            task = self._safe_call(handler, message, payload_type)
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _safe_call(
        self,
        handler: HandlerFunc,
        message: Any,
        payload_type: int
    ):
        """Call a handler with error handling.
        
        Args:
            handler: Handler function
            message: Message to pass to handler
            payload_type: Message type (for logging)
        """
        try:
            result = handler(message)
            
            # Handle both sync and async handlers
            if asyncio.iscoroutine(result):
                await result
        
        except asyncio.CancelledError:
            # Re-raise cancellation
            raise
        
        except Exception as e:
            logger.error(
                f"Handler error for payload_type={payload_type}: {e}",
                exc_info=True
            )
    
    def get_handler_count(self, payload_type: Optional[int] = None) -> int:
        """Get number of registered handlers.
        
        Args:
            payload_type: Specific type (None = total count)
            
        Returns:
            Number of handlers
        """
        if payload_type is None:
            return sum(len(handlers) for handlers in self._handlers.values()) + len(self._default_handlers)
        else:
            return len(self._handlers.get(payload_type, []))
    
    def __repr__(self) -> str:
        """String representation."""
        total_handlers = self.get_handler_count()
        return f"<MessageDispatcher handlers={total_handlers}>"
