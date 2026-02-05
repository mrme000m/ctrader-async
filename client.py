"""
Main cTrader async client.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from .config import ClientConfig
from .transport import TCPTransport, get_host, PROTOBUF_PORT
from .protocol import ProtocolHandler
from .auth import Authenticator
from .api import TradingAPI, MarketDataAPI, AccountAPI, SymbolCatalog
from .utils.errors import ConnectionError, AuthenticationError

logger = logging.getLogger(__name__)


class CTraderClient:
    """Modern async cTrader client.
    
    This is the main entry point for interacting with the cTrader Open API.
    It provides a clean, high-level interface for trading, market data, and
    account management.
    
    Example:
        >>> async with CTraderClient(
        ...     client_id="YOUR_ID",
        ...     client_secret="YOUR_SECRET",
        ...     access_token="YOUR_TOKEN",
        ...     account_id=12345,
        ...     host_type="demo"
        ... ) as client:
        ...     # Place a market order
        ...     position = await client.trading.place_market_order(
        ...         symbol="EURUSD",
        ...         side=TradeSide.BUY,
        ...         volume=0.01
        ...     )
        ...     print(f"Position: {position.id}")
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        access_token: str,
        account_id: int,
        host_type: str = "demo",
        **kwargs
    ):
        """Initialize cTrader client.
        
        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            access_token: OAuth access token
            account_id: Trading account ID
            host_type: Server type ("demo" or "live")
            **kwargs: Additional configuration options
            
        Additional configuration options:
            - connection_timeout: Connection timeout (default: 30s)
            - request_timeout: Request timeout (default: 30s)
            - auth_timeout: Authentication timeout (default: 60s)
            - reconnect_enabled: Enable auto-reconnection (default: True)
            - reconnect_max_attempts: Max reconnection attempts (default: 10)
            - rate_limit_trading: Trading rate limit per second (default: 50)
            - rate_limit_historical: Historical data rate limit (default: 5)
            
        Example:
            >>> client = CTraderClient(
            ...     client_id="12345",
            ...     client_secret="secret",
            ...     access_token="token",
            ...     account_id=12345,
            ...     host_type="demo",
            ...     connection_timeout=60.0,
            ...     reconnect_max_attempts=5
            ... )
        """
        # Create configuration
        self.config = ClientConfig(
            client_id=client_id,
            client_secret=client_secret,
            access_token=access_token,
            account_id=account_id,
            host_type=host_type,
            **kwargs
        )
        
        # Validate configuration
        self.config.validate()
        
        # Core components
        self._transport: Optional[TCPTransport] = None
        self._protocol: Optional[ProtocolHandler] = None
        self._authenticator: Optional[Authenticator] = None
        
        # High-level APIs (initialized after connection)
        self.trading: Optional[TradingAPI] = None
        self.market_data: Optional[MarketDataAPI] = None
        self.account: Optional[AccountAPI] = None
        self.symbols: Optional[SymbolCatalog] = None
        
        # State
        self._connected = False
        self._authenticated = False
        self._message_task: Optional[asyncio.Task] = None
        
        # Configure logging
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    @classmethod
    def from_config(cls, config: ClientConfig) -> CTraderClient:
        """Create client from configuration object.
        
        Args:
            config: Client configuration
            
        Returns:
            CTraderClient instance
            
        Example:
            >>> config = ClientConfig.from_env()
            >>> client = CTraderClient.from_config(config)
        """
        return cls(
            client_id=config.client_id,
            client_secret=config.client_secret,
            access_token=config.access_token,
            account_id=config.account_id,
            host_type=config.host_type,
        )
    
    @classmethod
    def from_env(cls, prefix: str = "CTRADER_") -> CTraderClient:
        """Create client from environment variables.
        
        Args:
            prefix: Prefix for environment variable names
            
        Returns:
            CTraderClient instance
            
        Example:
            >>> client = CTraderClient.from_env()
            >>> # Uses CTRADER_CLIENT_ID, CTRADER_CLIENT_SECRET, etc.
        """
        config = ClientConfig.from_env(prefix)
        return cls.from_config(config)
    
    async def connect(self):
        """Connect to cTrader server and authenticate.
        
        This method:
        1. Establishes TCP connection
        2. Performs two-phase authentication
        3. Loads symbol catalog
        4. Initializes high-level APIs
        
        Raises:
            ConnectionError: If connection fails
            AuthenticationError: If authentication fails
        """
        try:
            logger.info(f"Connecting to cTrader ({self.config.host_type})...")
            
            # Create transport
            self._transport = TCPTransport(
                message_max_size=self.config.message_max_size
            )
            
            # Connect to server
            host = get_host(self.config.host_type)
            import ssl as _ssl

            ssl_ctx = None
            if self.config.use_tls:
                ssl_ctx = _ssl.create_default_context()

            await self._transport.connect(
                host,
                PROTOBUF_PORT,
                timeout=self.config.connection_timeout,
                ssl=ssl_ctx,
            )
            
            self._connected = True
            logger.info(f"Connected to {host}:{PROTOBUF_PORT}")
            
            # Create protocol handler
            self._protocol = ProtocolHandler(self._transport)
            await self._protocol.start()
            
            logger.info("Protocol handler started")
            
            # Authenticate
            self._authenticator = Authenticator(self.config, self._protocol)
            
            logger.info("Starting authentication...")
            success = await self._authenticator.authenticate(max_attempts=3)
            
            if not success:
                raise AuthenticationError("Authentication failed")
            
            self._authenticated = True
            logger.info("Authentication successful")
            
            # Initialize symbol catalog
            self.symbols = SymbolCatalog(self._protocol, self.config)
            await self.symbols.load()
            
            logger.info(f"Loaded {len(self.symbols._symbols_by_name)} symbols")
            
            # Initialize high-level APIs
            self.trading = TradingAPI(self._protocol, self.config, self.symbols)
            self.market_data = MarketDataAPI(self._protocol, self.config, self.symbols)
            self.account = AccountAPI(self._protocol, self.config)
            
            logger.info("Client ready")
        
        except Exception as e:
            logger.error(f"Connection failed: {e}", exc_info=True)
            await self.disconnect()
            raise
    
    async def disconnect(self):
        """Disconnect from cTrader server.
        
        This gracefully closes all connections and cleans up resources.
        """
        logger.info("Disconnecting...")
        
        self._authenticated = False
        self._connected = False
        
        # Stop protocol handler
        if self._protocol:
            try:
                await self._protocol.stop()
            except Exception as e:
                logger.debug(f"Error stopping protocol: {e}")
        
        # Close transport
        if self._transport:
            try:
                await self._transport.close()
            except Exception as e:
                logger.debug(f"Error closing transport: {e}")
        
        # Clear APIs
        self.trading = None
        self.market_data = None
        self.account = None
        self.symbols = None
        
        logger.info("Disconnected")
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected.
        
        Returns:
            True if connected, False otherwise
        """
        return self._connected and self._transport and self._transport.is_connected()
    
    @property
    def is_authenticated(self) -> bool:
        """Check if client is authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        return self._authenticated
    
    @property
    def is_ready(self) -> bool:
        """Check if client is ready for operations.
        
        Returns:
            True if connected and authenticated, False otherwise
        """
        return self.is_connected and self.is_authenticated
    
    # Context manager support
    async def __aenter__(self):
        """Enter async context manager.
        
        Example:
            >>> async with CTraderClient(...) as client:
            ...     await client.trading.place_market_order(...)
        """
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        await self.disconnect()
    
    def __repr__(self) -> str:
        """String representation."""
        status = []
        if self.is_connected:
            status.append("connected")
        if self.is_authenticated:
            status.append("authenticated")
        
        status_str = ", ".join(status) if status else "disconnected"
        
        return (
            f"<CTraderClient {status_str}, "
            f"account={self.config.account_id}, "
            f"host={self.config.host_type}>"
        )
