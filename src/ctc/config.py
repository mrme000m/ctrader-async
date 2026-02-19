"""
Configuration management for cTrader async client.
"""

from __future__ import annotations

import os
import json
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class ClientConfig:
    """Configuration for cTrader client.
    
    Configuration can be loaded from:
    - Constructor arguments
    - Environment variables
    - Configuration file
    
    Args:
        client_id: OAuth client ID
        client_secret: OAuth client secret
        access_token: OAuth access token
        account_id: Trading account ID
        host_type: Server type ("demo" or "live")
        
    Optional Args:
        connection_timeout: Timeout for initial connection (seconds)
        request_timeout: Default timeout for requests (seconds)
        auth_timeout: Timeout for authentication (seconds)
        reconnect_max_attempts: Maximum reconnection attempts
        reconnect_base_delay: Base delay for exponential backoff (seconds)
        reconnect_max_delay: Maximum reconnection delay (seconds)
        rate_limit_trading: Rate limit for trading requests (per second)
        rate_limit_historical: Rate limit for historical data (per second)
        
    BetterStack Integration (Optional):
        betterstack_enabled: Enable BetterStack logging integration
        betterstack_ingest_host: BetterStack log ingest host
        betterstack_source_token: BetterStack source token
        betterstack_log_level: Minimum log level for BetterStack
        betterstack_heartbeat_url: Optional heartbeat URL for uptime monitoring
        
    Example:
        >>> config = ClientConfig(
        ...     client_id="your_id",
        ...     client_secret="your_secret",
        ...     access_token="your_token",
        ...     account_id=12345,
        ...     host_type="demo",
        ...     betterstack_enabled=True  # Auto-detects from env vars
        ... )
    """
    
    # Required settings
    client_id: str
    client_secret: str
    access_token: str
    account_id: int
    host_type: str = "demo"  # "demo" or "live"
    
    # Connection settings
    connection_timeout: float = 30.0
    request_timeout: float = 30.0
    auth_timeout: float = 60.0
    use_tls: bool = True  # cTrader protobuf endpoint expects TLS
    
    # Reconnection settings
    reconnect_max_attempts: int = 10
    reconnect_base_delay: float = 1.0
    reconnect_max_delay: float = 300.0
    reconnect_enabled: bool = True
    
    # Rate limiting
    rate_limit_trading: int = 50  # requests per second
    rate_limit_historical: int = 5  # requests per second
    
    # Logging
    log_level: str = "INFO"
    log_messages: bool = False  # Log all protobuf messages (debug)
    log_format: str = "plain"  # "plain" or "json"
    configure_logging: bool = False  # if True, client configures root logger
    
    # BetterStack Integration (optional, opt-in)
    betterstack_enabled: bool = False  # Enable BetterStack logging
    betterstack_ingest_host: Optional[str] = None  # e.g., "in.logtail.com"
    betterstack_source_token: Optional[str] = None  # Source token
    betterstack_log_level: str = "INFO"  # Min level to send to BetterStack
    betterstack_heartbeat_url: Optional[str] = None  # Uptime heartbeat URL
    betterstack_service_name: str = "ctrader-client"  # Service identifier
    betterstack_environment: str = "development"  # Environment name
    
    # Advanced
    heartbeat_interval: float = 30.0  # Send heartbeat every N seconds
    message_max_size: int = 10 * 1024 * 1024  # 10MB max message size

    # Connection watchdog
    stale_connection_timeout: Optional[float] = None  # None => auto (heartbeat_interval * 10, min 300s)
    stale_connection_threshold_multiplier: float = 10.0  # Multiplier for heartbeat interval
    watchdog_check_interval: float = 5.0

    # Token auto-refresh
    refresh_token: Optional[str] = None
    token_auto_refresh_enabled: bool = False
    token_refresh_margin_seconds: float = 60.0
    token_refresh_default_expires_in: int = 3600

    # Performance / backpressure
    inbound_queue_size: int = 1000  # max inbound messages buffered before processing
    inbound_workers: int = 1  # number of message processing tasks
    drop_inbound_when_full: bool = False  # if True, drop inbound messages instead of blocking

    # Streaming
    tick_queue_size: int = 1000  # per-stream tick buffer size
    
    # WebSocket settings
    websocket_ping_interval: float = 20.0
    websocket_ping_timeout: float = 10.0
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.host_type not in ("demo", "live"):
            raise ValueError(f"host_type must be 'demo' or 'live', got: {self.host_type}")
        
        if self.account_id <= 0:
            raise ValueError(f"account_id must be positive, got: {self.account_id}")
        
        if self.connection_timeout <= 0:
            raise ValueError(f"connection_timeout must be positive, got: {self.connection_timeout}")
        
        # If betterstack_enabled is True but no config provided, try to load from env
        if self.betterstack_enabled:
            if not self.betterstack_ingest_host:
                self.betterstack_ingest_host = os.getenv("BETTERSTACK_INGEST_HOST")
            if not self.betterstack_source_token:
                self.betterstack_source_token = os.getenv("BETTERSTACK_SOURCE_TOKEN")
            if not self.betterstack_heartbeat_url:
                self.betterstack_heartbeat_url = os.getenv("BETTERSTACK_UPTIME_HEARTBEAT_URL")
    
    @classmethod
    def from_env(cls, prefix: str = "CTRADER_") -> ClientConfig:
        """Load configuration from environment variables.
        
        Args:
            prefix: Prefix for environment variable names
            
        Returns:
            ClientConfig instance
            
        Example:
            >>> config = ClientConfig.from_env()
            >>> # Reads CTRADER_CLIENT_ID, CTRADER_CLIENT_SECRET, etc.
            >>> # Also reads BETTERSTACK_INGEST_HOST, BETTERSTACK_SOURCE_TOKEN, etc.
        """
        def _is_truthy(value: str | bool | None) -> bool:
            if value is None:
                return False
            if isinstance(value, bool):
                return value
            return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "enabled"}
        
        def get_env(key: str, default=None, cast=str):
            value = os.getenv(f"{prefix}{key}", default)
            if value is None:
                return default
            if cast == bool:
                return _is_truthy(value)
            return cast(value)
        
        def get_env_any(*keys: str, default=None, cast=str):
            """Try multiple env var names, return first found."""
            for key in keys:
                value = os.getenv(key)
                if value is not None:
                    if cast == bool:
                        return _is_truthy(value)
                    return cast(value)
            return default
        
        return cls(
            client_id=get_env("CLIENT_ID", ""),
            client_secret=get_env("CLIENT_SECRET", ""),
            access_token=get_env("ACCESS_TOKEN", ""),
            account_id=get_env("ACCOUNT_ID", 0, int),
            host_type=get_env("HOST_TYPE", "demo"),
            connection_timeout=get_env("CONNECTION_TIMEOUT", 30.0, float),
            request_timeout=get_env("REQUEST_TIMEOUT", 30.0, float),
            auth_timeout=get_env("AUTH_TIMEOUT", 60.0, float),
            use_tls=get_env("USE_TLS", True, bool),
            reconnect_max_attempts=get_env("RECONNECT_MAX_ATTEMPTS", 10, int),
            reconnect_base_delay=get_env("RECONNECT_BASE_DELAY", 1.0, float),
            reconnect_max_delay=get_env("RECONNECT_MAX_DELAY", 300.0, float),
            reconnect_enabled=get_env("RECONNECT_ENABLED", True, bool),
            rate_limit_trading=get_env("RATE_LIMIT_TRADING", 50, int),
            rate_limit_historical=get_env("RATE_LIMIT_HISTORICAL", 5, int),
            log_level=get_env("LOG_LEVEL", "INFO"),
            log_messages=get_env("LOG_MESSAGES", False, bool),
            log_format=get_env("LOG_FORMAT", "plain"),
            configure_logging=get_env("CONFIGURE_LOGGING", False, bool),
            inbound_queue_size=get_env("INBOUND_QUEUE_SIZE", 1000, int),
            inbound_workers=get_env("INBOUND_WORKERS", 1, int),
            drop_inbound_when_full=get_env("DROP_INBOUND_WHEN_FULL", False, bool),
            tick_queue_size=get_env("TICK_QUEUE_SIZE", 1000, int),
            stale_connection_timeout=get_env("STALE_CONNECTION_TIMEOUT", None, float),
            watchdog_check_interval=get_env("WATCHDOG_CHECK_INTERVAL", 5.0, float),
            refresh_token=get_env("REFRESH_TOKEN", None),
            token_auto_refresh_enabled=get_env("TOKEN_AUTO_REFRESH_ENABLED", False, bool),
            token_refresh_margin_seconds=get_env("TOKEN_REFRESH_MARGIN_SECONDS", 60.0, float),
            token_refresh_default_expires_in=get_env("TOKEN_REFRESH_DEFAULT_EXPIRES_IN", 3600, int),
            websocket_ping_interval=get_env("WEBSOCKET_PING_INTERVAL", 20.0, float),
            websocket_ping_timeout=get_env("WEBSOCKET_PING_TIMEOUT", 10.0, float),
            # BetterStack configuration (reads from both CTRADER_ and BETTERSTACK_ prefixes)
            betterstack_enabled=get_env_any(
                f"{prefix}BETTERSTACK_ENABLED",
                "BETTERSTACK_ENABLED",
                default=False,
                cast=bool
            ),
            betterstack_ingest_host=get_env_any(
                f"{prefix}BETTERSTACK_INGEST_HOST",
                "BETTERSTACK_INGEST_HOST"
            ),
            betterstack_source_token=get_env_any(
                f"{prefix}BETTERSTACK_SOURCE_TOKEN",
                "BETTERSTACK_SOURCE_TOKEN"
            ),
            betterstack_log_level=get_env_any(
                f"{prefix}BETTERSTACK_LOG_LEVEL",
                "BETTERSTACK_LOG_LEVEL",
                default="INFO"
            ),
            betterstack_heartbeat_url=get_env_any(
                f"{prefix}BETTERSTACK_HEARTBEAT_URL",
                "BETTERSTACK_UPTIME_HEARTBEAT_URL"
            ),
            betterstack_service_name=get_env_any(
                f"{prefix}BETTERSTACK_SERVICE_NAME",
                "BETTERSTACK_SERVICE_NAME",
                default="ctrader-client"
            ),
            betterstack_environment=get_env_any(
                f"{prefix}BETTERSTACK_ENVIRONMENT",
                "BETTERSTACK_ENVIRONMENT",
                default="development"
            ),
        )
    
    @classmethod
    def from_file(cls, path: str | Path) -> ClientConfig:
        """Load configuration from JSON file.
        
        Args:
            path: Path to configuration file
            
        Returns:
            ClientConfig instance
            
        Example:
            >>> config = ClientConfig.from_file("config.json")
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        with open(path, "r") as f:
            data = json.load(f)
        
        return cls(**data)
    
    def to_file(self, path: str | Path):
        """Save configuration to JSON file.
        
        Args:
            path: Path to save configuration
            
        Example:
            >>> config.to_file("config.json")
        """
        path = Path(path)
        with open(path, "w") as f:
            # Convert to dict and mask sensitive fields
            data = self.to_dict(mask_sensitive=True)
            json.dump(data, f, indent=2)
    
    def to_dict(self, mask_sensitive: bool = False) -> dict:
        """Convert configuration to dictionary.
        
        Args:
            mask_sensitive: If True, masks sensitive fields like tokens
            
        Returns:
            Dictionary representation of the configuration
        """
        data = {
            "client_id": self.client_id,
            "client_secret": "***" if mask_sensitive else self.client_secret,
            "access_token": "***" if mask_sensitive else self.access_token,
            "account_id": self.account_id,
            "host_type": self.host_type,
            "connection_timeout": self.connection_timeout,
            "request_timeout": self.request_timeout,
            "auth_timeout": self.auth_timeout,
            "use_tls": self.use_tls,
            "reconnect_enabled": self.reconnect_enabled,
            "reconnect_max_attempts": self.reconnect_max_attempts,
            "log_level": self.log_level,
            "log_format": self.log_format,
            "betterstack_enabled": self.betterstack_enabled,
            "betterstack_log_level": self.betterstack_log_level,
            "betterstack_service_name": self.betterstack_service_name,
            "betterstack_environment": self.betterstack_environment,
        }
        
        # Include BetterStack config if not masking or if empty
        if not mask_sensitive:
            data["betterstack_ingest_host"] = self.betterstack_ingest_host
            data["betterstack_heartbeat_url"] = self.betterstack_heartbeat_url
        else:
            data["betterstack_ingest_host"] = (
                "***" if self.betterstack_ingest_host else None
            )
            data["betterstack_has_source_token"] = bool(
                self.betterstack_source_token
            )
            data["betterstack_heartbeat_configured"] = bool(
                self.betterstack_heartbeat_url
            )
        
        return data
    
    def validate(self):
        """Validate that all required configuration is present.
        
        Raises:
            ValueError: If required configuration is missing
        """
        missing = []
        
        if not self.client_id:
            missing.append("client_id")
        if not self.client_secret:
            missing.append("client_secret")
        if not self.access_token:
            missing.append("access_token")
        if not self.account_id:
            missing.append("account_id")
        
        if missing:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing)}\n"
                f"Provide via constructor, environment variables (CTRADER_*), or config file."
            )
        
        # Validate BetterStack config if enabled
        if self.betterstack_enabled:
            if not self.betterstack_ingest_host or not self.betterstack_source_token:
                import logging
                logging.getLogger(__name__).warning(
                    "BetterStack enabled but missing ingest_host or source_token. "
                    "Set BETTERSTACK_INGEST_HOST and BETTERSTACK_SOURCE_TOKEN environment variables."
                )
    
    @property
    def host(self) -> str:
        """Get the appropriate host based on host_type."""
        # Import here to avoid circular dependency
        from .transport.endpoints import get_host
        return get_host(self.host_type)
    
    @property
    def port(self) -> int:
        """Get the protobuf port (5035 for both demo and live)."""
        return 5035
    
    @property
    def betterstack_configured(self) -> bool:
        """Check if BetterStack is properly configured.
        
        Returns:
            True if BetterStack is enabled and has required configuration
        """
        return (
            self.betterstack_enabled and
            bool(self.betterstack_ingest_host) and
            bool(self.betterstack_source_token)
        )
