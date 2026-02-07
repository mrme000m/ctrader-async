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
from .api import TradingAPI, MarketDataAPI, AccountAPI, SymbolCatalog, AssetCatalog, RiskAPI, HistoryAPI, SessionAPI
from .utils.errors import ConnectionError, AuthenticationError
from .utils.reconnect import ReconnectManager, ReconnectConfig
from .utils.metrics import MetricsCollector
from .utils.stream_registry import StreamRegistry
from .utils.tick_store import TickStore

logger = logging.getLogger(__name__)

from .utils.debug import connection_debug_enabled


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
        *,
        auto_model_bridge: bool = False,
        auto_cache_updater: bool = False,
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

        # Extension points for bots/agents
        from .utils import EventBus, HookManager
        self.events = EventBus()
        self.hooks = HookManager()

        # Built-in metrics (optional, but attached by default)
        self.metrics = MetricsCollector()

        # Best-effort tick cache (used for conversions)
        self.ticks = TickStore()
        self.conversion_subscriptions = None

        self._reconnect_task: asyncio.Task | None = None
        self._reconnect_manager: ReconnectManager | None = None
        self._closing: bool = False
        self._hooks_attached: bool = False

        # Tracks active streams that can be resubscribed after reconnect
        self._stream_registry = StreamRegistry()

        # Optional model normalization bridge + cache updater
        self.model_bridge = None
        self.state_cache_updater = None
        self._auto_model_bridge = bool(auto_model_bridge)
        self._auto_cache_updater = bool(auto_cache_updater)
        
        # High-level APIs (initialized after connection)
        self.trading: Optional[TradingAPI] = None
        self.market_data: Optional[MarketDataAPI] = None
        self.account: Optional[AccountAPI] = None
        self.symbols: Optional[SymbolCatalog] = None
        self.assets: Optional[AssetCatalog] = None
        self.risk: Optional[RiskAPI] = None
        self.history: Optional[HistoryAPI] = None
        self.session: Optional[SessionAPI] = None
        
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
        if self.is_ready:
            return

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
            self._protocol = ProtocolHandler(self._transport, config=self.config)
            await self._protocol.start()

            # Attach metrics to hooks + internal protocol events (idempotent)
            try:
                if not self._hooks_attached:
                    self.hooks.register("protocol.post_send_request", self.metrics.on_post_send_request)
                    self.hooks.register("protocol.post_response", self.metrics.on_post_response)
                    self._hooks_attached = True

                if getattr(self._protocol, "events", None) is not None:
                    self._protocol.events.on("protocol.inbound_dropped", self.metrics.on_inbound_dropped)
                    self._protocol.events.on("stream.tick_dropped", self.metrics.on_tick_dropped)
            except Exception:
                pass

            # Setup reconnect manager
            self._reconnect_manager = ReconnectManager(
                ReconnectConfig(
                    enabled=bool(getattr(self.config, "reconnect_enabled", True)),
                    max_attempts=int(getattr(self.config, "reconnect_max_attempts", 10)),
                    base_delay=float(getattr(self.config, "reconnect_base_delay", 1.0)),
                    max_delay=float(getattr(self.config, "reconnect_max_delay", 300.0)),
                )
            )

            # If protocol reports connection loss, attempt reconnect
            try:
                if getattr(self._protocol, "events", None) is not None:
                    self._protocol.events.on("protocol.connection_lost", self._on_protocol_connection_lost)
            except Exception:
                pass

            # Default event emission for raw envelopes (bot/agent friendly)
            self._protocol.dispatcher.register_default(
                lambda envelope: self.events.emit("protobuf.envelope", envelope)
            )

            logger.info("Protocol handler started")
            
            # Authenticate
            self._authenticator = Authenticator(self.config, self._protocol)
            
            logger.info("Starting authentication (application + account)...")
            success = await self._authenticator.authenticate(max_attempts=3)
            
            if not success:
                raise AuthenticationError("Authentication failed")
            
            self._authenticated = True
            logger.info("Authentication successful")
            
            # Initialize asset + symbol catalogs
            self.assets = AssetCatalog(self._protocol, self.config)
            await self.assets.load()

            self.symbols = SymbolCatalog(self._protocol, self.config)
            await self.symbols.load()

            logger.info(f"Loaded {len(self.symbols._symbols_by_name)} symbols")

            # Typed event emission (ticks, execution)
            await self._setup_typed_event_handlers()
            
            # Initialize high-level APIs
            self.trading = TradingAPI(self._protocol, self.config, self.symbols)
            self.market_data = MarketDataAPI(self._protocol, self.config, self.symbols, client=self)
            self.risk = RiskAPI(self._protocol, self.config, self.symbols, client=self)
            self.history = HistoryAPI(self._protocol, self.config, self.symbols, client=self)
            self.session = SessionAPI(self._protocol, self.config, client=self)

            # Optional helper to keep conversion-related tick subscriptions alive
            from .utils.conversion_subscriptions import ConversionSubscriptionManager
            self.conversion_subscriptions = ConversionSubscriptionManager(market_data=self.market_data, tick_store=self.ticks)
            self.account = AccountAPI(self._protocol, self.config)

            # Provide hook manager to APIs (optional)
            self.trading.hooks = self.hooks
            self.market_data.hooks = self.hooks
            self.account.hooks = self.hooks

            # Prepare (but do not auto-enable) model event bridge
            from .utils.model_bridge import ModelEventBridge
            self.model_bridge = ModelEventBridge(self.events, self.symbols, self.trading)

            # Prepare (but do not auto-enable) trading cache updater
            from .utils.state_cache import TradingStateCacheUpdater
            self.state_cache_updater = TradingStateCacheUpdater(self.events, self.trading)

            # Auto-enable if requested
            if self._auto_model_bridge and self.model_bridge:
                self.model_bridge.enable()
            if self._auto_cache_updater and self.state_cache_updater:
                # Cache updater assumes model events exist
                if not self._auto_model_bridge and self.model_bridge:
                    self.model_bridge.enable()
                self.state_cache_updater.enable()

            logger.info("Client ready")
        
        except Exception as e:
            logger.error(f"Connection failed: {e}", exc_info=True)
            await self.disconnect()
            raise
    
    async def _setup_typed_event_handlers(self):
        """Register internal protobuf handlers that emit typed events."""
        if not self._protocol or not self.symbols:
            return

        from .transport import ProtocolFraming
        from .models import Tick
        from .utils.typed_events import TickEvent, execution_events_from_payload
        from .messages.OpenApiMessages_pb2 import ProtoOASpotEvent, ProtoOAExecutionEvent

        async def on_spot(envelope):
            payload = ProtocolFraming.extract_payload(envelope)
            # Resolve symbol name via catalog if possible
            symbol_name = None
            try:
                info = await self.symbols.get_symbol_by_id(int(payload.symbolId))
                symbol_name = info.name if info else None
            except Exception:
                symbol_name = None

            if symbol_name is None:
                # fallback: try to resolve from local cache
                symbol_name = getattr(payload, "symbolName", "") or str(payload.symbolId)

            tick = Tick(
                symbol_id=int(payload.symbolId),
                symbol_name=str(symbol_name),
                bid=getattr(payload, "bid", 0) / 100000.0,
                ask=getattr(payload, "ask", 0) / 100000.0,
                timestamp=getattr(payload, "timestamp", 0),
            )
            evt = TickEvent(
                tick=tick,
                symbol_id=tick.symbol_id,
                symbol_name=tick.symbol_name,
                timestamp=tick.timestamp,
                payload=payload,
                envelope=envelope,
            )
            # Update last tick cache
            try:
                await self.ticks.set(tick)
            except Exception:
                pass

            await self.events.emit("tick", evt)

        async def on_execution(envelope):
            payload = ProtocolFraming.extract_payload(envelope)
            for event_name, event_obj in execution_events_from_payload(payload, envelope=envelope):
                await self.events.emit(event_name, event_obj)

        # Register handlers on dispatcher
        self._protocol.dispatcher.register(ProtoOASpotEvent().payloadType, on_spot)
        self._protocol.dispatcher.register(ProtoOAExecutionEvent().payloadType, on_execution)

    async def _on_protocol_connection_lost(self, evt):
        # Avoid reconnect loops during explicit shutdown
        if self._closing:
            return
        if not self.config.reconnect_enabled:
            return
        if self._reconnect_task and not self._reconnect_task.done():
            return
        self._reconnect_task = asyncio.create_task(self._reconnect_loop())

    async def _reconnect_loop(self) -> None:
        """Reconnect with backoff and perform refresh-only state recovery.

        Correctness rules:
        - never retry/resent non-idempotent trading requests
        - only rebuild connection + refresh server-authoritative state
        """
        if self._reconnect_manager is None:
            return

        async def _attempt():
            if connection_debug_enabled():
                logger.warning("Reconnect attempt starting")
            else:
                logger.debug("Reconnect attempt starting")
            await self.events.emit("client.reconnect.attempt", {})
            await self.metrics.on_reconnect_attempt({})

            # fully rebuild client connection
            try:
                await self.disconnect()
            except Exception:
                pass
            await self.connect()

            # refresh-only recovery
            try:
                if self.account:
                    await self.account.get_info(refresh=True)
                if self.trading:
                    await self.trading.refresh_positions()
                    await self.trading.refresh_orders()

                # Resubscribe active streams (best-effort)
                if self._protocol and self.symbols:
                    await self._stream_registry.resubscribe_all(protocol=self._protocol, symbols=self.symbols)
            except Exception:
                # best-effort
                pass

            if connection_debug_enabled():
                logger.warning("Reconnect successful; running recovery")
            else:
                logger.debug("Reconnect successful; running recovery")
            await self.events.emit("client.reconnect.success", {})
            await self.metrics.on_reconnect_success({})

        def _should_retry(exc: Exception) -> bool:
            # Authentication failures are not transient; do not loop forever.
            if isinstance(exc, AuthenticationError):
                logger.error(f"Reconnect will NOT retry due to authentication failure: {exc}")
                return False
            logger.debug(f"Reconnect will retry after error: {type(exc).__name__}: {exc}")
            return True

        try:
            await self._reconnect_manager.connect_with_retry(_attempt, should_retry=_should_retry)
        except AuthenticationError as e:
            logger.error(f"Reconnect failed fatally (authentication): {e}")
            # Surface a terminal reconnect failure event.
            try:
                await self.events.emit("client.reconnect.fatal", {"error": e})
            except Exception:
                pass
            raise

    async def disconnect(self):
        """Disconnect from cTrader server.
        
        This gracefully closes all connections and cleans up resources.
        """
        logger.info("Disconnecting...")

        # Cancel reconnect loop if running
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
        self._reconnect_task = None

        self._closing = True

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
        self.assets = None
        self.risk = None
        self.history = None
        self.session = None
        if self.conversion_subscriptions is not None:
            try:
                await self.conversion_subscriptions.stop()
            except Exception:
                pass
        self.conversion_subscriptions = None
        
        logger.info("Disconnected")
        self._closing = False
    
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
