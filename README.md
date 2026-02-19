# cTrader Async Client

A modern, pure Python asyncio client library for the cTrader Open API. This library provides a clean, intuitive interface for trading operations, market data streaming, and account management.

## Features

### Core Architecture
✅ **Pure Asyncio** - No Twisted dependencies, native Python async/await  
✅ **Clean API** - Intuitive, high-level interface for common operations  
✅ **Type Safe** - Full type hints for better IDE support and type checking  
✅ **Context Managers** - Automatic connection lifecycle management  
✅ **Well Tested** - Comprehensive test coverage (48+ unit tests)  
✅ **Production Ready** - Error handling, reconnection, rate limiting

### Authentication & Session
✅ **OAuth Flow** - HTTP-based OAuth helper for initial authentication  
✅ **Token Refresh** - Automatic and manual token refresh  
✅ **cTID Profile** - User identity information retrieval  
✅ **Multi-Account** - List and switch between accounts  
✅ **Server Version** - Get cTrader API server version

### Market Data
✅ **Real-time Ticks** - Async iterators for tick streaming (single & multi-symbol)  
✅ **Order Book Depth** - Level II market data streaming with analytics  
✅ **Live Candles** - Real-time candlestick updates as they form  
✅ **Historical Candles** - OHLCV candle data retrieval  
✅ **Historical Ticks** - Tick-by-tick historical data for backtesting  
✅ **Server Timestamps** - Optional server-side timestamps on tick events

### Trading Operations
✅ **Order Types** - Market, Limit, Stop, Stop-Limit orders  
✅ **Advanced Protection** - Trailing stop, guaranteed SL, relative SL/TP  
✅ **Position Management** - Modify SL/TP, partial/close positions  
✅ **Order Management** - Modify, cancel pending orders  
✅ **Bulk Operations** - Close all, cancel all, bulk modify  
✅ **Position Lifecycle** - Track orders and deals per position

### Risk Management
✅ **Margin Calculation** - Pre-trade margin requirement calculation  
✅ **Risk Validation** - Automated risk checks before trading  
✅ **PnL Tracking** - Real-time position PnL with cost breakdown  
✅ **Server PnL** - Server-calculated PnL for accuracy  
✅ **Dynamic Leverage** - Tiered leverage schedule queries  
✅ **Margin Monitoring** - Real-time margin change events  
✅ **Margin Calls** - History and threshold configuration

### Trade History & Reporting
✅ **Deal History** - Executed trade history with time ranges  
✅ **Order History** - Historical order retrieval  
✅ **Order Details** - Comprehensive order information  
✅ **Deal Offsets** - Netting account offset tracking  
✅ **Performance Analytics** - Win rate, profit factor, statistics  
✅ **Tax Reporting** - Generate tax reporting data

### Account Management
✅ **Account Info** - Balance, equity, margin, leverage  
✅ **Full Account Data** - Comprehensive account metrics  
✅ **Margin Status** - Quick margin health check  
✅ **Cash Flow** - Deposits, withdrawals, dividends history

### Symbol & Asset Catalog
✅ **Symbol Search** - Search and filter symbols  
✅ **Symbol Details** - Full specification retrieval  
✅ **Categories** - Symbol category browsing  
✅ **Asset Classes** - Asset classification  
✅ **Conversion Symbols** - FX conversion chain discovery

### Streaming & Events
✅ **Event Bus** - Pub/sub for all server events  
✅ **Typed Events** - Normalized model events (order, position, deal)  
✅ **Auto-Reconnect** - Automatic reconnection with state recovery  
✅ **Stream Resubscription** - Automatic stream recovery after reconnect  
✅ **Backpressure** - Bounded queues with drop policies

### Infrastructure
✅ **Rate Limiting** - Token bucket algorithm for API limits  
✅ **Circuit Breaker** - Failure detection and recovery  
✅ **Retry Logic** - Exponential backoff with jitter  
✅ **Metrics** - Built-in request/response metrics  
✅ **Hooks** - Extension points for custom logic  
✅ **Logging** - Structured logging (plain or JSON)  
✅ **Watchdog** - Stale connection detection  

## Installation

```bash
pip install ctrader-async
```

Or from source:
```bash
pip install -e .

Or directly from git:
```bash
pip install "ctrader-async @ git+https://github.com/yourusername/ctrader-async.git@<commit>"
```

## Quick Start

```python
import asyncio
import ctc
from ctc import CTraderClient, TradeSide

