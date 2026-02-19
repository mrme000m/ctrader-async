"""
BetterStack integration for cTrader async client.

This module provides optional logging and monitoring integration with BetterStack.
It is completely opt-in - if the required environment variables are not set,
all operations become no-ops with zero performance impact.

Environment Variables:
    BETTERSTACK_INGEST_HOST: BetterStack ingest host (e.g., "in.logtail.com")
    BETTERSTACK_SOURCE_TOKEN: BetterStack source token for authentication
    BETTERSTACK_ERRORS_DSN: Optional Sentry-compatible DSN for error tracking
    BETTERSTACK_UPTIME_HEARTBEAT_URL: Optional heartbeat URL for uptime monitoring
    BETTERSTACK_LOG_LEVEL: Minimum log level to send (default: INFO)
    BETTERSTACK_ENABLE_ON_CLIENT_INIT: Auto-enable on client init (default: true)

Example:
    >>> import ctc
    >>> from ctc.integrations import setup_betterstack_logging
    >>> 
    >>> # Enable BetterStack logging (if env vars are set)
    >>> setup_betterstack_logging()
    >>> 
    >>> # Or check if BetterStack is enabled
    >>> from ctc.integrations import betterstack_enabled
    >>> if betterstack_enabled():
    ...     print("BetterStack logging is active")
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from functools import lru_cache

# Module-level logger
logger = logging.getLogger(__name__)

# Try to import aiohttp for async HTTP requests, fall back to urllib
aiohttp: Any = None
urllib_request: Any = None

try:
    import aiohttp
except ImportError:
    try:
        import urllib.request as urllib_request
    except ImportError:
        pass


# Constants
DEFAULT_LOG_LEVEL = "INFO"
BETTERSTACK_VERSION = "1.0.0"


@lru_cache(maxsize=1)
def _is_truthy(value: str | bool | None) -> bool:
    """Check if a value is truthy."""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "enabled"}


@lru_cache(maxsize=1)
def betterstack_enabled() -> bool:
    """Check if BetterStack integration is enabled.
    
    Returns:
        True if both BETTERSTACK_INGEST_HOST and BETTERSTACK_SOURCE_TOKEN
        environment variables are set.
    """
    return bool(
        os.getenv("BETTERSTACK_INGEST_HOST") and 
        os.getenv("BETTERSTACK_SOURCE_TOKEN")
    )


def get_betterstack_config() -> BetterStackConfig:
    """Get BetterStack configuration from environment variables."""
    return BetterStackConfig.from_env()


@dataclass
class BetterStackConfig:
    """Configuration for BetterStack integration.
    
    This configuration is typically loaded from environment variables,
    but can also be created programmatically.
    
    Attributes:
        ingest_host: BetterStack ingest host (e.g., "in.logtail.com")
        source_token: BetterStack source token for authentication
        errors_dsn: Optional Sentry-compatible DSN for error tracking
        heartbeat_url: Optional heartbeat URL for uptime monitoring
        log_level: Minimum log level to send to BetterStack
        enable_on_init: Whether to auto-enable on client initialization
        timeout_seconds: HTTP request timeout in seconds
        batch_size: Number of logs to batch before sending (0 = no batching)
        flush_interval_seconds: How often to flush batched logs
        include_metadata: Whether to include system metadata with logs
        service_name: Service name for log identification
        service_version: Service version for log identification
        environment: Environment name (e.g., "production", "staging")
    """
    
    ingest_host: Optional[str] = None
    source_token: Optional[str] = None
    errors_dsn: Optional[str] = None
    heartbeat_url: Optional[str] = None
    log_level: str = DEFAULT_LOG_LEVEL
    enable_on_init: bool = True
    timeout_seconds: float = 5.0
    batch_size: int = 0  # 0 = no batching, send immediately
    flush_interval_seconds: float = 5.0
    include_metadata: bool = True
    service_name: str = "ctrader-client"
    service_version: str = "unknown"
    environment: str = "development"
    
    @classmethod
    def from_env(cls, prefix: str = "BETTERSTACK_") -> BetterStackConfig:
        """Create configuration from environment variables.
        
        Args:
            prefix: Prefix for environment variable names
            
        Returns:
            BetterStackConfig instance
            
        Example:
            >>> config = BetterStackConfig.from_env()
            >>> # Reads BETTERSTACK_INGEST_HOST, BETTERSTACK_SOURCE_TOKEN, etc.
        """
        def get_env(key: str, default=None, cast=str):
            value = os.getenv(f"{prefix}{key}", default)
            if value is None:
                return default
            if cast == bool:
                return _is_truthy(value)
            if cast == int:
                return int(value) if value else default
            if cast == float:
                return float(value) if value else default
            return cast(value)
        
        # Try to get version from package
        version = "unknown"
        try:
            from ctc import __version__
            version = __version__
        except ImportError:
            pass
        
        return cls(
            ingest_host=get_env("INGEST_HOST"),
            source_token=get_env("SOURCE_TOKEN"),
            errors_dsn=get_env("ERRORS_DSN"),
            heartbeat_url=get_env("UPTIME_HEARTBEAT_URL"),
            log_level=get_env("LOG_LEVEL", DEFAULT_LOG_LEVEL),
            enable_on_init=get_env("ENABLE_ON_CLIENT_INIT", True, bool),
            timeout_seconds=get_env("TIMEOUT_SECONDS", 5.0, float),
            batch_size=get_env("BATCH_SIZE", 0, int),
            flush_interval_seconds=get_env("FLUSH_INTERVAL_SECONDS", 5.0, float),
            include_metadata=get_env("INCLUDE_METADATA", True, bool),
            service_name=get_env("SERVICE_NAME", "ctrader-client"),
            service_version=get_env("SERVICE_VERSION", version),
            environment=get_env("ENVIRONMENT", "development"),
        )
    
    def is_configured(self) -> bool:
        """Check if the configuration is valid for use."""
        return bool(self.ingest_host and self.source_token)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary (sanitized)."""
        return {
            "ingest_host": self.ingest_host,
            "log_level": self.log_level,
            "enable_on_init": self.enable_on_init,
            "timeout_seconds": self.timeout_seconds,
            "batch_size": self.batch_size,
            "include_metadata": self.include_metadata,
            "service_name": self.service_name,
            "service_version": self.service_version,
            "environment": self.environment,
            "has_source_token": bool(self.source_token),
            "has_errors_dsn": bool(self.errors_dsn),
            "has_heartbeat_url": bool(self.heartbeat_url),
        }


