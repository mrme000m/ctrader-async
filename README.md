# cTrader Async Client

A modern, pure Python asyncio client library for the cTrader Open API. This library provides a clean, intuitive interface for trading operations, market data streaming, and account management.

## Features

✅ **Pure Asyncio** - No Twisted dependencies, native Python async/await  
✅ **Clean API** - Intuitive, high-level interface for common operations  
✅ **Type Safe** - Full type hints for better IDE support and type checking  
✅ **Event Streaming** - Async iterators for ticks, positions, and orders  
✅ **Context Managers** - Automatic connection lifecycle management  
✅ **Well Tested** - Comprehensive test coverage with mocked transports  
✅ **Production Ready** - Error handling, reconnection, rate limiting  

## Installation

```bash
pip install ctrader-async
```

Or from source:
```bash
pip install -e .
```

## Quick Start

```python
import asyncio
from ctrader_async import CTraderClient, TradeSide

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

### Event Callbacks

```python
async def handle_events():
    async with CTraderClient(...) as client:
        # Register event handlers
        @client.on_position_opened
        async def on_position(position):
            print(f"New position: {position.id}")
        
        @client.on_position_closed
        async def on_close(position):
            print(f"Position closed: {position.id}, PnL: {position.pnl_net_unrealized}")
        
        # Keep running
        await asyncio.Event().wait()
```

## Architecture

```
ctrader_async/
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
3. Configuration file

### Environment Variables

```bash
CTRADER_CLIENT_ID=your_client_id
CTRADER_CLIENT_SECRET=your_client_secret
CTRADER_ACCESS_TOKEN=your_access_token
CTRADER_ACCOUNT_ID=12345
CTRADER_HOST_TYPE=demo  # or live
```

### Configuration File

```python
from ctrader_async import ClientConfig

config = ClientConfig.from_file("ctrader_config.json")
client = CTraderClient.from_config(config)
```

## Error Handling

```python
from ctrader_async.utils.errors import (
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
- `stream_ticks()` - Stream real-time tick data (async iterator)
- `get_candles()` - Get historical candlestick data
- `get_quote()` - Get current bid/ask quote
- `subscribe_to_events()` - Subscribe to market events

### Account API

**Methods:**
- `get_info()` - Get account information
- `get_positions_summary()` - Get positions summary
- `get_orders_summary()` - Get orders summary
- `get_history()` - Get trade history

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
pytest --cov=ctrader_async tests/
```

## Examples

See the `examples/` directory for complete working examples:
- `basic_usage.py` - Basic connection and trading
- `market_orders.py` - Different order types
- `streaming_ticks.py` - Real-time data streaming
- `position_management.py` - Managing positions
- `event_handling.py` - Event-driven patterns
- `advanced_patterns.py` - Advanced use cases

## Requirements

- Python 3.10+
- `protobuf` - Protocol buffer serialization
  - Recommended: `protobuf>=4.25.0,<6.0`
  - Why `<6.0`? Many environments using `grpcio-status` / Google client libraries currently constrain protobuf to `<6.0`.
    This package stays compatible while still benefiting from newer protobuf fixes (including Python 3.12 deprecation cleanups).
- `python-dotenv` - Environment variable loading (optional)

## Comparison with OpenApiPy

| Feature | OpenApiPy (Twisted) | ctrader_async |
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
