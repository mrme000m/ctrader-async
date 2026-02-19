"""Logging helpers for cTrader async client.

This module provides enhanced logging capabilities including:
- Structured JSON formatting
- BetterStack integration (optional)
- Async-safe logging handlers
- Debug context management

Example:
    >>> from ctc.utils.logging import setup_logging
    >>> 
    >>> # Basic setup
    >>> setup_logging(level="INFO")
    >>> 
    >>> # With BetterStack integration (auto-detected from env vars)
    >>> setup_logging(level="INFO", betterstack=True)
    >>> 
    >>> # JSON format for structured logging
    >>> setup_logging(level="DEBUG", log_format="json")
"""

from __future__ import annotations

import json
import logging
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Optional, Generator


def _is_truthy(value: str | None) -> bool:
    """Check if a string value is truthy."""
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on", "enabled"}


class JsonLogFormatter(logging.Formatter):
    """Minimal structured JSON formatter.
    
    Formats log records as JSON objects with standard fields.
    Useful for structured logging and log aggregation systems.
    
    Example output:
        {
            "timestamp": "2024-01-15T10:30:00+00:00",
            "level": "INFO",
            "logger": "ctc.client",
            "message": "Connected to cTrader"
        }
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON."""
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add source location for debug and above
        if record.levelno >= logging.DEBUG:
            payload["source"] = {
                "file": record.filename,
                "line": record.lineno,
                "function": record.funcName,
            }
        
        # Add exception info if present
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        
        # Add any extra attributes from the record
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message",
                "asctime", "timestamp", "source", "exception"
            }:
                try:
                    # Only include JSON-serializable values
                    json.dumps({key: value})
                    payload[key] = value
                except (TypeError, ValueError):
                    pass
        
        return json.dumps(payload, ensure_ascii=False, default=str)


class ColorLogFormatter(logging.Formatter):
    """Colored log formatter for terminal output.
    
    Adds ANSI color codes to log levels for better readability
    in terminal/console outputs.
    """
    
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
        "RESET": "\033[0m",       # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format a log record with colors."""
        # Save original levelname
        original_levelname = record.levelname
        
        # Add color to levelname
        if record.levelname in self.COLORS:
            color = self.COLORS[record.levelname]
            reset = self.COLORS["RESET"]
            record.levelname = f"{color}{record.levelname}{reset}"
        
        # Format the message
        result = super().format(record)
        
        # Restore original levelname
        record.levelname = original_levelname
        
        return result


