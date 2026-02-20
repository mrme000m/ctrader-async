"""
Main cTrader async client.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional, Any

from .config import ClientConfig
from .transport import TCPTransport, get_host, PROTOBUF_PORT, WEBSOCKET_AVAILABLE
if WEBSOCKET_AVAILABLE:
    from .transport import AsyncWebSocketTransport
from .protocol import ProtocolHandler
from .auth import Authenticator
from .api import TradingAPI, MarketDataAPI, AccountAPI, SymbolCatalog, AssetCatalog, RiskAPI, HistoryAPI, SessionAPI
from .utils.errors import ConnectionError, AuthenticationError
from .utils.reconnect import ReconnectManager, ReconnectConfig
from .utils.metrics import MetricsCollector
from .utils.stream_registry import StreamRegistry
from .utils.tick_store import TickStore
from .utils.fx_converter import DefaultAssetConverter
from .utils.logging import setup_logging, create_structured_logger

logger = logging.getLogger(__name__)

from .utils.debug import connection_debug_enabled

# Optional BetterStack integration
try:
    from .integrations import BetterStackHandler, betterstack_enabled
except ImportError:
    BetterStackHandler = None  # type: ignore
    betterstack_enabled = lambda: False  # type: ignore


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
        use_websocket: bool = False,
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
            use_websocket: Use WebSocket transport instead of TCP (default: False)
            **kwargs: Additional configuration options
            
        Additional configuration options:
            - connection_timeout: Connection timeout (default: 30s)
            - request_timeout: Request timeout (default: 30s)
            - auth_timeout: Authentication timeout (default: 60s)
            - reconnect_enabled: Enable auto-reconnection (default: True)
            - reconnect_max_attempts: Max reconnection attempts (default: 10)
            - rate_limit_trading: Trading rate limit per second (default: 50)
            - rate_limit_historical: Historical data rate limit (default: 5)
            - websocket_ping_interval: WebSocket ping interval in seconds (default: 20)
            - websocket_ping_timeout: WebSocket ping timeout in seconds (default: 10)
            
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
        # Store transport type preference
        self._use_websocket = use_websocket
        if use_websocket and not WEBSOCKET_AVAILABLE:
            raise ImportError(
                "WebSocket transport requested but 'websockets' library is not installed. "
                "Install it with: pip install websockets"
            )
        
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
        
        # Core components (transport type determined at connect time)
        self._transport: Optional[TCPTransport | AsyncWebSocketTransport] = None
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
        self._watchdog_task: asyncio.Task | None = None
        self._token_refresh_task: asyncio.Task | None = None
        self._reconnect_manager: ReconnectManager | None = None
        self._closing: bool = False
        self._hooks_attached: bool = False
        self._last_inbound_monotonic: float = time.monotonic()
        self._token_expires_in: int | None = None

        # Tracks active streams that can be resubscribed after reconnect
        self._stream_registry = StreamRegistry()

        # Optional model normalization bridge + cache updater
        self.model_bridge = None
        self.state_cache_updater = None
        self._auto_model_bridge = bool(auto_model_bridge)
        self._auto_cache_updater = bool(auto_cache_updater)
        
        # BetterStack integration (optional, opt-in)
        self._betterstack: Optional[Any] = None
        self._betterstack_enabled = False
        
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
        
        # Setup logging (with optional BetterStack)
        if getattr(self.config, "configure_logging", False):
            setup_logging(
                self.config.log_level,
                log_format=self.config.log_format,
                betterstack=self.config.betterstack_enabled
            )
        
        # Initialize BetterStack if enabled in config
        if self.config.betterstack_enabled and BetterStackHandler is not None:
            self._init_betterstack()
    
    @classmethod
    def from_config(cls, config: ClientConfig, **kwargs) -> CTraderClient:
        """Create client from configuration object.

        Args:
            config: Client configuration
            **kwargs: Additional keyword arguments forwarded to the constructor
                      (e.g. use_websocket, auto_model_bridge, auto_cache_updater).

        Returns:
            CTraderClient instance

        Example:
            >>> config = ClientConfig.from_env()
            >>> client = CTraderClient.from_config(config, use_websocket=True)
        """
        # Build a kwargs dict from every field on the config dataclass so that
        # all optional settings (timeouts, rate limits, etc.) are preserved.
        import dataclasses
        config_kwargs = {
            f.name: getattr(config, f.name)
            for f in dataclasses.fields(config)
        }
        # Caller-supplied kwargs take precedence
        config_kwargs.update(kwargs)
        return cls(**config_kwargs)
    
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
    
    def _init_betterstack(self) -> None:
        """Initialize BetterStack integration.
        
        This method sets up BetterStack logging if configured.
        It's called automatically during initialization if
        betterstack_enabled is True in the configuration.
        """
        if BetterStackHandler is None:
            logger.debug("BetterStack integration not available")
            return
        
        if not self.config.betterstack_configured:
            logger.debug(
                "BetterStack not fully configured (missing ingest_host or source_token)"
            )
            return
        
        try:
            from .integrations import BetterStackConfig
            
            bs_config = BetterStackConfig(
                ingest_host=self.config.betterstack_ingest_host,
                source_token=self.config.betterstack_source_token,
                heartbeat_url=self.config.betterstack_heartbeat_url,
                log_level=self.config.betterstack_log_level,
                service_name=self.config.betterstack_service_name,
                service_version=getattr(self, "__version__", "unknown"),
                environment=self.config.betterstack_environment,
            )
            
            self._betterstack = BetterStackHandler(bs_config)
            self._betterstack_enabled = True
            
            logger.info(
                f"BetterStack integration enabled for {bs_config.service_name} "
                f"in {bs_config.environment} environment"
            )
            
        except Exception as e:
            logger.warning(f"Failed to initialize BetterStack: {e}")
            self._betterstack_enabled = False
            self._betterstack = None
    
    async def _send_betterstack_log(self, event: dict[str, Any]) -> None:
        """Send a log event to BetterStack if enabled."""
        if self._betterstack_enabled and self._betterstack:
            try:
                await self._betterstack.send_log(event)
            except Exception:
                pass  # Fail silently to not disrupt main flow
    
    async def _send_betterstack_heartbeat(self) -> None:
        """Send a heartbeat to BetterStack if enabled."""
        if self._betterstack_enabled and self._betterstack:
            try:
                await self._betterstack.send_heartbeat()
            except Exception:
                pass  # Fail silently
    
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
            transport_type = "WebSocket" if self._use_websocket else "TCP"
            logger.info(f"Connecting to cTrader via {transport_type} ({self.config.host_type})...")
            
            # Create transport based on preference
            if self._use_websocket:
                # WebSocket transport
                ws_ping_interval = getattr(self.config, 'websocket_ping_interval', 20.0)
                ws_ping_timeout = getattr(self.config, 'websocket_ping_timeout', 10.0)
                
                self._transport = AsyncWebSocketTransport(
                    ping_interval=ws_ping_interval,
                    ping_timeout=ws_ping_timeout
                )
                logger.info(f"Using WebSocket transport (ping_interval={ws_ping_interval}s)")
            else:
                # TCP transport (default)
                self._transport = TCPTransport(
                    message_max_size=self.config.message_max_size
                )
                logger.info("Using TCP transport")
            
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
            logger.info(f"Connected to {host}:{PROTOBUF_PORT} via {transport_type}")
            
            # Create protocol handler
            self._protocol = ProtocolHandler(self._transport, config=self.config)
            await self._protocol.start()
            self._last_inbound_monotonic = time.monotonic()

            # Attach metrics to hooks + internal protocol events (idempotent)
            try:
                if not self._hooks_attached:
                    self.hooks.register("protocol.post_send_request", self.metrics.on_post_send_request)
                    self.hooks.register("protocol.post_response", self.metrics.on_post_response)
                    self._hooks_attached = True

                if getattr(self._protocol, "events", None) is not None:
                    self._protocol.events.on("protocol.inbound_dropped", self.metrics.on_inbound_dropped)
                    self._protocol.events.on("stream.tick_dropped", self.metrics.on_tick_dropped)
                    self._protocol.events.on("protobuf.envelope", self._on_protocol_inbound)
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
            
            # Initialize asset converter for pip value calculations
            self.fx_converter = DefaultAssetConverter(
                symbols=self.symbols,
                assets=self.assets,
                ticks=self.ticks,
            )

            # Optional helper to keep conversion-related tick subscriptions alive
            from .utils.conversion_subscriptions import ConversionSubscriptionManager
            self.conversion_subscriptions = ConversionSubscriptionManager(market_data=self.market_data, tick_store=self.ticks)
            self.account = AccountAPI(self._protocol, self.config, client=self)

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

            self._start_background_tasks()

            # Send success log to BetterStack
            if self._betterstack_enabled:
                await self._send_betterstack_log({
                    "message": f"cTrader client connected successfully",
                    "level": "info",
                    "event": "client.connected",
                    "account_id": self.config.account_id,
                    "host_type": self.config.host_type,
                    "transport": transport_type,
                    "symbols_loaded": len(self.symbols._symbols_by_name) if self.symbols else 0,
                })
                # Send heartbeat if configured
                await self._send_betterstack_heartbeat()

            logger.info("Client ready")
        
        except Exception as e:
            logger.error(f"Connection failed: {e}", exc_info=True)
            # Send error to BetterStack
            if self._betterstack_enabled:
                await self._send_betterstack_log({
                    "message": f"cTrader client connection failed: {e}",
                    "level": "error",
                    "event": "client.connection_failed",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "account_id": self.config.account_id,
                    "host_type": self.config.host_type,
                })
            await self.disconnect()
            raise
    
    async def _setup_typed_event_handlers(self):
        """Register internal protobuf handlers that emit typed events."""
        if not self._protocol or not self.symbols:
            return

        from .transport import ProtocolFraming
        from .models import Tick
        from .utils.typed_events import TickEvent, execution_events_from_payload
        from .messages.OpenApiMessages_pb2 import (
            ProtoOASpotEvent,
            ProtoOAExecutionEvent,
            ProtoOATrailingSLChangedEvent,
            ProtoOAOrderErrorEvent,
            ProtoOATraderUpdatedEvent,
            ProtoOASymbolChangedEvent,
            ProtoOAAccountDisconnectEvent,
            ProtoOAAccountsTokenInvalidatedEvent,
            ProtoOAClientDisconnectEvent,
        )

        # ── Tick handler ───────────────────────────────────────────────────
        async def on_spot(envelope):
            payload = ProtocolFraming.extract_payload(envelope)
            symbol_name = None
            try:
                info = await self.symbols.get_symbol_by_id(int(payload.symbolId))
                symbol_name = info.name if info else None
            except Exception:
                symbol_name = None
            if symbol_name is None:
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
            try:
                await self.ticks.set(tick)
            except Exception:
                pass
            await self.events.emit("tick", evt)

        # ── Execution handler ──────────────────────────────────────────────
        async def on_execution(envelope):
            payload = ProtocolFraming.extract_payload(envelope)
            for event_name, event_obj in execution_events_from_payload(payload, envelope=envelope):
                await self.events.emit(event_name, event_obj)

        # ── Trailing SL changed ────────────────────────────────────────────
        async def on_trailing_sl_changed(envelope):
            payload = ProtocolFraming.extract_payload(envelope)
            position_id = getattr(payload, "positionId", None)
            new_sl = getattr(payload, "stopLossPrice", None)
            logger.info(f"Trailing SL updated for position {position_id}: {new_sl}")
            await self.events.emit("position.trailing_sl_changed", {
                "position_id": position_id,
                "stop_loss_price": new_sl,
                "payload": payload,
            })

        # ── Order error ────────────────────────────────────────────────────
        async def on_order_error(envelope):
            payload = ProtocolFraming.extract_payload(envelope)
            error_code = getattr(payload, "errorCode", "UNKNOWN")
            description = getattr(payload, "description", "")
            order_id = getattr(payload, "orderId", None)
            logger.error(f"Order error for order {order_id}: {error_code} - {description}")
            await self.events.emit("order.error", {
                "order_id": order_id,
                "error_code": error_code,
                "description": description,
                "payload": payload,
            })

        # ── Trader updated (balance/equity change) ─────────────────────────
        async def on_trader_updated(envelope):
            payload = ProtocolFraming.extract_payload(envelope)
            logger.debug("Trader info updated by server")
            # Invalidate account cache so next get_info() re-fetches from server
            try:
                if self.account:
                    self.account._cached_info = None
                    self.account._cached_full_info = None
            except Exception:
                pass
            await self.events.emit("account.trader_updated", {"payload": payload})

        # ── Symbol changed (spec update) ───────────────────────────────────
        async def on_symbol_changed(envelope):
            payload = ProtocolFraming.extract_payload(envelope)
            symbol_ids = list(getattr(payload, "symbolId", []) or [])
            logger.info(f"Symbol spec changed for ids={symbol_ids}")
            # Refresh each affected symbol in the catalog cache
            try:
                if self.symbols:
                    for sid in symbol_ids:
                        await self.symbols.get_symbol_details_by_id(int(sid))
            except Exception as e:
                logger.debug(f"Could not refresh symbol cache: {e}")
            await self.events.emit("market.symbol_changed", {
                "symbol_ids": symbol_ids,
                "payload": payload,
            })

        # ── Account disconnect ─────────────────────────────────────────────
        async def on_account_disconnect(envelope):
            payload = ProtocolFraming.extract_payload(envelope)
            account_id = getattr(payload, "ctidTraderAccountId", "?")
            logger.warning(f"Server sent ProtoOAAccountDisconnectEvent for account {account_id}")
            await self.events.emit("account.disconnected", {
                "account_id": account_id,
                "payload": payload,
            })

        # ── Token invalidated ──────────────────────────────────────────────
        async def on_token_invalidated(envelope):
            payload = ProtocolFraming.extract_payload(envelope)
            account_ids = list(getattr(payload, "ctidTraderAccountIds", []) or [])
            reason = getattr(payload, "reason", "unknown")
            logger.error(
                f"Server sent ProtoOAAccountsTokenInvalidatedEvent "
                f"— token invalidated for accounts {account_ids}: {reason}"
            )
            
            # Trigger re-authentication if our account is affected
            if self.config.account_id in account_ids:
                logger.warning(f"Our account {self.config.account_id} token invalidated, triggering re-auth")
                try:
                    # Use token auto-refresh if available
                    if self._should_enable_token_auto_refresh():
                        refresh_tok = getattr(self.config, "refresh_token", None)
                        if refresh_tok and self.session:
                            tokens = await self.session.refresh_token(refresh_tok)
                            new_access_token = str(tokens.get("access_token", "") or "")
                            if new_access_token:
                                self.config.access_token = new_access_token
                                new_refresh_token = str(tokens.get("refresh_token", "") or "")
                                if new_refresh_token:
                                    self.config.refresh_token = new_refresh_token
                                await self._reauth_account_with_current_token()
                                logger.info("Token refreshed and account re-authenticated after invalidation")
                    else:
                        # Fall back to triggering a reconnect
                        await self.events.emit("auth.reauth_required", {
                            "account_ids": account_ids,
                            "reason": reason,
                        })
                except Exception as e:
                    logger.error(f"Failed to re-authenticate after token invalidation: {e}")
            
            await self.events.emit("auth.token_invalidated", {
                "account_ids": account_ids,
                "reason": reason,
                "payload": payload,
            })

        # ── Client disconnect (common-level) ───────────────────────────────
        async def on_client_disconnect(envelope):
            payload = ProtocolFraming.extract_payload(envelope)
            reason = getattr(payload, "reason", None)
            logger.warning(f"Server sent ProtoOAClientDisconnectEvent reason={reason}")
            await self.events.emit("client.disconnect", {
                "reason": reason,
                "payload": payload,
            })

        # ── Register all handlers ──────────────────────────────────────────
        from .messages.OpenApiMessages_pb2 import (
            ProtoOAMarginChangedEvent,
            ProtoOAMarginCallUpdateEvent,
            ProtoOAMarginCallTriggerEvent,
        )

        async def on_margin_changed(envelope):
            try:
                payload = ProtocolFraming.extract_payload(envelope)
                money_digits = getattr(payload, "moneyDigits", 2)
                divisor = 10 ** money_digits
                await self.events.emit("risk.margin_changed", {
                    "position_id": getattr(payload, "positionId", None),
                    "used_margin": getattr(payload, "usedMargin", 0) / divisor,
                    "money_digits": money_digits,
                    "payload": payload,
                })
            except Exception as e:
                logger.debug(f"on_margin_changed error: {e}")

        async def on_margin_call_update(envelope):
            try:
                payload = ProtocolFraming.extract_payload(envelope)
                money_digits = getattr(payload, "moneyDigits", 2)
                divisor = 10 ** money_digits
                await self.events.emit("risk.margin_call_update", {
                    "event_type": "MARGIN_CALL_UPDATE",
                    "equity": getattr(payload, "equity", 0) / divisor,
                    "margin": getattr(payload, "margin", 0) / divisor,
                    "margin_level": getattr(payload, "marginLevel", 0.0),
                    "money_digits": money_digits,
                    "payload": payload,
                })
            except Exception as e:
                logger.debug(f"on_margin_call_update error: {e}")

        async def on_margin_call_trigger(envelope):
            try:
                payload = ProtocolFraming.extract_payload(envelope)
                money_digits = getattr(payload, "moneyDigits", 2)
                divisor = 10 ** money_digits
                await self.events.emit("risk.margin_call_trigger", {
                    "event_type": "MARGIN_CALL_TRIGGER",
                    "equity": getattr(payload, "equity", 0) / divisor,
                    "margin": getattr(payload, "margin", 0) / divisor,
                    "margin_level": getattr(payload, "marginLevel", 0.0),
                    "money_digits": money_digits,
                    "payload": payload,
                })
            except Exception as e:
                logger.debug(f"on_margin_call_trigger error: {e}")

        self._protocol.dispatcher.register(ProtoOASpotEvent().payloadType, on_spot)
        self._protocol.dispatcher.register(ProtoOAExecutionEvent().payloadType, on_execution)
        self._protocol.dispatcher.register(ProtoOATrailingSLChangedEvent().payloadType, on_trailing_sl_changed)
        self._protocol.dispatcher.register(ProtoOAOrderErrorEvent().payloadType, on_order_error)
        self._protocol.dispatcher.register(ProtoOATraderUpdatedEvent().payloadType, on_trader_updated)
        self._protocol.dispatcher.register(ProtoOASymbolChangedEvent().payloadType, on_symbol_changed)
        self._protocol.dispatcher.register(ProtoOAAccountDisconnectEvent().payloadType, on_account_disconnect)
        self._protocol.dispatcher.register(ProtoOAAccountsTokenInvalidatedEvent().payloadType, on_token_invalidated)
        self._protocol.dispatcher.register(ProtoOAClientDisconnectEvent().payloadType, on_client_disconnect)
        self._protocol.dispatcher.register(ProtoOAMarginChangedEvent().payloadType, on_margin_changed)
        self._protocol.dispatcher.register(ProtoOAMarginCallUpdateEvent().payloadType, on_margin_call_update)
        self._protocol.dispatcher.register(ProtoOAMarginCallTriggerEvent().payloadType, on_margin_call_trigger)

    async def _on_protocol_inbound(self, _evt):
        self._last_inbound_monotonic = time.monotonic()

    def _start_background_tasks(self) -> None:
        if self._watchdog_task is None or self._watchdog_task.done():
            self._watchdog_task = asyncio.create_task(self._stale_connection_watchdog_loop())

        if self._should_enable_token_auto_refresh():
            if self._token_refresh_task is None or self._token_refresh_task.done():
                self._token_refresh_task = asyncio.create_task(self._token_auto_refresh_loop())

    def _should_enable_token_auto_refresh(self) -> bool:
        return bool(
            getattr(self.config, "token_auto_refresh_enabled", False)
            and getattr(self.config, "refresh_token", None)
        )

    async def _stale_connection_watchdog_loop(self) -> None:
        try:
            check_interval = max(0.5, float(getattr(self.config, "watchdog_check_interval", 5.0)))
            stale_timeout = getattr(self.config, "stale_connection_timeout", None)
            if stale_timeout is None:
                # Use configurable multiplier (default 10x) with 300s minimum
                # to avoid false positives during trade bursts
                multiplier = float(getattr(self.config, "stale_connection_threshold_multiplier", 10.0))
                stale_timeout = max(300.0, float(self.config.heartbeat_interval) * multiplier)
            stale_timeout = float(stale_timeout)

            while not self._closing:
                await asyncio.sleep(check_interval)

                if not self.is_connected:
                    continue

                idle_seconds = time.monotonic() - self._last_inbound_monotonic
                if idle_seconds <= stale_timeout:
                    continue

                logger.warning(
                    "Stale connection detected: no inbound messages for %.1fs (threshold %.1fs)",
                    idle_seconds,
                    stale_timeout,
                )

                try:
                    await self.events.emit(
                        "client.connection_stale",
                        {"idle_seconds": idle_seconds, "threshold_seconds": stale_timeout},
                    )
                except Exception:
                    pass

                self._last_inbound_monotonic = time.monotonic()
                await self._on_protocol_connection_lost(
                    {"reason": "stale_connection", "idle_seconds": idle_seconds}
                )
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Watchdog loop failed: {e}", exc_info=True)

    async def _reauth_account_with_current_token(self) -> None:
        if not self._protocol:
            return

        from .messages.OpenApiMessages_pb2 import ProtoOAAccountAuthReq, ProtoOAAccountAuthRes

        req = ProtoOAAccountAuthReq()
        req.ctidTraderAccountId = self.config.account_id
        req.accessToken = self.config.access_token

        response = await self._protocol.send_request(
            req,
            timeout=self.config.auth_timeout,
            request_type="AccountAuth",
        )
        if not isinstance(response, ProtoOAAccountAuthRes):
            raise AuthenticationError(f"Unexpected account auth response: {type(response)}")

    async def _token_auto_refresh_loop(self) -> None:
        try:
            margin = max(0.0, float(getattr(self.config, "token_refresh_margin_seconds", 60.0)))

            while not self._closing:
                expires_in = self._token_expires_in
                if expires_in is None:
                    expires_in = int(getattr(self.config, "token_refresh_default_expires_in", 3600))
                delay_seconds = max(0.5, float(expires_in) - margin)
                await asyncio.sleep(delay_seconds)

                if self._closing:
                    break
                if not self.session:
                    continue

                refresh_tok = getattr(self.config, "refresh_token", None)
                if not refresh_tok:
                    logger.warning("Token auto-refresh disabled at runtime: missing refresh_token")
                    return

                try:
                    tokens = await self.session.refresh_token(refresh_tok)
                    new_access_token = str(tokens.get("access_token", "") or "")
                    new_refresh_token = str(tokens.get("refresh_token", "") or "")
                    new_expires_in = int(tokens.get("expires_in", 0) or 0)

                    if not new_access_token:
                        raise AuthenticationError("Token refresh response missing access_token")

                    self.config.access_token = new_access_token
                    if new_refresh_token:
                        self.config.refresh_token = new_refresh_token
                    if new_expires_in > 0:
                        self._token_expires_in = new_expires_in

                    await self._reauth_account_with_current_token()

                    logger.info("Access token auto-refreshed and account re-authenticated")
                    try:
                        await self.events.emit(
                            "auth.token_refreshed",
                            {
                                "expires_in": self._token_expires_in,
                                "has_refresh_token": bool(self.config.refresh_token),
                            },
                        )
                    except Exception:
                        pass
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.error(f"Token auto-refresh failed: {e}", exc_info=True)
                    try:
                        await self.events.emit("auth.token_refresh_failed", {"error": e})
                    except Exception:
                        pass
                    await asyncio.sleep(30.0)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Token refresh loop failed: {e}", exc_info=True)

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
            # Send reconnect success to BetterStack
            if self._betterstack_enabled:
                await self._send_betterstack_log({
                    "message": "cTrader client reconnected successfully",
                    "level": "info",
                    "event": "client.reconnected",
                    "account_id": self.config.account_id,
                    "host_type": self.config.host_type,
                })
        except AuthenticationError as e:
            logger.error(f"Reconnect failed fatally (authentication): {e}")
            # Send fatal reconnect failure to BetterStack
            if self._betterstack_enabled:
                await self._send_betterstack_log({
                    "message": f"cTrader client reconnect failed fatally: {e}",
                    "level": "error",
                    "event": "client.reconnect_fatal",
                    "error_type": "AuthenticationError",
                    "error_message": str(e),
                    "account_id": self.config.account_id,
                    "host_type": self.config.host_type,
                })
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

        if self._watchdog_task and not self._watchdog_task.done():
            self._watchdog_task.cancel()
            try:
                await self._watchdog_task
            except asyncio.CancelledError:
                pass
        self._watchdog_task = None

        if self._token_refresh_task and not self._token_refresh_task.done():
            self._token_refresh_task.cancel()
            try:
                await self._token_refresh_task
            except asyncio.CancelledError:
                pass
        self._token_refresh_task = None

        # Send disconnect log to BetterStack before cleanup
        if self._betterstack_enabled and self._connected:
            try:
                await self._send_betterstack_log({
                    "message": "cTrader client disconnecting",
                    "level": "info",
                    "event": "client.disconnecting",
                    "account_id": self.config.account_id,
                    "host_type": self.config.host_type,
                })
            except Exception:
                pass
        
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
        
        # Shutdown BetterStack handler
        if self._betterstack:
            try:
                await self._betterstack.shutdown()
            except Exception:
                pass
            self._betterstack = None
            self._betterstack_enabled = False
        
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