async def main():
    # Initialize client with credentials
    async with CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"  # or "live"
    ) as client:
        
        # Place a market order
        position = await client.trading.place_market_order(
            symbol="EURUSD",
            side=TradeSide.BUY,
            volume=0.01,
            stop_loss=1.0900,
            take_profit=1.1100
        )
        print(f"Position opened: {position.id} at {position.entry_price}")
        
        # Get account info
        account = await client.account.get_info()
        print(f"Balance: {account.balance}, Equity: {account.equity}")
        
        # Get all open positions
        positions = await client.trading.get_positions()
        for pos in positions:
            print(f"{pos.symbol_name}: {pos.volume} lots, PnL: {pos.pnl_net_unrealized}")

asyncio.run(main())
```

## API Overview

### Market Data Streaming

```python
from ctc.enums import TimeFrame

# Stream real-time ticks
async with client.market_data.stream_ticks("EURUSD") as stream:
    async for tick in stream:
        print(f"Bid: {tick.bid}, Ask: {tick.ask}")

# Stream order book depth (Level II)
async with client.market_data.stream_depth("EURUSD", depth=10) as stream:
    async for snapshot in stream:
        print(f"Best Bid: {snapshot.best_bid.price}")
        print(f"Best Ask: {snapshot.best_ask.price}")
        print(f"Spread: {snapshot.spread}")
        print(f"Order Book Imbalance: {snapshot.total_bid_volume() - snapshot.total_ask_volume()}")

# Stream live candles
async with client.market_data.stream_candles("EURUSD", TimeFrame.M5) as stream:
    async for candle in stream:
        print(f"O={candle.open} H={candle.high} L={candle.low} C={candle.close}")

# Get historical candles
candles = await client.market_data.get_candles("EURUSD", TimeFrame.H1, count=100)
```

### Risk Management

```python
# Calculate margin before placing order
margin_info = await client.risk.get_expected_margin("EURUSD", volume=1.0)
print(f"Required margin: {margin_info.formatted_margin}")

# Validate trade risk
validation = await client.risk.validate_trade_risk(
    symbol="EURUSD",
    volume=1.0,
    side="BUY",
    max_risk_percent=2.0
)

if validation['valid']:
    # Safe to place order
    position = await client.trading.place_market_order("EURUSD", "BUY", 1.0)
else:
    print("Trade rejected:", validation['warnings'])

# Get position PnL details
pnl = await client.risk.get_position_pnl(position_id)
print(f"Gross PnL: {pnl.formatted_gross_pnl}")
print(f"Net PnL: {pnl.formatted_net_pnl}")
print(f"Total Costs: {pnl.total_costs}")

# Monitor margin changes
def on_margin_change(position_id, used_margin, money_digits):
    print(f"Position {position_id} margin: {used_margin}")

client.risk.subscribe_margin_events(on_margin_change)
```

### Trade History & Reporting

```python
# Get recent trade history
deals = await client.history.get_deals(days=7)
for deal in deals:
    print(f"{deal.symbol_name} {deal.side} {deal.volume} @ {deal.execution_price}")

# Track position lifecycle
position_deals = await client.history.get_deals_by_position(position_id)
avg_entry = sum(d.execution_price * d.volume for d in position_deals) / sum(d.volume for d in position_deals)

# Get performance summary
summary = await client.history.get_performance_summary(days=30)
print(f"Win Rate: {summary['win_rate']:.1f}%")
print(f"Profit Factor: {summary['profit_factor']:.2f}")
print(f"Net PnL: {summary['net_pnl']:.2f}")
print(f"Average Win: {summary['avg_win']:.2f}")
print(f"Average Loss: {summary['avg_loss']:.2f}")
```

## Production usage patterns & best practices

### 1) Client lifecycle and task supervision

- Prefer `async with CTraderClient(...) as client:` so the transport/protocol tasks are cleaned up on exit.
- Keep long-running background tasks in an `asyncio.TaskGroup` (Py 3.11+) or track tasks and cancel them on shutdown.
- Treat `asyncio.CancelledError` as a normal shutdown path and avoid swallowing it.

### 2) Backpressure and queues

This library uses bounded queues in multiple places:

- Protocol inbound queue (`ClientConfig.inbound_queue_size`)
- Tick stream queues (`ClientConfig.tick_queue_size`)

If your consumer is slower than the incoming stream:

- Increase queue sizes for short bursts
- Or enable dropping to stay “latest only”:
  - `ClientConfig.drop_inbound_when_full=True` for inbound protocol frames
  - Use `MultiTickStream(..., coalesce_latest=True)` for ticks

### 3) Avoid doing I/O per tick

In streaming loops, avoid doing network I/O per tick (e.g., repeated symbol lookups). Cache symbol metadata once before entering the loop:

```python
symbol = await client.symbols.get_symbol("EURUSD")
pip_size = symbol.pip_size if symbol else 0.0001

