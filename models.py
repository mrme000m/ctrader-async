"""
Data models for cTrader async client.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from enum import Enum


@dataclass
class Symbol:
    """Trading symbol information.
    
    Attributes:
        id: Symbol identifier
        name: Symbol name (e.g., "EURUSD")
        digits: Price decimal places
        enabled: Whether trading is enabled
        category_name: Asset category
        base_asset_id: Base currency asset ID
        quote_asset_id: Quote currency asset ID
        description: Symbol description
        pip_position: Pip position (digits for pip calculation)
        pip_size: Calculated pip size
        price_tick_size: Minimum price tick size
        min_volume: Minimum trade volume (protocol units)
        max_volume: Maximum trade volume (protocol units)
        volume_step: Volume step increment (protocol units)
        lot_size: Lot size in base currency units (protocol: cents)
        enable_short_selling: Whether short selling is allowed
        guaranteed_stop_loss: Whether GSL is available
        swap_long: Swap for long positions
        swap_short: Swap for short positions
        leverage: Available leverage
        margin_rate: Margin rate
    """
    
    id: int
    name: str
    digits: int
    enabled: bool = True
    category_name: Optional[str] = None
    base_asset_id: Optional[int] = None
    quote_asset_id: Optional[int] = None
    description: Optional[str] = None
    pip_position: Optional[int] = None
    price_tick_size: Optional[float] = None
    min_volume: Optional[int] = None
    max_volume: Optional[int] = None
    volume_step: Optional[int] = None
    lot_size: Optional[int] = 100000 * 100  # Default: 100k units in cents
    enable_short_selling: Optional[bool] = None
    guaranteed_stop_loss: Optional[bool] = None
    swap_long: Optional[float] = None
    swap_short: Optional[float] = None
    leverage: Optional[float] = None
    margin_rate: Optional[float] = None
    
    @property
    def lot_size_units(self) -> float:
        """Get lot size in base currency units."""
        if self.lot_size is None:
            return 100_000.0
        return float(self.lot_size) / 100.0
    
    @property
    def pip_size(self) -> float:
        """Calculate pip size for this symbol."""
        if isinstance(self.pip_position, int) and self.pip_position >= 0:
            return 10 ** (-int(self.pip_position))
        d = int(self.digits or 5)
        return 10 ** (-(d - 1)) if d >= 3 else 10 ** (-d)
    
    def round_price(self, price: float) -> float:
        """Round price to symbol's digit precision."""
        return round(float(price), int(self.digits or 5))
    
    def lots_to_protocol_volume(self, lots: float) -> int:
        """Convert lots to protocol volume (cents of base currency)."""
        return int(round(float(lots) * self.lot_size_units * 100.0))
    
    def protocol_volume_to_lots(self, proto_volume: int) -> float:
        """Convert protocol volume to lots."""
        if self.lot_size_units <= 0:
            return 0.0
        return (float(proto_volume) / 100.0) / self.lot_size_units
    
    def volume_constraints_lots(self) -> tuple[Optional[float], Optional[float], Optional[float]]:
        """Get volume constraints in lots (min, max, step)."""
        if self.min_volume is None or self.max_volume is None or self.volume_step is None:
            return (None, None, None)
        
        to_lots = lambda v: (float(v) / 100.0) / self.lot_size_units if self.lot_size_units > 0 else None
        return (to_lots(self.min_volume), to_lots(self.max_volume), to_lots(self.volume_step))


@dataclass
class Position:
    """Open trading position.
    
    Attributes:
        id: Position identifier
        symbol_id: Symbol identifier
        symbol_name: Symbol name (optional, populated by client)
        volume: Position volume in lots
        side: Trade side (BUY or SELL)
        entry_price: Entry price
        current_price: Current market price (optional)
        stop_loss: Stop loss price
        take_profit: Take profit price
        trailing_stop: Whether trailing stop is enabled
        guaranteed_stop_loss: Whether GSL is active
        swap: Accumulated swap
        commission: Accumulated commission
        pnl_gross_unrealized: Gross unrealized PnL
        pnl_net_unrealized: Net unrealized PnL (after swap/commission)
        status: Position status
        open_timestamp: Position open time
        last_update_timestamp: Last update time
    """
    
    id: int
    symbol_id: int
    volume: float  # in lots
    side: str  # "BUY" or "SELL"
    entry_price: float
    symbol_name: Optional[str] = None
    current_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: Optional[bool] = None
    guaranteed_stop_loss: Optional[bool] = None
    swap: float = 0.0
    commission: float = 0.0
    pnl_gross_unrealized: float = 0.0
    pnl_net_unrealized: float = 0.0
    status: Optional[str] = None
    open_timestamp: Optional[int] = None
    last_update_timestamp: Optional[int] = None
    
    @property
    def open_datetime(self) -> Optional[datetime]:
        """Get open time as datetime."""
        if self.open_timestamp:
            return datetime.fromtimestamp(self.open_timestamp / 1000.0, tz=timezone.utc)
        return None
    
    @property
    def last_update_datetime(self) -> Optional[datetime]:
        """Get last update time as datetime (UTC, timezone-aware)."""
        if self.last_update_timestamp:
            return datetime.fromtimestamp(self.last_update_timestamp / 1000.0, tz=timezone.utc)
        return None


