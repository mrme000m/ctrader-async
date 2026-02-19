# API Reference

Complete API reference for the cTrader Async Client.

## Table of Contents

- [Client](#client)
- [Session API](#session-api)
- [Market Data API](#market-data-api)
- [Trading API](#trading-api)
- [Risk Management API](#risk-management-api)
- [History API](#history-api)
- [Account API](#account-api)
- [Symbol Catalog](#symbol-catalog)
- [Asset Catalog](#asset-catalog)
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
- `client.session` - Session management API
- `client.symbols` - Symbol catalog
- `client.assets` - Asset catalog
- `client.events` - Event bus for subscriptions
- `client.metrics` - Built-in metrics collector
- `client.hooks` - Hook manager for extensibility

---

## Session API

### get_available_accounts()

Get list of accounts accessible with current access token.

```python
accounts = await client.session.get_available_accounts()
for account in accounts:
    print(f"Account {account.account_id}: {account.account_type}")
    print(f"  Broker: {account.broker_name}")
    print(f"  Is Live: {account.is_live}")
```

**Returns:** `list[AccountSummary]`

### logout()

Logout from the current trading account.

```python
await client.session.logout()
```

### switch_account()

Switch to a different trading account.

```python
# Note: For proper account switching, create a new client instance
success = await client.session.switch_account(account_id: int)
```

**Returns:** bool - True if switch initiated successfully

### refresh_token()

Refresh an expired OAuth access token via the protobuf API.

```python
tokens = await client.session.refresh_token(refresh_token: str)
# Update client config with new token
client.config.access_token = tokens['access_token']
```

**Returns:** `dict` with keys:
- `access_token` - New access token
- `refresh_token` - New refresh token
- `expires_in` - Token expiry in seconds
- `token_type` - Token type (usually "Bearer")

### get_ctid_profile()

Get the cTID user profile for the current access token.

```python
profile = await client.session.get_ctid_profile()
print(f"User: {profile['nickname']} ({profile['email']})")
print(f"ID: {profile['user_id']}")
```

**Returns:** `dict` with keys:
- `user_id` - User identifier
- `nickname` - User nickname
- `email` - User email
- `first_name` - First name
- `last_name` - Last name
- `preferred_lang` - Preferred language

### get_server_version()

Get the cTrader Open API server version.

```python
version = await client.session.get_server_version()
print(f"Server version: {version}")
```

**Returns:** `str` - Server version string (e.g., "168")

---

## Market Data API

### stream_ticks()

Stream real-time tick data for a symbol.

```python
async with client.market_data.stream_ticks(
    symbol: str,
    subscribe_to_timestamp: bool = False
) as stream:
    async for tick in stream:
        # tick.bid, tick.ask, tick.timestamp
        ...
```

**Parameters:**
- `symbol` (str): Symbol name (e.g., "EURUSD")
- `subscribe_to_timestamp` (bool): Include server timestamps in tick events

**Returns:** AsyncIterator[Tick]

### stream_ticks_multi()

Stream real-time ticks for multiple symbols.

```python
async with client.market_data.stream_ticks_multi(
    symbols: list[str],
    coalesce_latest: bool = True,
    subscribe_to_timestamp: bool = False
) as stream:
    async for tick in stream:
        # tick.symbol_name, tick.bid, tick.ask
        ...
```

**Parameters:**
- `symbols` (list[str]): List of symbol names
- `coalesce_latest` (bool): Keep only latest tick per symbol when under load
- `subscribe_to_timestamp` (bool): Include server timestamps

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

### get_tick_data()

Get historical raw tick data for a symbol.

```python
ticks = await client.market_data.get_tick_data(
    symbol: str,
    quote_type: str = "BID",  # or "ASK"
    from_timestamp: Optional[int] = None,
    to_timestamp: Optional[int] = None,
    count: int = 1000
)

for tick in ticks:
    print(f"{tick['timestamp']}: {tick['price']}")
```

**Parameters:**
- `symbol` (str): Symbol name (e.g., "EURUSD")
- `quote_type` (str): "BID" or "ASK" (default: "BID")
- `from_timestamp` (int, optional): Start time in milliseconds
- `to_timestamp` (int, optional): End time in milliseconds
- `count` (int, optional): Maximum number of ticks (default: 1000)

**Returns:** list[dict] with keys:
- `timestamp` - Tick timestamp in milliseconds
- `price` - Tick price
- `type` - Quote type ("BID" or "ASK")

---

## Trading API

### place_market_order()

Place a market order.

```python
from ctc import TradeSide

position = await client.trading.place_market_order(
    symbol: str,
    side: TradeSide,  # TradeSide.BUY or TradeSide.SELL
    volume: float,
    *,
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
from ctc import TradeSide, TimeInForce, OrderTriggerMethod

order = await client.trading.place_limit_order(
    symbol: str,
    side: TradeSide,
    volume: float,
    price: float,  # Note: parameter name is 'price', not 'limit_price'
    *,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
    time_in_force: TimeInForce = TimeInForce.GOOD_TILL_CANCEL,
    expiration_timestamp: Optional[int] = None,
    comment: Optional[str] = None,
    label: Optional[str] = None,
    # Advanced protection
    slippage_in_points: Optional[int] = None,
    relative_stop_loss: Optional[int] = None,
    relative_take_profit: Optional[int] = None,
    guaranteed_stop_loss: Optional[bool] = None,
    trailing_stop_loss: Optional[bool] = None,
    stop_trigger_method: Optional[OrderTriggerMethod] = None,
    position_id: Optional[int] = None
)
```

**Returns:** Order

### place_stop_order()

Place a stop order.

```python
from ctc import TradeSide, TimeInForce, OrderTriggerMethod

order = await client.trading.place_stop_order(
    symbol: str,
    side: TradeSide,
    volume: float,
    stop_price: float,
    *,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
    time_in_force: TimeInForce = TimeInForce.GOOD_TILL_CANCEL,
    expiration_timestamp: Optional[int] = None,
    # Advanced protection options same as limit orders
    slippage_in_points: Optional[int] = None,
    relative_stop_loss: Optional[int] = None,
    relative_take_profit: Optional[int] = None,
    guaranteed_stop_loss: Optional[bool] = None,
    trailing_stop_loss: Optional[bool] = None,
    stop_trigger_method: Optional[OrderTriggerMethod] = None,
    position_id: Optional[int] = None
)
```

**Returns:** Order

### place_stop_limit_order()

Place a stop-limit order.

```python
from ctc import TradeSide, TimeInForce, OrderTriggerMethod

order = await client.trading.place_stop_limit_order(
    symbol: str,
    side: TradeSide,
    volume: float,
    stop_price: float,
    limit_price: float,
    *,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
    time_in_force: TimeInForce = TimeInForce.GOOD_TILL_CANCEL,
    expiration_timestamp: Optional[int] = None,
    comment: Optional[str] = None,
    label: Optional[str] = None,
    # Advanced protection options same as limit orders
    slippage_in_points: Optional[int] = None,
    relative_stop_loss: Optional[int] = None,
    relative_take_profit: Optional[int] = None,
    guaranteed_stop_loss: Optional[bool] = None,
    trailing_stop_loss: Optional[bool] = None,
    stop_trigger_method: Optional[OrderTriggerMethod] = None,
    position_id: Optional[int] = None
)
```

**Returns:** Order

### modify_position()

Modify position stop loss / take profit.

```python
from ctc import OrderTriggerMethod

await client.trading.modify_order(
    order_id: int,
    *,
    volume: Optional[float] = None,
    limit_price: Optional[float] = None,
    stop_price: Optional[float] = None,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
    expiration_timestamp: Optional[int] = None,
    slippage_in_points: Optional[int] = None,
    relative_stop_loss: Optional[int] = None,
    relative_take_profit: Optional[int] = None,
    guaranteed_stop_loss: Optional[bool] = None,
    trailing_stop_loss: Optional[bool] = None,
    stop_trigger_method: Optional[OrderTriggerMethod] = None
)
```

### cancel_order()

Cancel a pending order.

```python
await client.trading.cancel_order(order_id: int)
```

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

### refresh_positions()

Refresh positions from server.

```python
await client.trading.refresh_positions()
```

### refresh_orders()

Refresh orders from server.

```python
await client.trading.refresh_orders()
```

### close_positions_bulk()

Close multiple positions with bounded concurrency.

```python
await client.trading.close_positions_bulk(
    position_ids: list[int],
    *,
    concurrency: int = 5
)
```

### cancel_orders_bulk()

Cancel multiple orders with bounded concurrency.

```python
await client.trading.cancel_orders_bulk(
    order_ids: list[int],
    *,
    concurrency: int = 10
)
```

### modify_orders_bulk()

Modify multiple orders with bounded concurrency.

```python
await client.trading.modify_orders_bulk(
    order_modifications: list[dict],
    *,
    concurrency: int = 10
)
```

### modify_positions_bulk()

Modify multiple positions with bounded concurrency.

```python
await client.trading.modify_positions_bulk(
    position_modifications: list[dict],
    *,
    concurrency: int = 5
)
```

### close_all_positions()

Close all open positions.

```python
await client.trading.close_all_positions()
```

### cancel_all_orders()

Cancel all pending orders.

```python
await client.trading.cancel_all_orders()
```

### get_orders_by_position()

Get all orders associated with a specific position.

```python
orders = await client.trading.get_orders_by_position(position_id: int)
```

**Returns:** list[Order]

### iter_deals_history()

Iterate through deal history with pagination.

```python
async for deal in client.trading.iter_deals_history(
    from_timestamp: Optional[int] = None,
    to_timestamp: Optional[int] = None
):
    # Process deal
    ...
```

### get_deals_history()

Get deal history with optional filtering.

```python
deals = await client.trading.get_deals_history(
    from_timestamp: Optional[int] = None,
    to_timestamp: Optional[int] = None,
    max_count: Optional[int] = None
)
```

**Returns:** list[Deal]

### list_all_orders()

List all orders with optional filtering.

```python
orders = await client.trading.list_all_orders(
    from_timestamp: Optional[int] = None,
    to_timestamp: Optional[int] = None,
    include_closed: bool = False
)
```

**Returns:** list[Order]

from ctc import OrderTriggerMethod

await client.trading.modify_position(
    position_id: int,
    *,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
    guaranteed_stop_loss: Optional[bool] = None,
    trailing_stop_loss: Optional[bool] = None,
    stop_loss_trigger_method: Optional[OrderTriggerMethod] = None
)
```

### close_position()

Close a position (fully or partially).

```python
await client.trading.close_position(
    position_id: int,
    *,
    volume: Optional[float] = None  # None = close all
)
```

### modify_order()

Amend a pending order.

```python
await client.trading.modify_order(
    order_id: int,
    volume: Optional[float] = None,
    limit_price: Optional[float] = None,
    stop_price: Optional[float] = None,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
    expiration_timestamp: Optional[int] = None,
    slippage_in_points: Optional[int] = None,
    relative_stop_loss: Optional[int] = None,
    relative_take_profit: Optional[int] = None,
    guaranteed_stop_loss: Optional[bool] = None,
    trailing_stop_loss: Optional[bool] = None,
    stop_trigger_method: Optional[OrderTriggerMethod] = None
)
```

### cancel_order()

Cancel a pending order.

```python
await client.trading.cancel_order(order_id: int)
```

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

### get_orders_by_position()

Get all orders linked to a specific position.

```python
orders = await client.trading.get_orders_by_position(position_id: int)
```

**Returns:** list[Order]

### list_all_orders()

Get historical orders within a time range.

```python
orders = await client.trading.list_all_orders(
    from_timestamp: Optional[int] = None,
    to_timestamp: Optional[int] = None,
    max_rows: int = 1000
)
```

**Returns:** list[Order]

### iter_deals_history()

Iterate executed deals in a time window (async generator).

```python
async for deal in client.trading.iter_deals_history(
    from_timestamp: int,
    to_timestamp: int,
    max_rows: int = 500
):
    print(f"Deal: {deal.symbol_name} @ {deal.execution_price}")
```

### get_deals_history()

Get executed deals in a time window.

```python
deals = await client.trading.get_deals_history(
    from_timestamp: int,
    to_timestamp: int,
    max_rows: int = 500
)
```

**Returns:** list[Deal]

### Bulk Operations

```python
# Close multiple positions
await client.trading.close_positions_bulk(
    position_ids: list[int],
    concurrency: int = 5
)

# Cancel multiple orders
await client.trading.cancel_orders_bulk(
    order_ids: list[int],
    concurrency: int = 10
)

# Modify multiple orders
await client.trading.modify_orders_bulk(
    modifications: list[tuple],
    concurrency: int = 10
)

# Modify multiple positions
await client.trading.modify_positions_bulk(
    modifications: list[tuple[int, float, float]],  # (position_id, sl, tp)
    concurrency: int = 10
)

# Close all positions
await client.trading.close_all_positions()

# Cancel all orders
await client.trading.cancel_all_orders()
```

---

## Risk Management API

### get_expected_margin()

Calculate expected margin for a proposed trade.

```python
from ctc import TradeSide

margin_info = await client.risk.get_expected_margin(
    symbol: str,
    volume: float,
    order_type: Optional[TradeSide] = None
)

print(f"Required margin: {margin_info.formatted_margin}")
print(f"Buy margin: {margin_info.buy_margin}")
print(f"Sell margin: {margin_info.sell_margin}")
```

**Returns:** MarginInfo
- `margin` - Required margin amount
- `formatted_margin` - Formatted margin string
- `buy_margin` - Buy-specific margin (if available)
- `sell_margin` - Sell-specific margin (if available)

### validate_trade_risk()

Validate if a trade meets risk criteria.

```python
from ctc import TradeSide

validation = await client.risk.validate_trade_risk(
    symbol: str,
    volume: float,
    side: TradeSide,
    max_risk_percent: float = 2.0
)

if validation['valid']:
    # Safe to place order
    position = await client.trading.place_market_order(...)
else:
    print("Trade rejected:", validation['warnings'])
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
print(f"Gross PnL: {pnl.formatted_gross_pnl}")
print(f"Net PnL: {pnl.formatted_net_pnl}")
print(f"Total Costs: {pnl.total_costs}")
```

**Returns:** PositionPnL
- `gross_unrealized_pnl` - Gross unrealized PnL
- `net_unrealized_pnl` - Net unrealized PnL
- `swap` - Swap charges
- `commission` - Commission
- `total_costs` - Total costs (swap + commission)
- `formatted_gross_pnl` - Formatted gross PnL
- `formatted_net_pnl` - Formatted net PnL

### get_position_pnl_realtime()

Get server-calculated real-time PnL for a position.

```python
pnl = await client.risk.get_position_pnl_realtime(position_id: int)
```

**Returns:** PositionPnLRealtime with server-calculated values

### get_margin_calls()

Get margin call history.

```python
margin_calls = await client.risk.get_margin_calls()
for call in margin_calls:
    print(f"{call.margin_call_type} at {call.datetime}")
    print(f"  Equity: {call.formatted_equity}")
    print(f"  Margin Level: {call.formatted_margin_level}")
```

**Returns:** list[MarginCall]

### get_dynamic_leverage()

Get dynamic leverage tiers for a symbol.

```python
leverage_info = await client.risk.get_dynamic_leverage("EURUSD")
for tier in leverage_info.tiers:
    print(f"Volume {tier.volume_from}-{tier.volume_to}: 1:{tier.leverage}")

# Get leverage for specific volume
lev = leverage_info.get_leverage_for_volume(5.0)
```

**Returns:** DynamicLeverage

### update_margin_call()

Update margin call threshold for the account.

```python
await client.risk.update_margin_call(
    margin_call_type: str,  # "MARGIN_CALL" or "STOP_OUT"
    margin_level_threshold: float  # e.g., 120.0 for 120%
)
```

### subscribe_margin_events()

Subscribe to margin change events.

```python
def on_margin_change(position_id: int, used_margin: float, money_digits: int):
    print(f"Position {position_id} margin: {used_margin}")

client.risk.subscribe_margin_events(on_margin_change)
```

### subscribe_margin_call_events()

Subscribe to margin call and stop-out events.

```python
def on_margin_call(event_type: str, equity: float, margin: float, margin_level: float):
    print(f"{event_type}: Margin Level = {margin_level:.2f}%")
    if event_type == "MARGIN_CALL_TRIGGER":
        print("CRITICAL: Positions may be liquidated!")

client.risk.subscribe_margin_call_events(on_margin_call)
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

### get_deal_offsets()

Get deal offsets for netting accounts.

```python
offsets = await client.history.get_deal_offsets(
    from_timestamp: Optional[int] = None,
    to_timestamp: Optional[int] = None,
    days: Optional[int] = None
)

for offset in offsets:
    print(f"Deal {offset.open_deal_id} closed by {offset.close_deal_id}")
```

**Returns:** list[DealOffset]

### get_order_details()

Get detailed information about an order.

```python
order = await client.history.get_order_details(order_id: int)
```

**Returns:** Order or None

### get_orders_by_position()

Get all orders for a specific position.

```python
orders = await client.history.get_orders_by_position(position_id: int)
```

**Returns:** list[Order]

### get_performance_summary()

Get performance summary with calculated metrics.

```python
summary = await client.history.get_performance_summary(days: int = 30)

print(f"Win Rate: {summary['win_rate']:.1f}%")
print(f"Profit Factor: {summary['profit_factor']:.2f}")
print(f"Net PnL: {summary['net_pnl']:.2f}")
print(f"Average Win: {summary['avg_win']:.2f}")
print(f"Average Loss: {summary['avg_loss']:.2f}")
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
- `profit_factor` (float) - Profit factor

---

## Account API

### get_info()

Get account information (basic).

```python
account = await client.account.get_info(refresh: bool = False)
print(f"Balance: {account.balance}")
print(f"Equity: {account.equity}")
```

**Returns:** AccountInfo

### get_full_account_info()

Get complete account information with margin and risk metrics.

```python
info = await client.account.get_full_account_info(refresh: bool = False)
print(f"Balance: {info.formatted_balance}")
print(f"Margin Level: {info.formatted_margin_level}")
print(f"Risk Level: {info.margin_call_risk}")
print(f"Unrealized PnL: {info.unrealized_pnl}")
print(f"Total Swap: {info.swap}")
print(f"Total Commission: {info.commission}")
```

**Returns:** FullAccountInfo
- `account_id` - Account identifier
- `balance` - Account balance
- `equity` - Account equity
- `margin` - Used margin
- `free_margin` - Free margin
- `margin_level` - Margin level percentage
- `currency` - Account currency
- `account_type` - Account type (HEDGED, NETTED, SPREAD_BETTING)
- `leverage` - Account leverage
- `unrealized_pnl` - Total unrealized PnL
- `realized_pnl` - Realized PnL
- `swap` - Total swap charges
- `commission` - Total commission
- `margin_call_risk` - Risk assessment (LOW, MEDIUM, HIGH, CRITICAL)

### get_margin_status()

Get a quick margin status summary.

```python
status = await client.account.get_margin_status()
print(f"Margin Level: {status['margin_level']:.2f}%")
print(f"Free Margin: {status['free_margin']}")
print(f"Can Trade: {status['can_trade']}")
print(f"Risk: {status['margin_call_risk']}")
```

**Returns:** dict
- `margin_level` - Margin level percentage
- `free_margin` - Available margin
- `used_margin` - Used margin
- `equity` - Account equity
- `margin_call_risk` - Risk level string
- `can_trade` - Whether account can trade

### get_cash_flow_history()

Get cash flow history (deposits, withdrawals, dividends).

```python
entries = await client.account.get_cash_flow_history(
    from_timestamp: Optional[int] = None,
    to_timestamp: Optional[int] = None,
    days: Optional[int] = None,
    max_rows: int = 1000
)

for entry in entries:
    print(f"{entry.datetime}: {entry.type.value} {entry.formatted_amount}")
    if entry.is_credit:
        print(f"  Balance after: {entry.balance_after}")
```

**Returns:** list[CashFlowEntry]

### refresh_cache()

Refresh all cached account information.

```python
await client.account.refresh_cache()
```

---

## Symbol Catalog

### get_symbol()

Get symbol by name.

```python
symbol = await client.symbols.get_symbol("EURUSD")
if symbol:
    print(f"Digits: {symbol.digits}")
    print(f"Pip size: {symbol.pip_size}")
    print(f"Lot size: {symbol.lot_size}")
```

**Returns:** Symbol or None

### get_symbol_by_id()

Get symbol by ID.

```python
symbol = await client.symbols.get_symbol_by_id(symbol_id: int)
```

**Returns:** Symbol or None

### get_symbol_details_by_id()

Fetch full symbol details from the server by ID.

```python
symbol = await client.symbols.get_symbol_details_by_id(symbol_id: int)
```

**Returns:** Symbol with fresh data from server

### get_all()

Get all symbols.

```python
symbols = await client.symbols.get_all()
```

**Returns:** list[Symbol]

### search()

Search symbols by pattern.

```python
forex = await client.symbols.search("EUR")
crypto = await client.symbols.search("BTC")
```

**Returns:** list[Symbol]

### get_categories()

Get list of all symbol categories.

```python
categories = await client.symbols.get_categories()
for cat in categories:
    print(f"Category: {cat}")
```

**Returns:** list[str]

### get_symbols_by_category()

Get all symbols in a specific category.

```python
forex_symbols = await client.symbols.get_symbols_by_category("Forex")
crypto_symbols = await client.symbols.get_symbols_by_category("Crypto")
```

**Returns:** list[Symbol]

### get_conversion_symbols()

Get conversion symbols for asset pair.

```python
symbols = await client.symbols.get_conversion_symbols(
    first_asset_id: int,
    last_asset_id: int
)
```

**Returns:** list[Symbol] for currency conversion

---

## Asset Catalog

### get_asset()

Get asset by name.

```python
asset = await client.assets.get_asset("USD")
if asset:
    print(f"Asset ID: {asset.id}")
    print(f"Digits: {asset.digits}")
```

**Returns:** Asset or None

### get_asset_by_id()

Get asset by ID.

```python
asset = await client.assets.get_asset_by_id(asset_id: int)
```

**Returns:** Asset or None

### get_all()

Get all assets.

```python
assets = await client.assets.get_all()
```

**Returns:** list[Asset]

### get_asset_classes()

Get list of all asset classes.

```python
classes = await client.assets.get_asset_classes()
for asset_class in classes:
    print(f"{asset_class.name}: {len(asset_class.asset_ids)} assets")
```

**Returns:** list[AssetClass]

---

## Models

### Tick

Real-time tick data.

**Attributes:**
- `symbol_name` (str)
- `symbol_id` (int)
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

### DepthSnapshot

Order book snapshot.

**Attributes:**
- `bids` (list[DepthQuote])
- `asks` (list[DepthQuote])
- `best_bid` (DepthQuote)
- `best_ask` (DepthQuote)
- `spread` (float)

**Methods:**
- `total_bid_volume(levels: int) -> float`
- `total_ask_volume(levels: int) -> float`

### Position

Open trading position.

**Attributes:**
- `id` (int)
- `symbol_name` (str)
- `symbol_id` (int)
- `side` (str) - "BUY" or "SELL"
- `volume` (float)
- `entry_price` (float)
- `current_price` (float)
- `pnl_gross_unrealized` (float)
- `pnl_net_unrealized` (float)
- `swap` (float)
- `commission` (float)
- `stop_loss` (float, optional)
- `take_profit` (float, optional)

### Order

Pending order.

**Attributes:**
- `id` (int)
- `symbol_name` (str)
- `symbol_id` (int)
- `side` (str)
- `volume` (float)
- `order_type` (str) - "MARKET", "LIMIT", "STOP", "STOP_LIMIT"
- `status` (str)
- `limit_price` (float, optional)
- `stop_price` (float, optional)
- `stop_loss` (float, optional)
- `take_profit` (float, optional)
- `client_order_id` (str, optional)

### Deal

Executed trade.

**Attributes:**
- `deal_id` (int)
- `position_id` (int, optional)
- `order_id` (int, optional)
- `symbol_name` (str)
- `symbol_id` (int)
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

### TimeInForce

Order time in force.

**Values:**
- `GOOD_TILL_CANCEL` (GTC)
- `IMMEDIATE_OR_CANCEL` (IOC)
- `FILL_OR_KILL` (FOK)
- `GOOD_TILL_DATE` (GTD)

### OrderTriggerMethod

Stop order trigger method.

**Values:**
- `TRADE` - Trigger on trade
- `BID` - Trigger on bid
- `ASK` - Trigger on ask
- `MID` - Trigger on mid price

---

## Error Handling

All API methods may raise exceptions:

```python
from ctc.utils.errors import (
    CTraderError,
    ConnectionError,
    AuthenticationError,
    TradingError,
    MarketClosedError,
    RateLimitError,
    RequestTimeoutError,
    InvalidRequestError,
    SymbolNotFoundError,
    OrderError
)

try:
    position = await client.trading.place_market_order("EURUSD", TradeSide.BUY, 1.0)
except AuthenticationError as e:
    print(f"Auth failed: {e}")
except TradingError as e:
    print(f"Trading error: {e.code} - {e.description}")
except MarketClosedError:
    print("Market is closed")
except RateLimitError as e:
    print(f"Rate limited, retry after {e.retry_after}s")
except SymbolNotFoundError as e:
    print(f"Symbol not found: {e}")
```

### Rate Limit Error Handling

When rate limits are exceeded, the server may include a `retryAfter` field in the error response indicating how many seconds to wait before retrying:

```python
except RateLimitError as e:
    # e.retry_after contains the recommended wait time in seconds
    print(f"Rate limited, waiting {e.retry_after}s before retry...")
    await asyncio.sleep(e.retry_after)
```

---

## Configuration

### ClientConfig

Advanced client configuration.

```python
from ctc.config import ClientConfig

config = ClientConfig(
    # Connection
    request_timeout=30.0,
    connection_timeout=30.0,
    auth_timeout=60.0,
    
    # Queue sizes
    inbound_queue_size=1000,
    tick_queue_size=1000,
    depth_queue_size=100,
    candle_queue_size=100,
    
    # Behavior
    drop_inbound_when_full=False,
    reconnect_enabled=True,
    reconnect_max_attempts=10,
    
    # Rate limiting
    rate_limit_trading=50,      # Non-historical requests (subscriptions, trading)
    rate_limit_historical=5,    # Historical data requests (candles, tick data)
    
    # Heartbeat
    heartbeat_interval=30.0,    # Protocol-level heartbeat interval
    
    # WebSocket
    websocket_ping_interval=20.0,
    websocket_ping_timeout=10.0,
)

client = CTraderClient(..., config=config)
```

---

## OAuth Helper

For HTTP-based OAuth authentication:

```python
from ctc.auth import OAuthHelper

oauth = OAuthHelper(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    redirect_uri="https://your-app.com/callback"
)

# Generate authorization URL
auth_url = oauth.get_auth_uri(scope="trading")
print(f"Redirect user to: {auth_url}")

# Exchange authorization code for tokens
tokens = await oauth.exchange_code(auth_code)
access_token = tokens['access_token']
refresh_token = tokens['refresh_token']

# Refresh token later
new_tokens = await oauth.refresh_token_http(refresh_token)
```

---

For more examples, see the `examples/` directory in the repository.