async with client.market_data.stream_ticks("EURUSD") as stream:
    async for tick in stream:
        spread_pips = (tick.ask - tick.bid) / pip_size
        ...
```

### 4) Reconnect + retry

- Reconnect is handled in `CTraderClient` via `utils.ReconnectManager`.
- For idempotent operations (e.g., refetching positions), use `utils.retry_async` with a conservative policy.

```python
from ctc.utils import retry_async, RetryPolicy

policy = RetryPolicy(max_attempts=5, base_delay=0.2, max_delay=3.0)

positions = await retry_async(lambda: client.trading.get_positions(), policy=policy)
```

### 5) Prefer event-driven state over polling

For bots, enable:

- `ModelEventBridge` to translate execution events into `models.*`
- `TradingStateCacheUpdater` to keep `TradingAPI` caches warm

Then use `client.events` subscriptions instead of polling `get_positions()` every second.

### 6) Operational configuration (logging, watchdog, token refresh)

The client now supports production-focused runtime controls:

- Structured logging (`plain` or `json`)
- Stale-connection watchdog (auto-reconnect trigger)
- Background token auto-refresh + account re-auth

Constructor example:

```python
client = CTraderClient(
    client_id="...",
    client_secret="...",
    access_token="...",
    refresh_token="...",  # required for auto-refresh
    account_id=12345,
    host_type="live",

    # logging
    configure_logging=True,
    log_level="INFO",
    log_format="json",  # "plain" | "json"

    # watchdog
    watchdog_check_interval=5.0,
    stale_connection_timeout=90.0,  # None => heartbeat_interval * 3

    # token auto-refresh
    token_auto_refresh_enabled=True,
    token_refresh_margin_seconds=60.0,
    token_refresh_default_expires_in=3600,
)
```

Equivalent environment variables:

```bash
export CTRADER_CONFIGURE_LOGGING=true
export CTRADER_LOG_LEVEL=INFO
export CTRADER_LOG_FORMAT=json

export CTRADER_WATCHDOG_CHECK_INTERVAL=5
export CTRADER_STALE_CONNECTION_TIMEOUT=90

export CTRADER_REFRESH_TOKEN="..."
export CTRADER_TOKEN_AUTO_REFRESH_ENABLED=true
export CTRADER_TOKEN_REFRESH_MARGIN_SECONDS=60
export CTRADER_TOKEN_REFRESH_DEFAULT_EXPIRES_IN=3600
```

Runtime events emitted by these features:

- `client.connection_stale`
- `auth.token_refreshed`
- `auth.token_refresh_failed`

## Streaming Market Data

```python
async def stream_ticks():
    async with CTraderClient(...) as client:
        # Stream real-time tick data
        async with client.market_data.stream_ticks("EURUSD") as stream:
            async for tick in stream:
                print(f"EURUSD Bid: {tick.bid:.5f}, Ask: {tick.ask:.5f}")
                
                # Process tick data
                if tick.bid > 1.1000:
                    break

asyncio.run(stream_ticks())
```

## Advanced Usage

### Managing Positions

```python
async def manage_positions():
    async with CTraderClient(...) as client:
        # Get all positions
        positions = await client.trading.get_positions()
        
        # Modify position SL/TP
        for pos in positions:
            await client.trading.modify_position(
                position_id=pos.id,
                stop_loss=pos.entry_price - 0.0050,
                take_profit=pos.entry_price + 0.0100
            )
        
        # Close specific position
        await client.trading.close_position(positions[0].id)
        
        # Close all positions
        await client.trading.close_all_positions()
```

### Historical Data

```python
async def get_historical_data():
    async with CTraderClient(...) as client:
        # Get candlestick data
        candles = await client.market_data.get_candles(
            symbol="EURUSD",
            timeframe="H1",
            count=100
        )
        
        for candle in candles:
            print(f"{candle.timestamp}: O={candle.open} H={candle.high} L={candle.low} C={candle.close}")
