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
    
    # Advanced
    heartbeat_interval: float = 30.0  # Send heartbeat every N seconds
    message_max_size: int = 10 * 1024 * 1024  # 10MB max message size
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.host_type not in ("demo", "live"):
            raise ValueError(f"host_type must be 'demo' or 'live', got: {self.host_type}")
        
        if self.account_id <= 0:
            raise ValueError(f"account_id must be positive, got: {self.account_id}")
        
        if self.connection_timeout <= 0:
            raise ValueError(f"connection_timeout must be positive, got: {self.connection_timeout}")
    
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
        """
        def get_env(key: str, default=None, cast=str):
            value = os.getenv(f"{prefix}{key}", default)
            if value is None:
                return default
            if cast == bool:
                return str(value).lower() in ("true", "1", "yes", "on")
            return cast(value)
        
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
            json.dump(self.__dict__, f, indent=2)
    
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
