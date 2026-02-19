"""Runtime debug flags and utilities controlled via environment variables.

These utilities enable enhanced diagnostics and debugging capabilities
without requiring code changes. Features are opt-in via environment variables.

Environment Variables:
    CTRADER_DEBUG: Enable comprehensive debug mode
    CTRADER_CONNECTION_DEBUG: Emit more connection/reconnect logs at INFO/WARNING
    CTRADER_PROTOCOL_DEBUG: Log all protobuf messages (very verbose)
    CTRADER_LOG_CALLS: Log all API calls with timing
    CTRADER_TRACE_EXCEPTIONS: Capture full stack traces for all exceptions

Quick Reference:
    >>> from ctc.utils.debug import debug_mode_enabled, set_debug_mode
    >>> 
    >>> # Check if debug mode is enabled
    >>> if debug_mode_enabled():
    ...     print("Debug mode is active")
    >>> 
    >>> # Enable debug mode programmatically
    >>> set_debug_mode(True)
"""

from __future__ import annotations

import os
import sys
import functools
import logging
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Callable, Optional, TypeVar
from functools import lru_cache

# Type variable for generic function wrapper
F = TypeVar("F", bound=Callable[..., Any])

logger = logging.getLogger(__name__)


def _is_truthy(value: str | None) -> bool:
    """Check if a string value is truthy.
    
    Truthy values: 1, true, yes, y, on, enabled (case-insensitive).
    """
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on", "enabled"}


# ============================================================================
# Debug Mode Flags
# ============================================================================

@lru_cache(maxsize=1)
def debug_mode_enabled() -> bool:
    """Check if comprehensive debug mode is enabled.
    
    Returns:
        True if CTRADER_DEBUG environment variable is set to a truthy value.
    """
    return _is_truthy(os.getenv("CTRADER_DEBUG"))


@lru_cache(maxsize=1)
def connection_debug_enabled() -> bool:
    """Check if connection debug logging is enabled.
    
    When enabled, connection/reconnect logs are emitted at INFO/WARNING
    instead of DEBUG level for better visibility.
    
    Returns:
        True if CTRADER_CONNECTION_DEBUG is truthy.
    """
    return _is_truthy(os.getenv("CTRADER_CONNECTION_DEBUG"))


@lru_cache(maxsize=1)
def protocol_debug_enabled() -> bool:
    """Check if protocol message debugging is enabled.
    
    When enabled, all protobuf messages are logged (very verbose).
    
    Returns:
        True if CTRADER_PROTOCOL_DEBUG is truthy.
    """
    return _is_truthy(os.getenv("CTRADER_PROTOCOL_DEBUG"))


@lru_cache(maxsize=1)
def log_calls_enabled() -> bool:
    """Check if API call logging is enabled.
    
    When enabled, all API calls are logged with timing information.
    
    Returns:
        True if CTRADER_LOG_CALLS is truthy.
    """
    return _is_truthy(os.getenv("CTRADER_LOG_CALLS"))


@lru_cache(maxsize=1)
def trace_exceptions_enabled() -> bool:
    """Check if full exception tracing is enabled.
    
    When enabled, full stack traces are captured for all exceptions.
    
    Returns:
        True if CTRADER_TRACE_EXCEPTIONS is truthy.
    """
    return _is_truthy(os.getenv("CTRADER_TRACE_EXCEPTIONS"))


# ============================================================================
# Debug Mode Management
# ============================================================================

def set_debug_mode(enabled: bool, *, include_connection: bool = True) -> None:
    """Enable or disable debug mode at runtime.
    
    This function updates the internal debug state and configures
    logging levels appropriately.
    
    Args:
        enabled: Whether to enable debug mode
        include_connection: Also enable connection debug logging
        
    Example:
        >>> set_debug_mode(True)  # Enable all debug features
        >>> set_debug_mode(False)  # Disable debug mode
    """
    # Clear the lru_cache for debug mode checks
    debug_mode_enabled.cache_clear()
    connection_debug_enabled.cache_clear()
    
    # Set environment variable for this process
    if enabled:
        os.environ["CTRADER_DEBUG"] = "1"
        if include_connection:
            os.environ["CTRADER_CONNECTION_DEBUG"] = "1"
    else:
        os.environ.pop("CTRADER_DEBUG", None)
        os.environ.pop("CTRADER_CONNECTION_DEBUG", None)
    
    # Update logging level
    root_logger = logging.getLogger()
    if enabled:
        if root_logger.level > logging.DEBUG:
            root_logger.setLevel(logging.DEBUG)
        logging.getLogger("ctc").setLevel(logging.DEBUG)
        logger.info("Debug mode enabled")
    else:
        logger.info("Debug mode disabled")