```

### Events (recommended patterns)

The client exposes a lightweight async `EventBus` at `client.events`. This is the preferred integration point for bots/agents, logging, and state synchronization.

There are a few layers of events:

- `protobuf.envelope`: raw protobuf envelope (advanced / low-level)
- `execution.*`: typed execution lifecycle events derived from `ProtoOAExecutionEvent`
- `model.*`: normalized `ctc.models` dataclasses (optional bridge)

```python
import asyncio
from ctc import CTraderClient

async def main():
    async with CTraderClient.from_env(auto_enable_features=True) as client:
        # 1) Subscribe to raw envelopes (debug / observability)
        client.events.on("protobuf.envelope", lambda env: None)

        # 2) Subscribe to normalized domain models (stable interface)
        async def on_order(order):
            print("order update", order.id, order.symbol_name, order.volume)

        async def on_position(pos):
            print("position update", pos.id, pos.symbol_name, pos.volume)

        async def on_deal(deal):
            print("deal", deal.deal_id, deal.symbol_name, deal.volume)

        client.events.on("model.order", on_order)
        client.events.on("model.position", on_position)
        client.events.on("model.deal", on_deal)

        # keep process alive
        await asyncio.Event().wait()

asyncio.run(main())
```

To enable the model bridge + state cache updater automatically, construct the client with `auto_enable_features=True` (see `CTraderClient`), or enable them manually:

```python
from ctc.utils import ModelEventBridge, TradingStateCacheUpdater

bridge = ModelEventBridge(client.events, client.symbols, client.trading)
bridge.enable()

updater = TradingStateCacheUpdater(client.events, client.trading)
updater.enable()
```

## Observability & debugging

### Logging

The library uses Python's standard `logging` module. For troubleshooting, enable debug logs for the relevant namespaces:

```python
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger("ctc").setLevel(logging.DEBUG)
# Or narrow it down:
# logging.getLogger("ctc.protocol").setLevel(logging.DEBUG)
# logging.getLogger("ctc.transport").setLevel(logging.DEBUG)
```

### Correlation IDs (`clientMsgId`)

Most request/response flows are correlated via `clientMsgId` (a UUID) at the protobuf envelope layer.

You can observe them via:
- debug logs in `ProtocolHandler.send_request()`
- hooks (below)

### Built-in metrics (`client.metrics`)

The client exposes a lightweight metrics collector at `client.metrics` (see `utils.metrics`). It tracks:
- request count + bytes sent
- response count
- latency min/max/sum/count (from hook timing)
- inbound protocol drops (when `drop_inbound_when_full=True`)
- tick drops (when tick queues are full)
- reconnect attempts/successes

```python
snap = client.metrics.snapshot()
print(snap.requests_sent, snap.latency_count, snap.tick_dropped)
```

### Auto-reconnect + state recovery

If `ClientConfig.reconnect_enabled=True`, the client will attempt to reconnect on transport receive errors.
Recovery is **refresh-only** (safe by default):
- reconnect + re-auth
- reload symbols
- refresh account info
- refresh positions + orders

Events emitted on `client.events`:
- `client.reconnect.attempt`
- `client.reconnect.success`
- `client.reconnect.fatal` (non-retriable failure, e.g. authentication)

This implementation intentionally does **not** resend non-idempotent trading requests.

#### Tick stream resubscription on reconnect

If you created tick streams via `client.market_data.stream_ticks(...)` or `client.market_data.stream_ticks_multi(...)`,
active streams are automatically **resubscribed** after a successful reconnect.

Important behavior:
- Stream iterators remain **alive** during the brief unsubscribe/resubscribe window (they do not raise `StopAsyncIteration`).
- Resubscription is **best-effort**: if one stream fails to resubscribe, others still continue.
- Only spot tick subscriptions are auto-resubscribed. Execution events already flow without an explicit subscribe in this library.

If you build custom stream-like objects and want the same behavior, implement an async `resubscribe(protocol, symbols)` method
and register it with the client’s internal registry (see `utils.stream_registry`).

### Hook points (metrics, tracing, risk gates)

The client owns a `HookManager` at `client.hooks`. Internally, `ProtocolHandler.send_request()` can call these named hooks:

- `protocol.pre_send_request`
- `protocol.post_send_request`
- `protocol.post_response`

Example: record timings and sizes for every request:

```python
import time
from ctc import CTraderClient

