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

### Planned
- WebSocket transport option
- Advanced order types (trailing stop, etc.)
- Position hedging support
- Trade history retrieval
- Performance metrics
- Reconnection state recovery
- Circuit breaker pattern
- More comprehensive examples
- Integration tests
- Performance benchmarks