class DebugContextFilter(logging.Filter):
    """Filter that adds debug context to log records.
    
    Can be used to add contextual information to all log records
    within a specific scope.
    """
    
    def __init__(self, name: str = "", **context):
        super().__init__(name)
        self.context = context
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to log record."""
        for key, value in self.context.items():
            if not hasattr(record, key):
                setattr(record, key, value)
        return True


def setup_logging(
    level: str = "INFO",
    *,
    log_format: str = "plain",
    betterstack: bool = False,
    enable_colors: Optional[bool] = None,
    loggers: Optional[list[str]] = None,
) -> list[logging.Handler]:
    """Configure logging once and keep existing handlers usable.
    
    This function sets up logging for the cTrader client with various
    formatting options and optional BetterStack integration.
    
    Args:
        level: Logging level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format style - "plain", "json", or "colored"
        betterstack: Whether to enable BetterStack integration. If True but
                    BetterStack is not configured, a warning is logged.
        enable_colors: Force enable/disable colors. If None, auto-detects
                      based on terminal capabilities.
        loggers: List of logger names to configure. If None, configures root.
        
    Returns:
        List of handlers that were added
        
    Example:
        >>> # Basic setup
        >>> setup_logging(level="INFO")
        
        >>> # With JSON formatting
        >>> setup_logging(level="DEBUG", log_format="json")
        
        >>> # With BetterStack (auto-detects from env vars)
        >>> setup_logging(level="INFO", betterstack=True)
        
        >>> # Colored output for terminal
        >>> setup_logging(level="INFO", log_format="colored")
    """
    handlers_added: list[logging.Handler] = []
    
    # Resolve level
    resolved_level = getattr(logging, str(level).upper(), logging.INFO)
    
    # Determine colors
    if enable_colors is None:
        enable_colors = sys.stdout.isatty() and log_format == "colored"
    
    # Create formatter
    formatter: logging.Formatter
    if log_format.lower() == "json":
        formatter = JsonLogFormatter()
    elif log_format.lower() == "colored" and enable_colors:
        formatter = ColorLogFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    # Determine which loggers to configure
    target_loggers = []
    if loggers:
        for name in loggers:
            target_loggers.append(logging.getLogger(name))
    else:
        target_loggers.append(logging.getLogger())
    
    # Configure each logger
    for logger in target_loggers:
        logger.setLevel(resolved_level)
        
        # Add console handler if none exists
        if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(resolved_level)
            logger.addHandler(console_handler)
            handlers_added.append(console_handler)
        else:
            # Update formatter on existing handlers
            for handler in logger.handlers:
                if isinstance(handler, logging.StreamHandler):
                    handler.setFormatter(formatter)
    
    # Set up BetterStack if requested
    if betterstack:
        try:
            from ctc.integrations import setup_betterstack_logging
            
            for name in (loggers or [None]):
                handler = setup_betterstack_logging(
                    level=resolved_level,
                    logger_name=name,
                )
                if handler:
                    handlers_added.append(handler)
                elif name is None:
                    logging.getLogger().debug(
                        "BetterStack requested but not configured "
                        "(set BETTERSTACK_INGEST_HOST and BETTERSTACK_SOURCE_TOKEN)"
                    )
        except ImportError as e:
            logging.getLogger().warning(f"Could not import BetterStack integration: {e}")
    
    return handlers_added


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Get a logger with optional level configuration.
    
    Args:
        name: Logger name
        level: Optional level to set
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    if level:
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger


@contextmanager
def log_context(
    logger: logging.Logger,
    operation: str,
    level: int = logging.INFO,
    **context
) -> Generator[None, None, None]:
    """Context manager for logging operation start/end with timing.
    
    Args:
        logger: Logger to use
        operation: Name of the operation being performed
        level: Log level for messages
        **context: Additional context to log
        
    Yields:
        None
        
    Example:
        >>> logger = logging.getLogger("ctc.client")
        >>> with log_context(logger, "connect", host="demo"):
        ...     await client.connect()
        [logs: "Starting operation: connect", "Completed operation: connect in 1.23s"]
    """
    start_time = datetime.now(timezone.utc)
    
    # Log start
    start_msg = f"Starting operation: {operation}"
    if context:
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        start_msg = f"{start_msg} ({context_str})"
    logger.log(level, start_msg)
    
    try:
        yield
        
        # Log success
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.log(level, f"Completed operation: {operation} in {duration:.3f}s")
        
    except Exception as e:
        # Log failure
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.log(
            logging.ERROR,
            f"Failed operation: {operation} after {duration:.3f}s: {e}",
            exc_info=True
        )
        raise


class StructuredLogAdapter(logging.LoggerAdapter):
    """Logger adapter that adds structured context to all messages.
    
    This adapter allows you to attach persistent context data to a logger,
    which is then included in every log message.
    
    Example:
        >>> logger = logging.getLogger("ctc.client")
        >>> adapter = StructuredLogAdapter(logger, account_id=12345)
        >>> adapter.info("Connected")  # Logs with account_id context
    """
    
    def __init__(
        self,
        logger: logging.Logger,
        extra: Optional[dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(logger, extra or {})
        self.extra.update(kwargs)
    
    def process(
        self,
        msg: str,
        kwargs: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """Process the log message, adding extra context."""
        # Merge adapter extra with any extra in kwargs
        extra = kwargs.get("extra", {})
        merged_extra = {**self.extra, **extra}
        
        # Format message with context for plain text output
        if merged_extra:
            context_str = " ".join(f"[{k}={v}]" for k, v in merged_extra.items())
            msg = f"{msg} {context_str}"
        
        kwargs["extra"] = merged_extra
        return msg, kwargs
    
    def bind(self, **kwargs) -> StructuredLogAdapter:
        """Create a new adapter with additional bound context."""
        new_extra = {**self.extra, **kwargs}
        return StructuredLogAdapter(self.logger, new_extra)


def create_structured_logger(
    name: str,
    **context
) -> StructuredLogAdapter:
    """Create a structured logger with bound context.
    
    Args:
        name: Logger name
        **context: Context data to bind to the logger
        
    Returns:
        StructuredLogAdapter instance
        
    Example:
        >>> logger = create_structured_logger("ctc.client", account_id=12345)
        >>> logger.info("Connected")  # Includes account_id in log
    """
    return StructuredLogAdapter(logging.getLogger(name), **context)


# Global debug mode flag
debug_mode = _is_truthy(
    sys.modules["os"].environ.get("CTRADER_DEBUG")
)


def set_debug_mode(enabled: bool) -> None:
    """Enable or disable debug mode globally.
    
    When debug mode is enabled, additional diagnostic information
    is logged at INFO level instead of DEBUG.
    
    Args:
        enabled: Whether to enable debug mode
    """
    global debug_mode
    debug_mode = enabled
    
    # Update root logger level if enabling
    if enabled:
        root = logging.getLogger()
        if root.level > logging.DEBUG:
            root.setLevel(logging.DEBUG)
        
        logging.getLogger("ctc").setLevel(logging.DEBUG)
        logging.info("Debug mode enabled")


def is_debug_mode() -> bool:
    """Check if debug mode is enabled.
    
    Returns:
        True if debug mode is enabled
    """
    return debug_mode