async def main():
    async with CTraderClient.from_env() as client:
        inflight: dict[str, float] = {}

        async def pre(ctx):
            inflight[ctx.data["request_type"]] = time.perf_counter()

        async def post_send(ctx):
            # request_type, client_msg_id, bytes_sent
            pass

        async def post_resp(ctx):
            rt = ctx.data["request_type"]
            dt = time.perf_counter() - inflight.pop(rt, time.perf_counter())
            print("request", rt, "took", dt)

        client.hooks.register("protocol.pre_send_request", pre)
        client.hooks.register("protocol.post_send_request", post_send)
        client.hooks.register("protocol.post_response", post_resp)

        # any API call will now trigger hooks
        await client.account.get_info()
```

### Raw event tap

For deep debugging (or building custom decoders), subscribe to `protobuf.envelope`:

```python
async def log_envelope(env):
    print("payloadType=", env.payloadType, "clientMsgId=", getattr(env, "clientMsgId", ""))

client.events.on("protobuf.envelope", log_envelope)
```

## Architecture

```
ctc/
├── transport/          # Low-level TCP/protocol handling
├── protocol/           # Message correlation & dispatch
├── auth/              # Authentication state machine
├── api/               # High-level APIs (trading, market data, account)
├── streams/           # Async iterators for real-time data
├── utils/             # Rate limiting, reconnection, errors
└── models/            # Data classes for positions, orders, etc.
```

## Configuration

Configuration can be provided via:
1. Constructor arguments
2. Environment variables
3. A config file (via `ClientConfig.from_file`)

A `CTraderClient.from_env()` helper exists and is the recommended default for deployments (12-factor style).

### Environment Variables

```bash
CTRADER_CLIENT_ID=your_client_id
CTRADER_CLIENT_SECRET=your_client_secret
CTRADER_ACCESS_TOKEN=your_access_token
CTRADER_ACCOUNT_ID=12345
CTRADER_HOST_TYPE=demo  # or live

# Extra connection diagnostics (verbose connect/reconnect logs)
CTRADER_CONNECTION_DEBUG=1
```

### Configuration File

```python
from ctc import ClientConfig

config = ClientConfig.from_file("ctrader_config.json")
client = CTraderClient.from_config(config)
```

## Error Handling

```python
from ctc.utils.errors import (
    ConnectionError,
    AuthenticationError,
    TradingError,
    MarketClosedError,
    RateLimitError
)

async def safe_trading():
    try:
        async with CTraderClient(...) as client:
            position = await client.trading.place_market_order(...)
    except AuthenticationError as e:
        print(f"Auth failed: {e}")
    except TradingError as e:
        print(f"Trading error: {e.code} - {e.description}")
    except MarketClosedError:
        print("Market is closed")
    except RateLimitError as e:
        print(f"Rate limited, retry after {e.retry_after}s")
```

## API Reference

### CTraderClient

Main client class providing access to all APIs.

**Methods:**
- `connect()` - Establish connection and authenticate
- `disconnect()` - Close connection gracefully
- `from_env()` - Build client from environment variables (`CTRADER_*`)
- `from_config()` - Build client from a `ClientConfig`
- Context manager support: `async with CTraderClient(...) as client:`

**Properties:**
- `trading` - Trading operations API
- `market_data` - Market data and streaming API
- `account` - Account information API
- `symbols` - Symbol catalog API

### Session API

**Methods:**
- `get_available_accounts()` - List accessible accounts
- `logout()` - Logout from current account
- `refresh_token()` - Refresh access token
- `get_ctid_profile()` - Get cTID user profile
- `get_server_version()` - Get API server version

### Trading API

**Methods:**
- `place_market_order()` - Place market order
- `place_limit_order()` - Place limit order (with advanced protection)
- `place_stop_order()` - Place stop order (with advanced protection)
- `place_stop_limit_order()` - Place stop-limit order (with advanced protection)
- `modify_position()` - Modify position SL/TP
- `modify_order()` - Amend pending order
- `close_position()` - Close position (full or partial)
- `cancel_order()` - Cancel pending order
- `get_positions()` - Get all open positions
- `get_orders()` - Get all pending orders
- `get_orders_by_position()` - Get orders linked to position
- `list_all_orders()` - Get historical orders
- `close_all_positions()` - Close all positions
- `cancel_all_orders()` - Cancel all pending orders
- `close_positions_bulk()` - Close multiple positions
- `cancel_orders_bulk()` - Cancel multiple orders

### Market Data API

**Methods:**
- `stream_ticks()` - Stream real-time tick data (single symbol)
- `stream_ticks_multi()` - Stream ticks for multiple symbols
- `stream_depth()` - Stream order book depth (Level II)
- `stream_candles()` - Stream live candlestick updates
- `get_candles()` - Get historical candlestick data
- `get_tick_data()` - Get historical tick data

### Risk Management API

**Methods:**
- `get_expected_margin()` - Calculate required margin
- `validate_trade_risk()` - Validate trade against risk limits
- `get_position_pnl()` - Get position PnL breakdown
- `get_position_pnl_realtime()` - Get server-calculated PnL
- `get_margin_calls()` - Get margin call history
- `get_dynamic_leverage()` - Get tiered leverage schedule
- `update_margin_call()` - Update margin call thresholds
- `subscribe_margin_events()` - Monitor margin changes
- `subscribe_margin_call_events()` - Monitor margin calls

### History API

**Methods:**
- `get_deals()` - Get deal/trade history
- `get_deals_by_position()` - Get deals for specific position
- `get_deal_offsets()` - Get netting account offsets
- `get_order_details()` - Get detailed order information
- `get_orders_by_position()` - Get orders linked to position
- `get_performance_summary()` - Get performance analytics

### Account API

**Methods:**
- `get_info()` - Get basic account information
- `get_full_account_info()` - Get comprehensive account data
- `get_margin_status()` - Get quick margin summary
- `get_cash_flow_history()` - Get deposits/withdrawals history
- `refresh_cache()` - Refresh cached account data

### Symbol Catalog

**Methods:**
- `get_all()` - Get all available symbols
- `get_symbol()` - Get symbol by name
- `get_symbol_by_id()` - Get symbol by ID
- `get_symbol_details_by_id()` - Get fresh symbol details from server
- `search()` - Search symbols by pattern
- `get_categories()` - Get symbol categories
- `get_symbols_by_category()` - Get symbols in category
- `get_conversion_symbols()` - Get FX conversion symbols

### Asset Catalog

**Methods:**
- `get_all()` - Get all assets
- `get_asset()` - Get asset by name
- `get_asset_by_id()` - Get asset by ID
- `get_asset_classes()` - Get asset class groupings

## Testing

Run tests with pytest:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest --cov=ctc tests/
```

