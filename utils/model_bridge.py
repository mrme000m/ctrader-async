"""Model event bridge.

Listens to typed execution lifecycle events and re-emits normalized `models.*` events
for consumers that want stable domain models instead of protobuf payloads.

Emitted events:
- model.order (models.Order)
- model.position (models.Position)

This is optional and must be enabled explicitly.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from .events import EventBus
from .typed_events import OrderUpdateEvent, PositionUpdateEvent, DealEvent, ExecutionErrorEvent
from .normalization import normalize_order_update, normalize_position_update


from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NormalizedDeal:
    deal_id: int
    order_id: int | None
    position_id: int | None
    symbol_id: int | None
    # Keep original deal payload for advanced consumers
    deal: any


@dataclass(frozen=True, slots=True)
class NormalizedExecutionError:
    error_code: str
    payload: any

logger = logging.getLogger(__name__)


@dataclass
class ModelEventBridge:
    events: EventBus
    symbols: any
    trading: any

    _enabled: bool = False

    def enable(self) -> None:
        if self._enabled:
            return
        self._enabled = True
        self.events.on("execution.order", self._on_order)
        self.events.on("execution.position", self._on_position)
        self.events.on("execution.deal", self._on_deal)
        self.events.on("execution.error", self._on_error)

    def disable(self) -> None:
        if not self._enabled:
            return
        self._enabled = False
        self.events.off("execution.order", self._on_order)
        self.events.off("execution.position", self._on_position)
        self.events.off("execution.deal", self._on_deal)
        self.events.off("execution.error", self._on_error)

    async def _on_order(self, evt: OrderUpdateEvent) -> None:
        try:
            order = await normalize_order_update(evt, symbols=self.symbols, trading=self.trading)
            await self.events.emit("model.order", order)
        except Exception as exc:
            logger.debug(f"Model bridge order normalize failed: {exc}")

    async def _on_position(self, evt: PositionUpdateEvent) -> None:
        try:
            pos = await normalize_position_update(evt, symbols=self.symbols, trading=self.trading)
            await self.events.emit("model.position", pos)
        except Exception as exc:
            logger.debug(f"Model bridge position normalize failed: {exc}")

    async def _on_deal(self, evt: DealEvent) -> None:
        try:
            from ..models import Deal

            # Rich model event
            raw_volume = getattr(evt.deal, "volume", None)
            raw_exec_price = getattr(evt.deal, "executionPrice", None)
            raw_price = getattr(evt.deal, "price", None)
            raw_ts = getattr(evt.deal, "utcTimestamp", None)
            if raw_ts is None:
                raw_ts = getattr(evt.deal, "timestamp", None)

            # best-effort additional fields
            raw_side = getattr(evt.deal, "side", None)
            if raw_side is None:
                raw_side = getattr(evt.deal, "tradeSide", None)

            raw_symbol_name = getattr(evt.deal, "symbolName", None)

            d = Deal(
                deal_id=int(evt.deal_id),
                order_id=evt.order_id,
                position_id=evt.position_id,
                symbol_id=evt.symbol_id,
                symbol_name=(str(raw_symbol_name) if raw_symbol_name else None),
                side=(str(raw_side) if raw_side else None),
                volume=(raw_volume / 100.0 if isinstance(raw_volume, (int, float)) else None),
                execution_price=(
                    float(raw_exec_price)
                    if isinstance(raw_exec_price, (int, float))
                    else (float(raw_price) if isinstance(raw_price, (int, float)) else None)
                ),
                timestamp=(int(raw_ts) if isinstance(raw_ts, (int, float)) else None),
            )
            await self.events.emit("model.deal", d)

            # Backward-compatible lightweight deal
            nd = NormalizedDeal(
                deal_id=int(evt.deal_id),
                order_id=evt.order_id,
                position_id=evt.position_id,
                symbol_id=evt.symbol_id,
                deal=evt.deal,
            )
            await self.events.emit("model.deal.raw", nd)
        except Exception as exc:
            logger.debug(f"Model bridge deal normalize failed: {exc}")

    async def _on_error(self, evt: ExecutionErrorEvent) -> None:
        try:
            ne = NormalizedExecutionError(error_code=str(evt.error_code), payload=evt.payload)
            await self.events.emit("model.execution_error", ne)
        except Exception as exc:
            logger.debug(f"Model bridge error normalize failed: {exc}")
