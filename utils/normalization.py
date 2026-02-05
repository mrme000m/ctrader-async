"""Event-to-model normalization.

Converts execution lifecycle payloads into existing `models` dataclasses.
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from .typed_events import OrderUpdateEvent, PositionUpdateEvent
from ..models import Order, Position

if TYPE_CHECKING:
    from ..api.symbols import SymbolCatalog
    from ..api.trading import TradingAPI


async def normalize_order_update(
    evt: OrderUpdateEvent,
    *,
    symbols: "SymbolCatalog",
    trading: Optional["TradingAPI"] = None,
) -> Order:
    """Convert an OrderUpdateEvent into a models.Order.

    Uses TradingAPI._parse_order for consistency.
    """

    symbol_info = None
    try:
        if evt.symbol_id:
            name = await symbols.get_symbol_name(int(evt.symbol_id))
            if name:
                symbol_info = await symbols.get_symbol(name)
    except Exception:
        symbol_info = None

    if trading is None:
        # Minimal fallback mapping
        o = evt.order
        return Order(
            id=int(getattr(o, "orderId", 0) or 0),
            symbol_id=int(getattr(getattr(o, "tradeData", None), "symbolId", 0) or 0),
            symbol_name=(symbol_info.name if symbol_info else None),
            volume=float(getattr(getattr(o, "tradeData", None), "volume", 0) or 0) / 100.0,
            side=str(getattr(getattr(o, "tradeData", None), "tradeSide", "")),
            limit_price=getattr(o, "limitPrice", None),
            stop_price=getattr(o, "stopPrice", None),
            stop_loss=getattr(o, "stopLoss", None),
            take_profit=getattr(o, "takeProfit", None),
            client_order_id=getattr(o, "clientOrderId", None),
        )

    return trading._parse_order(evt.order, symbol_info)


async def normalize_position_update(
    evt: PositionUpdateEvent,
    *,
    symbols: "SymbolCatalog",
    trading: Optional["TradingAPI"] = None,
) -> Position:
    """Convert a PositionUpdateEvent into a models.Position.

    Uses TradingAPI._parse_position for consistency.
    """

    symbol_info = None
    try:
        if evt.symbol_id:
            name = await symbols.get_symbol_name(int(evt.symbol_id))
            if name:
                symbol_info = await symbols.get_symbol(name)
    except Exception:
        symbol_info = None

    if trading is None:
        p = evt.position
        return Position(
            id=int(getattr(p, "positionId", 0) or 0),
            symbol_id=int(getattr(getattr(p, "tradeData", None), "symbolId", 0) or 0),
            symbol_name=(symbol_info.name if symbol_info else None),
            volume=float(getattr(getattr(p, "tradeData", None), "volume", 0) or 0) / 100.0,
            side=str(getattr(getattr(p, "tradeData", None), "tradeSide", "")),
            entry_price=float(getattr(p, "price", 0.0) or 0.0),
            stop_loss=(float(getattr(p, "stopLoss", 0.0)) if getattr(p, "stopLoss", 0) else None),
            take_profit=(float(getattr(p, "takeProfit", 0.0)) if getattr(p, "takeProfit", 0) else None),
            last_update_timestamp=(int(getattr(p, "utcLastUpdateTimestamp", 0)) or None),
        )

    return trading._parse_position(evt.position, symbol_info)