class BetterStackHandler:
    """Main handler for BetterStack integration.
    
    This class manages the BetterStack integration, including:
    - Log ingestion via HTTP API
    - Error tracking (Sentry-compatible)
    - Heartbeat monitoring
    
    The handler is designed to be non-invasive - if BetterStack is not
    configured, all operations become no-ops with minimal overhead.
    
    Example:
        >>> handler = BetterStackHandler()
        >>> await handler.initialize()
        >>> 
        >>> # Send a log
        >>> await handler.send_log({"message": "Trading started", "level": "info"})
        >>> 
        >>> # Send heartbeat
        >>> await handler.send_heartbeat()
        >>> 
        >>> await handler.shutdown()
    """
    
    def __init__(self, config: Optional[BetterStackConfig] = None):
        """Initialize the BetterStack handler.
        
        Args:
            config: BetterStack configuration. If None, loads from environment.
        """
        self.config = config or BetterStackConfig.from_env()
        self._enabled = self.config.is_configured()
        self._session: Any = None
        self._log_queue: list[dict] = []
        self._flush_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self._initialized = False
        
        # Import aiohttp if available
        self._aiohttp_available = aiohttp is not None
        
    @property
    def enabled(self) -> bool:
        """Check if BetterStack is enabled and configured."""
        return self._enabled
    
    async def initialize(self) -> bool:
        """Initialize the BetterStack handler.
        
        Returns:
            True if initialization was successful or already initialized.
            False if BetterStack is not configured.
        """
        if not self._enabled:
            return False
        
        if self._initialized:
            return True
        
        try:
            # Initialize aiohttp session if available
            if self._aiohttp_available:
                self._session = aiohttp.ClientSession(
                    headers={
                        "Authorization": f"Bearer {self.config.source_token}",
                        "Content-Type": "application/json",
                        "User-Agent": f"ctrader-betterstack/{BETTERSTACK_VERSION}",
                    }
                )
            
            # Start background flush task if batching is enabled
            if self.config.batch_size > 0:
                self._flush_task = asyncio.create_task(self._flush_loop())
            
            self._initialized = True
            logger.debug("BetterStack handler initialized")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to initialize BetterStack handler: {e}")
            self._enabled = False
            return False
    
    async def shutdown(self) -> None:
        """Shutdown the BetterStack handler and flush any pending logs."""
        if not self._initialized:
            return
        
        self._shutdown_event.set()
        
        # Flush remaining logs
        if self._log_queue:
            await self._flush_logs()
        
        # Cancel flush task
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Close session
        if self._session:
            await self._session.close()
            self._session = None
        
        self._initialized = False
        logger.debug("BetterStack handler shutdown")
    
    async def send_log(self, event: dict[str, Any]) -> bool:
        """Send a log event to BetterStack.
        
        Args:
            event: Log event dictionary with at least 'message' and 'level' keys.
            
        Returns:
            True if the log was sent successfully, False otherwise.
            Always returns True if BetterStack is not enabled.
        """
        if not self._enabled:
            return True
        
        if not self._initialized:
            await self.initialize()
        
        # Add metadata
        if self.config.include_metadata:
            event = self._enrich_event(event)
        
        # Add to queue if batching is enabled
        if self.config.batch_size > 0:
            self._log_queue.append(event)
            if len(self._log_queue) >= self.config.batch_size:
                await self._flush_logs()
            return True
        
        # Send immediately
        return await self._send_single_log(event)
    
    async def send_heartbeat(self) -> bool:
        """Send a heartbeat to BetterStack uptime monitoring.
        
        Returns:
            True if the heartbeat was sent successfully, False otherwise.
            Always returns True if heartbeat URL is not configured.
        """
        if not self.config.heartbeat_url:
            return True
        
        try:
            if self._aiohttp_available and self._session:
                async with self._session.get(
                    self.config.heartbeat_url,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
                ) as response:
                    return response.status == 200
            else:
                # Synchronous fallback
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, self._send_heartbeat_sync)
        except Exception as e:
            logger.debug(f"Failed to send BetterStack heartbeat: {e}")
            return False
    
    async def capture_exception(
        self, 
        exc_info: Optional[tuple] = None,
        extra: Optional[dict] = None
    ) -> bool:
        """Capture an exception for error tracking.
        
        Args:
            exc_info: Exception info tuple (type, value, traceback).
                     If None, uses sys.exc_info().
            extra: Additional context to include with the exception.
            
        Returns:
            True if the exception was captured successfully.
        """
        if not self._enabled:
            return True
        
        if exc_info is None:
            exc_info = sys.exc_info()
        
        if exc_info[0] is None:
            return True
        
        try:
            exc_type, exc_value, exc_tb = exc_info
            
            event = {
                "message": f"Exception: {exc_type.__name__}: {exc_value}",
                "level": "error",
                "exception": {
                    "type": exc_type.__name__ if exc_type else "Unknown",
                    "value": str(exc_value) if exc_value else "",
                    "traceback": traceback.format_exception(*exc_info),
                },
            }
            
            if extra:
                event["context"] = extra
            
            return await self.send_log(event)
            
        except Exception as e:
            logger.debug(f"Failed to capture exception: {e}")
            return False
    
    def _enrich_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """Enrich a log event with metadata."""
        enriched = {
            **event,
            "dt": datetime.now(timezone.utc).isoformat(),
            "service": self.config.service_name,
            "service_version": self.config.service_version,
            "environment": self.config.environment,
        }
        
        # Add system info
        enriched["system"] = {
            "python_version": sys.version,
            "platform": sys.platform,
        }
        
        return enriched
    
    async def _send_single_log(self, event: dict[str, Any]) -> bool:
        """Send a single log event to BetterStack."""
        if not self.config.ingest_host or not self.config.source_token:
            return True
        
        url = f"https://{self.config.ingest_host}/"
        
        try:
            if self._aiohttp_available and self._session:
                async with self._session.post(
                    url,
                    json=event,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
                ) as response:
                    return response.status in (200, 201, 202)
            else:
                # Synchronous fallback
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    None, self._send_log_sync, url, event
                )
        except Exception as e:
            logger.debug(f"Failed to send log to BetterStack: {e}")
            return False
    
    def _send_log_sync(self, url: str, event: dict[str, Any]) -> bool:
        """Synchronous fallback for sending logs."""
        if urllib_request is None:
            return False
        
        try:
            data = json.dumps(event).encode("utf-8")
            headers = {
                "Authorization": f"Bearer {self.config.source_token}",
                "Content-Type": "application/json",
                "User-Agent": f"ctrader-betterstack/{BETTERSTACK_VERSION}",
            }
            req = urllib_request.Request(
                url, data=data, headers=headers, method="POST"
            )
            with urllib_request.urlopen(req, timeout=self.config.timeout_seconds) as resp:
                return resp.status in (200, 201, 202)
        except Exception:
            return False
    
    def _send_heartbeat_sync(self) -> bool:
        """Synchronous fallback for sending heartbeat."""
        if urllib_request is None or not self.config.heartbeat_url:
            return False
        
        try:
            req = urllib_request.Request(
                self.config.heartbeat_url, method="GET"
            )
            with urllib_request.urlopen(req, timeout=self.config.timeout_seconds) as resp:
                return resp.status == 200
        except Exception:
            return False
    
    async def _flush_loop(self) -> None:
        """Background task to periodically flush batched logs."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self.config.flush_interval_seconds
                )
            except asyncio.TimeoutError:
                if self._log_queue:
                    await self._flush_logs()
    
    async def _flush_logs(self) -> None:
        """Flush all queued logs to BetterStack."""
        if not self._log_queue:
            return
        
        logs = self._log_queue.copy()
        self._log_queue.clear()
        
        # Send logs as a batch
        for log in logs:
            await self._send_single_log(log)


class BetterStackLogHandler(logging.Handler):
    """Python logging handler that sends logs to BetterStack.
    
    This handler integrates with Python's standard logging module
    to automatically send log records to BetterStack.
    
    Example:
        >>> import logging
        >>> from ctc.integrations import BetterStackLogHandler
        >>> 
        >>> handler = BetterStackLogHandler()
        >>> handler.setLevel(logging.INFO)
        >>> 
        >>> logger = logging.getLogger("ctrader")
        >>> logger.addHandler(handler)
        >>> 
        >>> logger.info("Trading started")  # Sent to BetterStack
    """
    
    def __init__(
        self,
        config: Optional[BetterStackConfig] = None,
        level: int = logging.NOTSET,
    ):
        """Initialize the handler.
        
        Args:
            config: BetterStack configuration. If None, loads from environment.
            level: Minimum log level to handle.
        """
        super().__init__(level=level)
        self.config = config or BetterStackConfig.from_env()
        self._handler = BetterStackHandler(self.config)
        self._initialized = False
        self._lock = asyncio.Lock()
    
    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to BetterStack.
        
        This method is called by the logging framework when a log
        record needs to be processed.
        """
        if not self._handler.enabled:
            return
        
        try:
            event = self._format_record(record)
            
            # Use asyncio.create_task for async operation
            try:
                loop = asyncio.get_running_loop()
                asyncio.create_task(self._async_emit(event))
            except RuntimeError:
                # No event loop running, skip async emit
                pass
                
        except Exception:
            self.handleError(record)
    
    def _format_record(self, record: logging.LogRecord) -> dict[str, Any]:
        """Format a log record into BetterStack event format."""
        event = {
            "message": self.format(record),
            "level": record.levelname.lower(),
            "logger": record.name,
            "filename": record.filename,
            "lineno": record.lineno,
            "function": record.funcName,
        }
        
        # Add exception info if present
        if record.exc_info:
            event["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else "Unknown",
                "value": str(record.exc_info[1]) if record.exc_info[1] else "",
                "traceback": traceback.format_exception(*record.exc_info),
            }
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in event and not key.startswith("_"):
                try:
                    # Only include JSON-serializable values
                    json.dumps({key: value})
                    event[key] = value
                except (TypeError, ValueError):
                    pass
        
        return event
    
    async def _async_emit(self, event: dict[str, Any]) -> None:
        """Asynchronously emit the log event."""
        async with self._lock:
            if not self._initialized:
                await self._handler.initialize()
                self._initialized = True
            
            await self._handler.send_log(event)
    
    async def initialize(self) -> bool:
        """Initialize the handler."""
        if not self._handler.enabled:
            return False
        return await self._handler.initialize()
    
    async def shutdown(self) -> None:
        """Shutdown the handler."""
        await self._handler.shutdown()


