"""Typed, high-level events for bots/agents.

These events sit above the raw protobuf envelopes and provide a stable interface
for automation systems.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from ..models import Tick


def execution_events_from_payload(payload: Any, *, envelope: Any | None = None) -> list[tuple[str, Any]]:
    """Convert a ProtoOAExecutionEvent payload into one or more typed lifecycle events.

    Returns a list of (event_name, event_obj) pairs.

    Event names:
    - execution (always)
    - execution.error (if errorCode present)
    - execution.order (if order present)
    - execution.position (if position present)
    - execution.deal (if deal present)
    """

    events: list[tuple[str, Any]] = [("execution", ExecutionEvent(payload=payload, envelope=envelope))]

    error_code = getattr(payload, "errorCode", "")
    if error_code:
        events.append(
            (
                "execution.error",
                ExecutionErrorEvent(error_code=str(error_code), payload=payload, envelope=envelope),
            )
        )

    order = getattr(payload, "order", None)
    if order is not None:
        order_id = int(getattr(order, "orderId", 0) or 0)
        symbol_id = None
        td = getattr(order, "tradeData", None)
        if td is not None:
            symbol_id = int(getattr(td, "symbolId", 0) or 0) or None
        events.append(
            (
                "execution.order",
                OrderUpdateEvent(
                    order_id=order_id,
                    symbol_id=symbol_id,
                    payload=payload,
                    order=order,
                    envelope=envelope,
                ),
            )
        )

    position = getattr(payload, "position", None)
    if position is not None:
        position_id = int(getattr(position, "positionId", 0) or 0)
        symbol_id = None
        td = getattr(position, "tradeData", None)
        if td is not None:
            symbol_id = int(getattr(td, "symbolId", 0) or 0) or None
        events.append(
            (
                "execution.position",
                PositionUpdateEvent(
                    position_id=position_id,
                    symbol_id=symbol_id,
                    payload=payload,
                    position=position,
                    envelope=envelope,
                ),
            )
        )

    deal = getattr(payload, "deal", None)
    if deal is not None:
        deal_id = int(getattr(deal, "dealId", 0) or 0)
        events.append(
            (
                "execution.deal",
                DealEvent(
                    deal_id=deal_id,
                    order_id=(int(getattr(deal, "orderId", 0) or 0) or None),
                    position_id=(int(getattr(deal, "positionId", 0) or 0) or None),
                    symbol_id=(int(getattr(deal, "symbolId", 0) or 0) or None),
                    payload=payload,
                    deal=deal,
                    envelope=envelope,
                ),
            )
        )

    return events


@dataclass(frozen=True, slots=True)
class TickEvent:
    """Real-time tick update."""

    tick: Tick
    symbol_id: int
    symbol_name: str
    timestamp: int
    # Raw protobuf payload/envelope for advanced users
    payload: Any | None = None
    envelope: Any | None = None


@dataclass(frozen=True, slots=True)
class ExecutionEvent:
    """Raw execution event wrapper."""

    payload: Any
    envelope: Any | None = None


@dataclass(frozen=True, slots=True)
class ExecutionErrorEvent:
    """Execution event that carries an errorCode."""

    error_code: str
    payload: Any
    envelope: Any | None = None


@dataclass(frozen=True, slots=True)
class OrderUpdateEvent:
    """Order update observed via execution event."""

    order_id: int
    symbol_id: int | None
    payload: Any
    order: Any
    envelope: Any | None = None


@dataclass(frozen=True, slots=True)
class PositionUpdateEvent:
    """Position update observed via execution event."""

    position_id: int
    symbol_id: int | None
    payload: Any
    position: Any
    envelope: Any | None = None


@dataclass(frozen=True, slots=True)
class DealEvent:
    """Deal / fill info observed via execution event."""

    deal_id: int
    order_id: int | None
    position_id: int | None
    symbol_id: int | None
    payload: Any
    deal: Any
    envelope: Any | None = None
