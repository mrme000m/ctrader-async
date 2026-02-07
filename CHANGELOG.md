# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

### Improvements over OpenApiPy
- No Twisted dependency (pure asyncio)
- Clean async/await API (no callbacks)
- Type hints throughout
- Better error handling
- Modern Python patterns (context managers, async iterators)
- Easier testing with transport abstraction
- Comprehensive documentation
- Better performance (native async, no thread synchronization)

## [Unreleased]

### Added

#### Market Data Enhancements
- **Order Book Depth Streaming (Level II)** - Real-time order book data with incremental updates
  - `DepthStream` class for streaming market depth
  - `DepthQuote` and `DepthSnapshot` models with built-in analytics
  - `stream_depth()` method in MarketDataAPI
  - Analytics: spread calculation, volume aggregation, order book imbalance
  - Example: `examples/order_book_depth.py`

- **Live Candle Streaming** - Real-time candlestick updates as candles form
  - `CandleStream` class for streaming live candles
  - `stream_candles()` method in MarketDataAPI
  - Support for all timeframes (M1, M5, H1, D1, etc.)
  - Example: `examples/live_candle_streaming.py` with pattern detection

#### Risk Management APIs
- **Pre-trade Margin Calculation** - Calculate margin requirements before placing orders
  - `RiskAPI` class with comprehensive risk management methods
  - `get_expected_margin()` - Calculate required margin for proposed trades
  - `MarginInfo` model with formatting helpers
  - Prevents insufficient margin errors

- **Position PnL Tracking** - Detailed profit/loss breakdown
  - `get_position_pnl()` - Get gross/net PnL, swap, commission breakdown
  - `PositionPnL` model with cost analysis
  - Real-time PnL monitoring capabilities

- **Risk Validation** - Automated pre-trade risk checks
  - `validate_trade_risk()` - Validate trades against risk parameters
  - Configurable risk limits (max % of equity, margin usage)
  - Detailed validation results with warnings

- **Margin Monitoring** - Real-time margin tracking
  - `subscribe_margin_events()` - Monitor margin changes in real-time
  - `get_margin_calls()` - Retrieve margin call history
  - `MarginCall` model for margin call tracking
  - Example: `examples/margin_and_risk_management.py`

#### Trade History & Reporting
- **Deal History Retrieval** - Access executed trade history
  - `HistoryAPI` class for trade history and reporting
  - `get_deals()` - Retrieve deal history with flexible time ranges
  - `get_deals_by_position()` - Track all executions for a specific position
  - Support for date range and last N days queries

- **Performance Analytics** - Automated trading performance metrics
  - `get_performance_summary()` - Calculate win rate, profit factor, statistics
  - Metrics: total deals, wins/losses, avg win/loss, profit factor
  - Symbol-based performance breakdown
  - Time-based analysis (daily, hourly)

- **Order Details** - Detailed order information retrieval
  - `get_order_details()` - Get comprehensive order information
  - Position lifecycle tracking
  - Example: `examples/trade_history_and_reporting.py` with tax reporting

### Enhanced

#### Streaming Infrastructure
- All stream classes now support reconnect recovery via stream registry
- Bounded queues with backpressure handling for all streams
- Configurable queue sizes per stream type
- Consistent async context manager pattern across all streams

#### Model Enhancements
- Added 7 new model classes: `DepthQuote`, `DepthSnapshot`, `MarginInfo`, `PositionPnL`, `MarginCall`
- All models include formatting helpers and datetime conversion
- Full type hints and comprehensive docstrings

#### Client Integration
- Added `client.risk` - Risk management API
- Added `client.history` - Trade history API
- Seamless integration with existing client architecture
- Proper cleanup and teardown in disconnect flow

#### Documentation
- Complete API reference documentation (`docs/API_REFERENCE.md`)
- 4 new comprehensive example files
- 24+ usage examples covering all new features
- Updated README with feature overview and quick start guides

#### Testing
- Added 43 unit tests covering all new models and calculations
- Tests for edge cases (empty data, zero values, etc.)
- Integration test placeholders for live testing
- All tests passing

### Planned
- WebSocket transport option
- Token refresh and multi-account support
- Symbol categories and asset classes
- Advanced order types enhancements
- Position hedging support
- Circuit breaker pattern
- Performance benchmarks