@dataclass
class Order:
    """Pending order.
    
    Attributes:
        id: Order identifier
        symbol_id: Symbol identifier
        symbol_name: Symbol name (optional)
        volume: Order volume in lots
        side: Trade side (BUY or SELL)
        order_type: Order type (LIMIT, STOP, etc.)
        status: Order status
        time_in_force: Time in force setting
        limit_price: Limit price (for LIMIT/STOP_LIMIT orders)
        stop_price: Stop price (for STOP/STOP_LIMIT orders)
        stop_loss: Stop loss price
        take_profit: Take profit price
        trailing_stop: Whether trailing stop is enabled
        guaranteed_stop_loss: Whether GSL is active
        stop_trigger_method: Stop trigger method
        expiration_timestamp: Order expiration time
        create_timestamp: Order creation time
        last_update_timestamp: Last update time
        client_order_id: Client-assigned order ID
        label: Order label
        comment: Order comment
    """
    
    id: int
    symbol_id: int
    volume: float  # in lots
    side: str  # "BUY" or "SELL"
    symbol_name: Optional[str] = None
    order_type: Optional[str] = None
    status: Optional[str] = None
    time_in_force: Optional[str] = None
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: Optional[bool] = None
    guaranteed_stop_loss: Optional[bool] = None
    stop_trigger_method: Optional[str] = None
    expiration_timestamp: Optional[int] = None
    create_timestamp: Optional[int] = None
    last_update_timestamp: Optional[int] = None
    client_order_id: Optional[str] = None
    label: Optional[str] = None
    comment: Optional[str] = None
    
    @property
    def expiration_datetime(self) -> Optional[datetime]:
        """Get expiration time as datetime."""
        if self.expiration_timestamp:
            return datetime.fromtimestamp(self.expiration_timestamp / 1000.0, tz=timezone.utc)
        return None
    
    @property
    def create_datetime(self) -> Optional[datetime]:
        """Get creation time as datetime."""
        if self.create_timestamp:
            return datetime.fromtimestamp(self.create_timestamp / 1000.0, tz=timezone.utc)
        return None


@dataclass
class AccountInfo:
    """Trading account information.
    
    Attributes:
        account_id: Account identifier
        balance: Account balance
        equity: Account equity
        margin: Used margin
        free_margin: Free margin available
        margin_level: Margin level percentage
        currency: Account currency
        is_live: Whether this is a live account
        account_type: Account type
        leverage: Account leverage
        deposit_asset_id: Deposit currency asset ID
        money_digits: Decimal places for money values
        last_update_timestamp: Last update time
    """
    
    balance: float
    equity: float
    margin: float
    free_margin: float
    account_id: Optional[int] = None
    margin_level: Optional[float] = None
    currency: Optional[str] = None
    is_live: Optional[bool] = None
    account_type: Optional[str] = None
    leverage: Optional[float] = None
    deposit_asset_id: Optional[int] = None
    money_digits: Optional[int] = None
    last_update_timestamp: Optional[int] = None
    
    @property
    def last_update_datetime(self) -> Optional[datetime]:
        """Get last update time as datetime (UTC, timezone-aware)."""
        if self.last_update_timestamp:
            return datetime.fromtimestamp(self.last_update_timestamp / 1000.0, tz=timezone.utc)
        return None


@dataclass
class Tick:
    """Real-time tick data.
    
    Attributes:
        symbol_id: Symbol identifier
        symbol_name: Symbol name
        bid: Bid price
        ask: Ask price
        timestamp: Tick timestamp (milliseconds)
        spread: Spread in pips (optional)
    """
    
    symbol_id: int
    symbol_name: str
    bid: float
    ask: float
    timestamp: int
    spread: Optional[float] = None
    
    @property
    def mid_price(self) -> float:
        """Calculate mid price."""
        return (self.bid + self.ask) / 2.0
    
    @property
    def datetime(self) -> datetime:
        """Get tick time as datetime."""
        return datetime.fromtimestamp(self.timestamp / 1000.0, tz=timezone.utc)


@dataclass
class Candle:
    """OHLC candlestick data.
    
    Attributes:
        timestamp: Candle timestamp
        open: Open price
        high: High price
        low: Low price
        close: Close price
        volume: Tick volume
        symbol_name: Symbol name (optional)
        timeframe: Timeframe (optional)
    """
    
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int = 0
    symbol_name: Optional[str] = None
    timeframe: Optional[str] = None
    
    @property
    def range(self) -> float:
        """Calculate candle range (high - low)."""
        return self.high - self.low
    
    @property
    def body(self) -> float:
        """Calculate candle body size (abs(close - open))."""
        return abs(self.close - self.open)
    
    @property
    def is_bullish(self) -> bool:
        """Check if candle is bullish."""
        return self.close > self.open
    
    @property
    def is_bearish(self) -> bool:
        """Check if candle is bearish."""
        return self.close < self.open


@dataclass
class Deal:
    """Executed trade deal (fill).

    This model is meant to be convenient for bots/agents.

    Notes:
    - When emitted from live execution events, not all fields are always available.
      For that reason, most fields are optional with sensible defaults.
    """

    deal_id: int
    position_id: Optional[int] = None
    order_id: Optional[int] = None
    symbol_id: Optional[int] = None
    symbol_name: Optional[str] = None
    side: Optional[str] = None
    volume: Optional[float] = None  # in lots
    execution_price: Optional[float] = None
    commission: float = 0.0
    swap: float = 0.0
    pnl: float = 0.0
    timestamp: Optional[int] = None
    
    @property
    def datetime(self) -> Optional[datetime]:
        """Get execution time as datetime."""
        if self.timestamp:
            return datetime.fromtimestamp(self.timestamp / 1000.0, tz=timezone.utc)
        return None


@dataclass
class Asset:
    """Asset (currency) information.
    
    Attributes:
        id: Asset identifier
        name: Asset name (e.g., "USD", "EUR")
        display_name: Display name
        digits: Decimal places
    """
    
    id: int
    name: str
    display_name: Optional[str] = None
    digits: Optional[int] = None
