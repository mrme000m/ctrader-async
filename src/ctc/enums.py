"""
Enumerations for cTrader async client.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Type, TypeVar

E = TypeVar("E", bound="ProtoMappableEnum")


class ProtoMappableEnum(Enum):
    """Base enum that can be mapped to/from protobuf enums."""
    
    def to_proto(self, proto_enum_cls: Any) -> int:
        """Convert to protobuf enum value.
        
        Args:
            proto_enum_cls: Protobuf enum class
            
        Returns:
            Integer enum value
            
        Raises:
            ValueError: If enum name not found in protobuf enum
        """
        try:
            return getattr(proto_enum_cls, self.name)
        except AttributeError as exc:
            raise ValueError(
                f"{self.__class__.__name__}.{self.name} not found in {proto_enum_cls}"
            ) from exc
    
    @classmethod
    def from_proto(cls: Type[E], proto_enum_cls: Any, value: int) -> E:
        """Create enum from protobuf enum value.
        
        Args:
            proto_enum_cls: Protobuf enum class
            value: Integer enum value
            
        Returns:
            Enum instance
            
        Raises:
            ValueError: If value not found in enum
        """
        # Try items() method first (newer protobuf)
        if hasattr(proto_enum_cls, "items"):
            for name, val in proto_enum_cls.items():
                if val == value and name in cls.__members__:
                    return cls[name]
        
        # Fallback to dir() inspection
        name_to_val = {
            n: getattr(proto_enum_cls, n) 
            for n in dir(proto_enum_cls) 
            if n.isupper()
        }
        
        for name, val in name_to_val.items():
            if val == value and name in cls.__members__:
                return cls[name]
        
        raise ValueError(
            f"Value {value} not found in {cls.__name__} for proto {proto_enum_cls}"
        )


class TradeSide(ProtoMappableEnum):
    """Trade side enumeration.
    
    Attributes:
        BUY: Long position (buy)
        SELL: Short position (sell)
    """
    
    BUY = "BUY"
    SELL = "SELL"
    
    def __str__(self) -> str:
        return self.value
    
    @property
    def is_buy(self) -> bool:
        """Check if this is a buy side."""
        return self == TradeSide.BUY
    
    @property
    def is_sell(self) -> bool:
        """Check if this is a sell side."""
        return self == TradeSide.SELL
    
    def opposite(self) -> TradeSide:
        """Get opposite trade side."""
        return TradeSide.SELL if self == TradeSide.BUY else TradeSide.BUY


class OrderType(ProtoMappableEnum):
    """Order type enumeration.
    
    Attributes:
        MARKET: Market order (immediate execution at current price)
        LIMIT: Limit order (execution at specified price or better)
        STOP: Stop order (becomes market order when stop price reached)
        MARKET_RANGE: Market order with maximum slippage
        STOP_LIMIT: Stop-limit order (becomes limit order when stop price reached)
        STOP_LOSS_TAKE_PROFIT: SL/TP order for position protection
    """
    
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    MARKET_RANGE = "MARKET_RANGE"
    STOP_LIMIT = "STOP_LIMIT"
    STOP_LOSS_TAKE_PROFIT = "STOP_LOSS_TAKE_PROFIT"
    
    def __str__(self) -> str:
        return self.value


class TimeFrame(ProtoMappableEnum):
    """Chart timeframe enumeration.
    
    Attributes:
        M1: 1 minute
        M2: 2 minutes
        M3: 3 minutes
        M4: 4 minutes
        M5: 5 minutes
        M10: 10 minutes
        M15: 15 minutes
        M30: 30 minutes
        H1: 1 hour
        H4: 4 hours
        H12: 12 hours
        D1: 1 day
        W1: 1 week
        MN1: 1 month
    """
    
    M1 = "M1"
    M2 = "M2"
    M3 = "M3"
    M4 = "M4"
    M5 = "M5"
    M10 = "M10"
    M15 = "M15"
    M30 = "M30"
    H1 = "H1"
    H4 = "H4"
    H12 = "H12"
    D1 = "D1"
    W1 = "W1"
    MN1 = "MN1"
    
    def __str__(self) -> str:
        return self.value
    
    @property
    def minutes(self) -> int:
        """Get timeframe duration in minutes."""
        name = self.name
        
        # Special cases
        if name == "MN1":
            return 60 * 24 * 30  # Approximate month
        if name == "D1":
            return 60 * 24
        if name == "W1":
            return 60 * 24 * 7
        
        # Minute-based
        if name.startswith("M") and name[1:].isdigit():
            return int(name[1:])
        
        # Hour-based
        if name.startswith("H") and name[1:].isdigit():
            return int(name[1:]) * 60
        
        # Fallback
        return 60
    
    @property
    def seconds(self) -> int:
        """Get timeframe duration in seconds."""
        return self.minutes * 60
    
    def to_timedelta_seconds(self, count: int = 1) -> int:
        """Get total seconds for N bars of this timeframe.
        
        Args:
            count: Number of bars
            
        Returns:
            Total seconds
        """
        return self.seconds * max(1, int(count))


class TimeInForce(ProtoMappableEnum):
    """Time in force for orders.
    
    Attributes:
        GOOD_TILL_CANCEL: Order remains active until cancelled
        GOOD_TILL_DATE: Order active until specified date
        IMMEDIATE_OR_CANCEL: Execute immediately or cancel
        FILL_OR_KILL: Execute completely or cancel
        MARKET_ON_OPEN: Execute at market open
    """
    
    GOOD_TILL_CANCEL = "GOOD_TILL_CANCEL"
    GOOD_TILL_DATE = "GOOD_TILL_DATE"
    IMMEDIATE_OR_CANCEL = "IMMEDIATE_OR_CANCEL"
    FILL_OR_KILL = "FILL_OR_KILL"
    MARKET_ON_OPEN = "MARKET_ON_OPEN"
    
    def __str__(self) -> str:
        return self.value


class OrderTriggerMethod(ProtoMappableEnum):
    """Stop loss/take profit trigger method.
    
    Attributes:
        TRADE: Trigger on trade (any price)
        OPPOSITE: Trigger on opposite side (bid for sell, ask for buy)
        DOUBLE_TRADE: Trigger on two consecutive trades
        DOUBLE_OPPOSITE: Trigger on two consecutive opposite quotes
    """
    
    TRADE = "TRADE"
    OPPOSITE = "OPPOSITE"
    DOUBLE_TRADE = "DOUBLE_TRADE"
    DOUBLE_OPPOSITE = "DOUBLE_OPPOSITE"
    
    def __str__(self) -> str:
        return self.value


class OrderStatus(Enum):
    """Order status.
    
    Attributes:
        PENDING: Order is pending
        ACCEPTED: Order accepted by server
        FILLED: Order fully filled
        PARTIALLY_FILLED: Order partially filled
        REJECTED: Order rejected
        CANCELLED: Order cancelled
        EXPIRED: Order expired
    """
    
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    
    def __str__(self) -> str:
        return self.value


class PositionStatus(Enum):
    """Position status.
    
    Attributes:
        OPEN: Position is open
        CLOSED: Position is closed
    """
    
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    
    def __str__(self) -> str:
        return self.value


# Helper functions for backward compatibility with protobuf
def to_proto_trade_side(ts: TradeSide) -> int:
    """Convert TradeSide to protobuf value."""
    from .messages.OpenApiModelMessages_pb2 import ProtoOATradeSide
    return ts.to_proto(ProtoOATradeSide)


def to_proto_order_type(ot: OrderType) -> int:
    """Convert OrderType to protobuf value."""
    from .messages.OpenApiModelMessages_pb2 import ProtoOAOrderType
    return ot.to_proto(ProtoOAOrderType)


def to_proto_timeframe(tf: TimeFrame) -> int:
    """Convert TimeFrame to protobuf value."""
    from .messages.OpenApiModelMessages_pb2 import ProtoOATrendbarPeriod
    return tf.to_proto(ProtoOATrendbarPeriod)


def to_proto_time_in_force(tif: TimeInForce) -> int:
    """Convert TimeInForce to protobuf value."""
    from .messages.OpenApiModelMessages_pb2 import ProtoOATimeInForce
    return tif.to_proto(ProtoOATimeInForce)


def to_proto_trigger_method(tm: OrderTriggerMethod) -> int:
    """Convert OrderTriggerMethod to protobuf value."""
    from .messages.OpenApiModelMessages_pb2 import ProtoOAOrderTriggerMethod
    return tm.to_proto(ProtoOAOrderTriggerMethod)