# Convenience functions for module-level usage

_def_handler: Optional[BetterStackHandler] = None


def _get_default_handler() -> Optional[BetterStackHandler]:
    """Get or create the default BetterStack handler."""
    global _def_handler
    if _def_handler is None:
        config = BetterStackConfig.from_env()
        if config.is_configured():
            _def_handler = BetterStackHandler(config)
    return _def_handler


async def send_betterstack_log(event: dict[str, Any]) -> bool:
    """Send a log event to BetterStack using the default handler.
    
    Args:
        event: Log event dictionary.
        
    Returns:
        True if the log was sent successfully.
    """
    handler = _get_default_handler()
    if handler is None:
        return True
    return await handler.send_log(event)


async def send_betterstack_heartbeat() -> bool:
    """Send a heartbeat to BetterStack using the default handler.
    
    Returns:
        True if the heartbeat was sent successfully.
    """
    handler = _get_default_handler()
    if handler is None:
        return True
    return await handler.send_heartbeat()


async def capture_betterstack_exception(
    exc_info: Optional[tuple] = None,
    extra: Optional[dict] = None
) -> bool:
    """Capture an exception to BetterStack using the default handler.
    
    Args:
        exc_info: Exception info tuple. If None, uses sys.exc_info().
        extra: Additional context.
        
    Returns:
        True if the exception was captured successfully.
    """
    handler = _get_default_handler()
    if handler is None:
        return True
    return await handler.capture_exception(exc_info, extra)