## Examples

See the `examples/` directory for complete working examples:

**Basic Usage:**
- `basic_usage.py` - Basic connection and account/symbol queries
- `market_orders.py` - Placing and managing orders/positions
- `event_driven_bot.py` - Event-driven bot skeleton using `client.events`
- `advanced_protection_orders.py` - Advanced order protection fields (trailing/GSL/relative SL/TP)

**Market Data:**
- `streaming_ticks.py` - Real-time tick data streaming (single symbol)
- `multi_symbol_ticks.py` - Real-time multi-symbol streaming (coalescing latest)
- `historical_data.py` - Fetching historical candles
- `order_book_depth.py` - **NEW!** Level II market data streaming and analysis
- `live_candle_streaming.py` - **NEW!** Real-time candlestick streaming with patterns

**Risk & Reporting:**
- `margin_and_risk_management.py` - **NEW!** Margin calculation, risk validation, PnL tracking
- `trade_history_and_reporting.py` - **NEW!** Deal history, performance analytics, tax reports

**Infrastructure:**
- `reconnect_stream_recovery.py` - Simulated disconnect/reconnect with continued stream consumption

## Requirements

- Python 3.10+
- `protobuf` - Protocol buffer serialization
  - Recommended: `protobuf>=4.25.0,<6.0`
  - Why `<6.0`? Many environments using `grpcio-status` / Google client libraries currently constrain protobuf to `<6.0`.
    This package stays compatible while still benefiting from newer protobuf fixes (including Python 3.12 deprecation cleanups).
- `python-dotenv` - Environment variable loading (optional)

## Comparison with OpenApiPy

| Feature | OpenApiPy (Twisted) | ctc |
|---------|---------------------|---------------|
| **Async Framework** | Twisted (Deferreds) | Native asyncio |
| **API Style** | Low-level callbacks | High-level async/await |
| **Dependencies** | Twisted (heavy) | stdlib only |
| **Type Hints** | None | Full coverage |
| **Testing** | Difficult | Easy with mocks |
| **Documentation** | Minimal | Comprehensive |
| **Streaming** | Callbacks | Async iterators |
| **Error Handling** | Twisted Failures | Python exceptions |

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/ctrader-async.git
cd ctrader-async

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## Support

- Documentation: See [docs/API_REFERENCE.md](docs/API_REFERENCE.md)
- Issues: https://github.com/yourusername/ctrader-async/issues

## Security

For security vulnerabilities, please see [SECURITY.md](SECURITY.md).

## Changelog

See CHANGELOG.md for version history.
