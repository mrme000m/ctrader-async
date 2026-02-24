# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Live candles (ProtoOALiveTrendbarEvent)** – new `CandleStream`
  class and associated market_data helpers for full real‑time candlestick
  updates.  Implements subscription/unsubscription messages and delta‑
  decoding of trendbar payloads.

#### Session & Authentication
- **Token Refresh** - Automatic and manual token refresh support
  - `session.refresh_token()` - Refresh access token via protobuf API
  - `OAuthHelper` class for HTTP-based OAuth flow
  - `get_auth_uri()`, `exchange_code()`, `refresh_token_http()` methods
  - Token auto-refresh background task with configurable margin

- **cTID Profile** - User identity information
  - `session.get_ctid_profile()` - Get cTID user profile details
  - Returns user_id, nickname, email, preferred language

- **Account Management** - Enhanced multi-account support
  - `session.get_available_accounts()` - List accessible accounts
  - `session.switch_account()` - Switch between accounts
  - `session.get_server_version()` - Get API server version

#### Symbol & Asset Management
- **Symbol Details by ID** - Server-side symbol lookup
  - `symbols.get_symbol_details_by_id()` - Fresh symbol details from server
  - Updates local cache with authoritative data

- **Conversion Symbols** - Currency conversion chain discovery
  - `symbols.get_conversion_symbols()` - Get symbols for asset conversion
  - Used for FX rate calculations between any two assets

- **Asset Classes** - Asset categorization
  - `assets.get_asset_classes()` - Get asset class groupings
  - Currencies, Commodities, Indices, Stocks, Crypto

#### Trading Enhancements
- **Orders by Position** - Complete position lifecycle tracking
  - `trading.get_orders_by_position()` - Get all orders for a position
  - `history.get_orders_by_position()` - Historical order retrieval

- **Historical Order List** - Comprehensive order history
  - `trading.list_all_orders()` - Get orders across time ranges
  - Supports pagination for large histories

- **Advanced Order Features** - Extended order capabilities
  - `subscribeToSpotTimestamp` flag in tick streams
  - Coalescing latest tick support in multi-symbol streams

#### Market Data
- **Historical Tick Data** - Tick-by-tick price history
  - `market_data.get_tick_data()` - Raw tick data for backtesting
  - Supports BID and ASK quote types
  - Cumulative timestamp and delta price decoding

#### Risk Management
- **Margin Call Updates** - Dynamic margin call configuration
  - `risk.update_margin_call()` - Update margin call thresholds
  - Configure MARGIN_CALL and STOP_OUT levels

#### Infrastructure
- **Production Runtime Controls**
  - Structured logging (plain or JSON format)
  - Stale-connection watchdog with auto-reconnect
  - Background token auto-refresh
  - Connection debug mode for troubleshooting

#### Event Handling
- **All Server-Push Events** - Complete event coverage
  - `position.trailing_sl_changed` - Trailing stop adjustments
  - `order.error` - Async order error notifications
  - `account.trader_updated` - Account info changes
  - `market.symbol_changed` - Symbol specification updates
  - `account.disconnected` - Server-initiated disconnect
  - `auth.token_invalidated` - Token invalidation events
  - `client.disconnect` - Connection-level disconnect

### Changed

#### Documentation
- Updated API_REFERENCE.md with all new methods
- Added comprehensive examples for all features
- Improved inline docstrings throughout codebase

### Fixed

- Fixed `kwargs` scope bug in `client.connect()` method
- Fixed incorrect method name in `validate_trade_risk()` (now uses `get_full_account_info()`)
- Fixed event handler import casing for `ProtoOATrailingSLChangedEvent`
- **Protocol heartbeat** - Added explicit `ProtoHeartbeatEvent` sending in `ProtocolHandler._heartbeat_loop()`
- **Rate limiting** - Fixed `MarketDataAPI` to use separate rate limiters:
  - `_historical_rate_limiter` (5 req/s) for historical data requests
  - `_trading_rate_limiter` (50 req/s) for streaming/subscription operations
- **Token invalidation** - Enhanced `on_token_invalidated()` handler to trigger automatic re-authentication when account token is invalidated
- **Margin event extractors** - Fixed margin event handlers to use `ProtocolFraming.extract_payload()` instead of non-existent `self._protobuf.extract()`
- **Error handling** - Added `Authenticator._get_retry_after()` method to extract rate limit retry delays from error responses
- All identified gaps from audit documents now addressed

---

## [0.1.0] - 2024-02-06

### Added
- Initial release of ctrader-async
- Pure asyncio implementation (no Twisted dependency)
- Clean high-level API for trading operations
- Market data streaming with async iterators
- Account management API
- Symbol catalog with caching
- Request/response correlation with timeout management
- Message dispatching system
- Clean authentication state machine
- Rate limiting (token bucket algorithm)
- Exponential backoff reconnection logic
- Context manager support for automatic cleanup
- Comprehensive type hints
- Full error handling with custom exceptions
- Examples for common use cases
- Complete documentation

### Features

#### Core
- Pure asyncio TCP transport
- Protocol buffer message framing
- Request correlation with client message IDs
- Automatic timeout handling
- Background cleanup of stale requests

#### Trading
- Market orders with SL/TP
- Limit orders
- Stop orders
- Stop-limit orders
- Position management (modify SL/TP, close)
- Order management (modify, cancel)
- Bulk operations (close all, cancel all)

#### Market Data
- Real-time tick streaming (async iterator)
- Historical candlestick data
- Symbol catalog with search
- Quote snapshots

#### Account
- Account information
- Balance and equity tracking
- Margin calculations

#### Risk Management
- Expected margin calculation
- Position PnL tracking
- Margin call monitoring
- Dynamic leverage queries

#### Trade History
- Deal history retrieval
- Performance analytics
- Order details

### Improvements over OpenApiPy
- No Twisted dependency (pure asyncio)
- Clean async/await API (no callbacks)
- Type hints throughout
- Better error handling
- Modern Python patterns (context managers, async iterators)
- Easier testing with transport abstraction
- Comprehensive documentation
- Better performance (native async, no thread synchronization)