def get_debug_status() -> dict[str, bool]:
    """Get current debug configuration status.
    
    Returns:
        Dictionary with all debug flags and their current values.
        
    Example:
        >>> status = get_debug_status()
        >>> print(f"Debug mode: {status['debug_mode']}")
        >>> print(f"Connection debug: {status['connection_debug']}")
    """
    return {
        "debug_mode": debug_mode_enabled(),
        "connection_debug": connection_debug_enabled(),
        "protocol_debug": protocol_debug_enabled(),
        "log_calls": log_calls_enabled(),
        "trace_exceptions": trace_exceptions_enabled(),
    }


# ============================================================================
# Debugging Decorators
# ============================================================================

def log_calls(
    level: int = logging.DEBUG,
    log_args: bool = False,
    log_result: bool = False,
    log_exceptions: bool = True
) -> Callable[[F], F]:
    """Decorator to log function calls with timing.
    
    Args:
        level: Logging level for the call log
        log_args: Whether to log function arguments
        log_result: Whether to log function return value
        log_exceptions: Whether to log exceptions
        
    Returns:
        Decorated function
        
    Example:
        >>> @log_calls(log_args=True)
        ... async def connect():
        ...     await transport.connect()
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            if not log_calls_enabled() and not debug_mode_enabled():
                return await func(*args, **kwargs)
            
            func_name = func.__qualname__
            start_time = time.monotonic()
            
            # Build log message
            args_str = ""
            if log_args:
                args_repr = [repr(a) for a in args]
                kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
                args_str = f"({', '.join(args_repr + kwargs_repr)})"
            
            logger.log(level, f"Call: {func_name}{args_str}")
            
            try:
                result = await func(*args, **kwargs)
                elapsed = time.monotonic() - start_time
                
                result_str = ""
                if log_result:
                    result_str = f" -> {result!r}"
                
                logger.log(level, f"Return: {func_name} in {elapsed:.3f}s{result_str}")
                return result
                
            except Exception as e:
                elapsed = time.monotonic() - start_time
                if log_exceptions:
                    logger.log(
                        logging.ERROR,
                        f"Exception in {func_name} after {elapsed:.3f}s: {e}",
                        exc_info=trace_exceptions_enabled()
                    )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            if not log_calls_enabled() and not debug_mode_enabled():
                return func(*args, **kwargs)
            
            func_name = func.__qualname__
            start_time = time.monotonic()
            
            args_str = ""
            if log_args:
                args_repr = [repr(a) for a in args]
                kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
                args_str = f"({', '.join(args_repr + kwargs_repr)})"
            
            logger.log(level, f"Call: {func_name}{args_str}")
            
            try:
                result = func(*args, **kwargs)
                elapsed = time.monotonic() - start_time
                
                result_str = ""
                if log_result:
                    result_str = f" -> {result!r}"
                
                logger.log(level, f"Return: {func_name} in {elapsed:.3f}s{result_str}")
                return result
                
            except Exception as e:
                elapsed = time.monotonic() - start_time
                if log_exceptions:
                    logger.log(
                        logging.ERROR,
                        f"Exception in {func_name} after {elapsed:.3f}s: {e}",
                        exc_info=trace_exceptions_enabled()
                    )
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper  # type: ignore
    return decorator


# ============================================================================
# Context Managers
# ============================================================================

@contextmanager
def debug_context(operation: str, **context_data):
    """Context manager for debugging operations.
    
    Logs entry, exit, and exceptions for a code block.
    
    Args:
        operation: Name of the operation being debugged
        **context_data: Additional context data to log
        
    Yields:
        None
        
    Example:
        >>> with debug_context("connect", host="demo"):
        ...     await client.connect()
    """
    if not debug_mode_enabled():
        yield
        return
    
    start_time = time.monotonic()
    context_str = ", ".join(f"{k}={v}" for k, v in context_data.items())
    
    logger.debug(f"[START] {operation} {context_str}")
    
    try:
        yield
        elapsed = time.monotonic() - start_time
        logger.debug(f"[END] {operation} in {elapsed:.3f}s")
    except Exception as e:
        elapsed = time.monotonic() - start_time
        logger.debug(
            f"[EXCEPTION] {operation} after {elapsed:.3f}s: {e}",
            exc_info=trace_exceptions_enabled()
        )
        raise


@contextmanager
def profile_block(name: str):
    """Context manager for profiling code blocks.
    
    Logs timing information for the wrapped code block.
    
    Args:
        name: Name of the code block being profiled
        
    Yields:
        None
        
    Example:
        >>> with profile_block("symbol_loading"):
        ...     await symbols.load()
    """
    start_time = time.monotonic()
    yield
    elapsed = time.monotonic() - start_time
    logger.debug(f"[PROFILE] {name}: {elapsed:.3f}s")


# ============================================================================
# Diagnostic Utilities
# ============================================================================

def dump_object_state(obj: Any, name: str = "object") -> dict[str, Any]:
    """Dump the state of an object for debugging.
    
    Args:
        obj: Object to dump state from
        name: Name to include in the dump
        
    Returns:
        Dictionary containing object state information
        
    Example:
        >>> state = dump_object_state(client, "CTraderClient")
        >>> logger.debug(f"Client state: {state}")
    """
    state: dict[str, Any] = {
        "name": name,
        "type": type(obj).__name__,
        "module": type(obj).__module__,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    # Get public attributes
    try:
        if hasattr(obj, "__dict__"):
            public_attrs = {
                k: repr(v) if not callable(v) else f"<callable {type(v).__name__}>"
                for k, v in obj.__dict__.items()
                if not k.startswith("_")
            }
            state["attributes"] = public_attrs
    except Exception as e:
        state["attributes_error"] = str(e)
    
    # Get properties
    try:
        properties = {}
        for attr_name in dir(type(obj)):
            attr = getattr(type(obj), attr_name, None)
            if isinstance(attr, property):
                try:
                    properties[attr_name] = repr(getattr(obj, attr_name))
                except Exception as e:
                    properties[attr_name] = f"<error: {e}>"
        if properties:
            state["properties"] = properties
    except Exception as e:
        state["properties_error"] = str(e)
    
    return state


def format_exception_info(exc: Optional[BaseException] = None) -> dict[str, Any]:
    """Format exception information for debugging.
    
    Args:
        exc: Exception to format. If None, uses sys.exc_info().
        
    Returns:
        Dictionary with formatted exception information
        
    Example:
        >>> try:
        ...     risky_operation()
        ... except Exception as e:
        ...     info = format_exception_info(e)
        ...     logger.error(f"Operation failed: {info}")
    """
    import traceback
    
    if exc is None:
        exc_type, exc_value, exc_tb = sys.exc_info()
    else:
        exc_type = type(exc)
        exc_value = exc
        exc_tb = exc.__traceback__
    
    if exc_type is None:
        return {"error": "No exception information available"}
    
    return {
        "type": exc_type.__name__ if exc_type else "Unknown",
        "module": exc_type.__module__ if exc_type else "unknown",
        "message": str(exc_value) if exc_value else "",
        "traceback": traceback.format_exception(exc_type, exc_value, exc_tb) if exc_tb else [],
    }


# ============================================================================
# Runtime Diagnostics
# ============================================================================

def get_runtime_info() -> dict[str, Any]:
    """Get runtime diagnostic information.
    
    Returns:
        Dictionary with system and runtime information
        
    Example:
        >>> info = get_runtime_info()
        >>> print(f"Python: {info['python_version']}")
        >>> print(f"Platform: {info['platform']}")
    """
    import platform
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "debug_flags": get_debug_status(),
    }


# ============================================================================
# Import asyncio for the decorator
# ============================================================================

import asyncio


# ============================================================================
# Export public API
# ============================================================================

__all__ = [
    # Debug flags
    "debug_mode_enabled",
    "connection_debug_enabled",
    "protocol_debug_enabled",
    "log_calls_enabled",
    "trace_exceptions_enabled",
    
    # Management
    "set_debug_mode",
    "get_debug_status",
    
    # Decorators
    "log_calls",
    
    # Context managers
    "debug_context",
    "profile_block",
    
    # Utilities
    "dump_object_state",
    "format_exception_info",
    "get_runtime_info",
]
