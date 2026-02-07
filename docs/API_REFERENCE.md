# API Reference

Complete API reference for the cTrader Async Client.

## Table of Contents

- [Client](#client)
- [Market Data API](#market-data-api)
- [Trading API](#trading-api)
- [Risk Management API](#risk-management-api)
- [History API](#history-api)
- [Account API](#account-api)
- [Models](#models)
- [Enums](#enums)

---

## Client

### CTraderClient

Main client class for interacting with cTrader Open API.

```python
from ctc import CTraderClient

client = CTraderClient(
    client_id: str,
    client_secret: str,
    access_token: str,
    account_id: int,
    host_type: str = "demo",  # or "live"
    config: Optional[ClientConfig] = None
)
```

**Context Manager Usage:**
```python
async with CTraderClient(...) as client:
    # Client automatically connects and disconnects
    await client.trading.place_market_order(...)
```

**Properties:**
- `client.market_data` - Market data API
- `client.trading` - Trading API
- `client.risk` - Risk management API
- `client.history` - Trade history API
- `client.account` - Account API
- `client.symbols` - Symbol catalog
- `client.assets` - Asset catalog

---

## Market Data API

### stream_ticks()

Stream real-time tick data for a symbol.

```python
async with client.market_data.stream_ticks(symbol: str) as stream:
    async for tick in stream:
        # tick.bid, tick.ask, tick.timestamp
        ...
```

**Parameters:**
- `symbol` (str): Symbol name (e.g., "EURUSD")

**Returns:** AsyncIterator[Tick]

### stream_ticks_multi()

Stream real-time ticks for multiple symbols.

```python
async with client.market_data.stream_ticks_multi(
    symbols: list[str],
    coalesce_latest: bool = True
) as stream:
    async for tick in stream:
        # tick.symbol_name, tick.bid, tick.ask
        ...
```

**Parameters:**
- `symbols` (list[str]): List of symbol names
- `coalesce_latest` (bool): Keep only latest tick per symbol when under load

**Returns:** AsyncIterator[Tick]

### stream_depth()

Stream real-time order book depth (Level II market data).

```python
async with client.market_data.stream_depth(
    symbol: str,
    depth: int = 10
) as stream:
    async for snapshot in stream:
        # snapshot.bids, snapshot.asks, snapshot.spread
        ...
```

**Parameters:**
- `symbol` (str): Symbol name
- `depth` (int): Number of price levels (default: 10)

**Returns:** AsyncIterator[DepthSnapshot]

**DepthSnapshot Properties:**
- `bids` - List of bid quotes (sorted descending)
- `asks` - List of ask quotes (sorted ascending)
- `best_bid` - Highest bid quote
- `best_ask` - Lowest ask quote
- `spread` - Bid-ask spread
- `total_bid_volume(levels)` - Total bid volume
- `total_ask_volume(levels)` - Total ask volume

### stream_candles()

Stream real-time candlestick data as candles form.

```python
from ctc.enums import TimeFrame

async with client.market_data.stream_candles(
    symbol: str,
    timeframe: TimeFrame
) as stream:
    async for candle in stream:
        # candle.open, candle.high, candle.low, candle.close
        ...
```

**Parameters:**
- `symbol` (str): Symbol name
- `timeframe` (TimeFrame): Candle timeframe (M1, M5, H1, etc.)

**Returns:** AsyncIterator[Candle]

### get_candles()

Get historical candlestick data.

```python
candles = await client.market_data.get_candles(
    symbol: str,
    timeframe: TimeFrame,
    from_timestamp: Optional[int] = None,
    to_timestamp: Optional[int] = None,
    count: Optional[int] = None
)
```

**Parameters:**
- `symbol` (str): Symbol name
- `timeframe` (TimeFrame): Candle timeframe
- `from_timestamp` (int, optional): Start time in milliseconds
- `to_timestamp` (int, optional): End time in milliseconds
- `count` (int, optional): Number of candles (alternative to timestamps)

**Returns:** list[Candle]

---

## Trading API

### place_market_order()

Place a market order.

```python
position = await client.trading.place_market_order(
    symbol: str,
    side: str,  # "BUY" or "SELL"
    volume: float,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
    label: Optional[str] = None,
    comment: Optional[str] = None
)
```

**Returns:** Position

### place_limit_order()

Place a limit order.

```python
order = await client.trading.place_limit_order(
    symbol: str,
    side: str,
    volume: float,
    limit_price: float,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None
)
```

**Returns:** Order

### get_positions()

Get all open positions.

```python
positions = await client.trading.get_positions()
```

**Returns:** list[Position]

### get_orders()

Get all pending orders.

```python
orders = await client.trading.get_orders()
```

**Returns:** list[Order]

### close_position()

Close a position.

```python
await client.trading.close_position(position_id: int, volume: Optional[float] = None)
```

### modify_position()

Modify position stop loss / take profit.

```python
await client.trading.modify_position(
    position_id: int,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None
)
```

### cancel_order()

Cancel a pending order.

```python
await client.trading.cancel_order(order_id: int)
```

---

## Risk Management API

### get_expected_margin()

Calculate expected margin for a proposed trade.

```python
margin_info = await client.risk.get_expected_margin(
    symbol: str,
    volume: float,
    order_type: Optional[str] = None
)
```

**Returns:** MarginInfo
- `margin` - Required margin amount
- `formatted_margin` - Formatted margin string
- `buy_margin` - Buy-specific margin (if available)
- `sell_margin` - Sell-specific margin (if available)

### validate_trade_risk()

Validate if a trade meets risk criteria.

```python
validation = await client.risk.validate_trade_risk(
    symbol: str,
    volume: float,
    side: str,
    max_risk_percent: float = 2.0
)
```

**Returns:** dict
- `valid` (bool) - Whether trade passes validation
- `margin_required` (float) - Required margin
- `margin_available` (float) - Available margin
- `margin_sufficient` (bool) - Sufficient margin available
- `risk_percent` (float) - Risk as % of equity
- `risk_acceptable` (bool) - Risk within limits
- `warnings` (list[str]) - Validation warnings

### get_position_pnl()

Get detailed PnL breakdown for a position.

```python
pnl = await client.risk.get_position_pnl(position_id: int)
```

**Returns:** PositionPnL
- `gross_unrealized_pnl` - Gross unrealized PnL
- `net_unrealized_pnl` - Net unrealized PnL
- `swap` - Swap charges
- `commission` - Commission
- `total_costs` - Total costs (swap + commission)
- `formatted_gross_pnl` - Formatted gross PnL
- `formatted_net_pnl` - Formatted net PnL

### get_margin_calls()

Get margin call history.

```python
margin_calls = await client.risk.get_margin_calls()
```

**Returns:** list[MarginCall]

### subscribe_margin_events()

Subscribe to margin change events.

```python
def on_margin_change(position_id, used_margin, money_digits):
    print(f"Position {position_id} margin: {used_margin}")

client.risk.subscribe_margin_events(on_margin_change)
```

---

## History API

### get_deals()

Get deal/trade history.

```python
deals = await client.history.get_deals(
    from_timestamp: Optional[int] = None,
    to_timestamp: Optional[int] = None,
    days: Optional[int] = None,
    max_rows: int = 1000
)
```

**Parameters:**
- `from_timestamp` - Start time in milliseconds
- `to_timestamp` - End time in milliseconds
- `days` - Get deals from last N days (alternative to timestamps)
- `max_rows` - Maximum number of deals

**Returns:** list[Deal]

### get_deals_by_position()

Get all deals for a specific position.

```python
deals = await client.history.get_deals_by_position(position_id: int)
```

**Returns:** list[Deal]

### get_order_details()

Get detailed information about an order.

```python
order = await client.history.get_order_details(order_id: int)
```

**Returns:** Order or None

### get_performance_summary()

Get performance summary with calculated metrics.

```python
summary = await client.history.get_performance_summary(days: int = 30)
```

**Returns:** dict
- `total_deals` (int) - Total number of deals
- `winning_deals` (int) - Number of winning deals
- `losing_deals` (int) - Number of losing deals
- `win_rate` (float) - Win rate percentage
- `total_pnl` (float) - Total PnL
- `total_commission` (float) - Total commission
- `total_swap` (float) - Total swap
- `net_pnl` (float) - Net PnL after costs
- `avg_win` (float) - Average winning trade
- `avg_loss` (float) - Average losing trade
- `largest_win` (float) - Largest win
- `largest_loss` (float) - Largest loss
- `profit_factor` (float) - Profit factor (total wins / total losses)

---

## Account API

### get_account_info()

Get account information.

```python
account = await client.account.get_account_info()
```

**Returns:** AccountInfo
- `balance` - Account balance
- `equity` - Account equity
- `margin` - Used margin
- `free_margin` - Free margin
- `margin_level` - Margin level percentage
- `currency` - Account currency

---

## Models

### Tick

Real-time tick data.

**Attributes:**
- `symbol_name` (str)
- `bid` (float)
- `ask` (float)
- `timestamp` (int) - Milliseconds
- `datetime` (datetime) - Converted timestamp

### Candle

OHLCV candlestick data.

**Attributes:**
- `timestamp` (int)
- `open` (float)
- `high` (float)
- `low` (float)
- `close` (float)
- `volume` (int)
- `symbol_name` (str, optional)
- `timeframe` (str, optional)
- `datetime` (datetime)

### DepthQuote

Single price level in order book.

**Attributes:**
- `id` (int)
- `price` (float)
- `volume` (float)
- `side` (str) - "BUY" or "ASK"

### Position

Open trading position.

**Attributes:**
- `id` (int)
- `symbol_name` (str)
- `side` (str) - "BUY" or "SELL"
- `volume` (float)
- `entry_price` (float)
- `current_price` (float)
- `pnl_gross_unrealized` (float)
- `pnl_net_unrealized` (float)
- `swap` (float)
- `commission` (float)

### Order

Pending order.

**Attributes:**
- `id` (int)
- `symbol_name` (str)
- `side` (str)
- `volume` (float)
- `order_type` (str) - "LIMIT", "STOP", etc.
- `status` (str)
- `limit_price` (float, optional)
- `stop_price` (float, optional)

### Deal

Executed trade.

**Attributes:**
- `deal_id` (int)
- `position_id` (int, optional)
- `order_id` (int, optional)
- `symbol_name` (str)
- `side` (str)
- `volume` (float)
- `execution_price` (float)
- `commission` (float)
- `swap` (float)
- `pnl` (float)
- `timestamp` (int)
- `datetime` (datetime)

---

## Enums

### TimeFrame

Candlestick timeframes.

**Values:**
- `M1` - 1 minute
- `M2` - 2 minutes
- `M3` - 3 minutes
- `M4` - 4 minutes
- `M5` - 5 minutes
- `M10` - 10 minutes
- `M15` - 15 minutes
- `M30` - 30 minutes
- `H1` - 1 hour
- `H4` - 4 hours
- `H12` - 12 hours
- `D1` - 1 day
- `W1` - 1 week
- `MN1` - 1 month

### TradeSide

Trade direction.

**Values:**
- `BUY`
- `SELL`

### OrderType

Order types.

**Values:**
- `MARKET`
- `LIMIT`
- `STOP`
- `STOP_LIMIT`

---

## Error Handling

All API methods may raise exceptions:

```python
from ctc.utils.errors import (
    CTraderError,
    ConnectionError,
    AuthenticationError,
    RequestTimeoutError,
    InvalidRequestError
)

try:
    position = await client.trading.place_market_order("EURUSD", "BUY", 1.0)
except InvalidRequestError as e:
    print(f"Invalid request: {e}")
except RequestTimeoutError as e:
    print(f"Request timed out: {e}")
except CTraderError as e:
    print(f"cTrader error: {e}")
```

---

## Configuration

### ClientConfig

Advanced client configuration.

```python
from ctc.config import ClientConfig

config = ClientConfig(
    request_timeout=30.0,
    inbound_queue_size=1000,
    tick_queue_size=1000,
    depth_queue_size=100,
    candle_queue_size=100,
    drop_inbound_when_full=False
)

client = CTraderClient(..., config=config)
```

---

For more examples, see the `examples/` directory in the repository.