def setup_betterstack_logging(
    level: Optional[int] = None,
    logger_name: Optional[str] = None,
    config: Optional[BetterStackConfig] = None,
) -> Optional[BetterStackLogHandler]:
    """Set up BetterStack logging for a logger.
    
    This function adds a BetterStackLogHandler to the specified logger.
    If BetterStack is not configured, this function does nothing.
    
    Args:
        level: Minimum log level to send. If None, uses config.log_level.
        logger_name: Name of the logger to configure. If None, uses root logger.
        config: BetterStack configuration. If None, loads from environment.
        
    Returns:
        The configured handler, or None if BetterStack is not enabled.
        
    Example:
        >>> from ctc.integrations import setup_betterstack_logging
        >>> 
        >>> # Set up for root logger
        >>> handler = setup_betterstack_logging(level=logging.INFO)
        >>> 
        >>> # Set up for specific logger
        >>> handler = setup_betterstack_logging(
        ...     level=logging.WARNING,
        ...     logger_name="ctc.client"
        ... )
    """
    config = config or BetterStackConfig.from_env()
    
    if not config.is_configured():
        logger.debug("BetterStack not configured, skipping setup")
        return None
    
    # Determine log level
    if level is None:
        level = getattr(logging, config.log_level.upper(), logging.INFO)
    
    # Get the logger
    target_logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
    
    # Create and configure handler
    handler = BetterStackLogHandler(config=config, level=level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    target_logger.addHandler(handler)
    
    logger.info(
        f"BetterStack logging configured for {logger_name or 'root'} "
        f"at level {logging.getLevelName(level)}"
    )
    
    return handler
