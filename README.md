# cTrader Async Client

A modern, pure Python asyncio client library for the cTrader Open API. This library provides a clean, intuitive interface for trading operations, market data streaming, and account management.

## Features

### Core
✅ **Pure Asyncio** - No Twisted dependencies, native Python async/await  
✅ **Clean API** - Intuitive, high-level interface for common operations  
✅ **Type Safe** - Full type hints for better IDE support and type checking  
✅ **Context Managers** - Automatic connection lifecycle management  
✅ **Well Tested** - Comprehensive test coverage (43+ unit tests)  
✅ **Production Ready** - Error handling, reconnection, rate limiting

### Market Data
✅ **Real-time Ticks** - Async iterators for tick streaming (single & multi-symbol)  
✅ **Order Book Depth** - Level II market data streaming with analytics  
✅ **Live Candles** - Real-time candlestick updates as they form  
✅ **Historical Data** - OHLCV candle data retrieval

### Trading & Risk
✅ **Order Management** - Market, Limit, Stop orders with protection  
✅ **Position Management** - Open, modify, close positions with bulk operations  
✅ **Risk Management** - Pre-trade margin calculation and validation  
✅ **PnL Tracking** - Real-time position PnL monitoring with cost breakdown

### Reporting & Analytics
✅ **Trade History** - Deal/trade history with flexible time ranges  
✅ **Performance Analytics** - Automated win rate, profit factor, statistics  
✅ **Position Lifecycle** - Track all fills and executions per position  
✅ **Tax Reporting** - Generate tax reporting data and statements  

## Installation

```bash
pip install ctrader-async
```

Or from source:
```bash
pip install -e .

Or directly from git:
```bash
pip install "ctrader-async @ git+https://github.com/mrme000m/ctrader-async.git@<commit>"
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

### Trading API

**Methods:**
- `place_market_order()` - Place market order
- `place_limit_order()` - Place limit order
- `place_stop_order()` - Place stop order
- `place_stop_limit_order()` - Place stop-limit order
- `modify_position()` - Modify position SL/TP
- `close_position()` - Close position (full or partial)
- `cancel_order()` - Cancel pending order
- `get_positions()` - Get all open positions
- `get_orders()` - Get all pending orders
- `close_all_positions()` - Close all positions
- `cancel_all_orders()` - Cancel all pending orders

### Market Data API

**Methods:**
- `stream_ticks()` - Stream real-time tick data for one symbol (async iterator)
- `stream_ticks_multi()` - Stream ticks for multiple symbols (supports coalescing latest)
- `get_candles()` - Get historical candlestick data

### Account API

**Methods:**
- `get_info()` - Get account information (cached; `refresh=True` forces server fetch)

### Symbols API

**Methods:**
- `get_all()` - Get all available symbols
- `get_symbol()` - Get specific symbol details
- `search()` - Search symbols by name/pattern

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

Contributions are welcome! Please see CONTRIBUTING.md for guidelines.

## Support

- Documentation: https://ctrader-async.readthedocs.io
- Issues: https://github.com/yourusername/ctrader-async/issues
- Discord: https://discord.gg/ctrader-async

## Changelog

See CHANGELOG.md for version history.
