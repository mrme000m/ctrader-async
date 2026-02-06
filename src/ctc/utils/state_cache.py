"""State cache updater.

Optional bridge that keeps TradingAPI caches up to date using model events.

Listens:
- model.order (models.Order)
- model.position (models.Position)

Updates:
- TradingAPI._orders
- TradingAPI._positions

This is useful for bots/agents that want low-latency state without frequent reconcile.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .events import EventBus

logger = logging.getLogger(__name__)


@dataclass
class TradingStateCacheUpdater:
    events: EventBus
    trading: any

    _enabled: bool = False

    def enable(self) -> None:
        if self._enabled:
            return
        self._enabled = True
        self.events.on("model.order", self._on_order)
        self.events.on("model.position", self._on_position)
        self.events.on("model.deal", self._on_deal)

    def disable(self) -> None:
        if not self._enabled:
            return
        self._enabled = False
        self.events.off("model.order", self._on_order)
        self.events.off("model.position", self._on_position)
        self.events.off("model.deal", self._on_deal)

    async def _on_order(self, order) -> None:
        try:
            # Heuristic: if an order volume is 0, treat as removed.
            vol = getattr(order, "volume", None)
            remove = (vol is not None and vol <= 0)

            async with self.trading._orders_lock:
                self.trading._orders = [
                    o for o in self.trading._orders if getattr(o, "id", None) != order.id
                ]
                if not remove:
                    self.trading._orders.append(order)
        except Exception as exc:
            logger.debug(f"State cache updater order failed: {exc}")

    async def _on_position(self, pos) -> None:
        try:
            # Heuristic: remove positions with zero volume
            vol = getattr(pos, "volume", None)
            remove = (vol is not None and vol <= 0)

            async with self.trading._positions_lock:
                self.trading._positions = [
                    p for p in self.trading._positions if getattr(p, "id", None) != pos.id
                ]
                if not remove:
                    self.trading._positions.append(pos)
        except Exception as exc:
            logger.debug(f"State cache updater position failed: {exc}")

    async def _on_deal(self, deal) -> None:
        """Deal-driven cleanup.

        Heuristics:
        - If a deal references an order id, that order is no longer pending -> remove from cache.
        - If a deal references a position id and includes deal volume, decrement cached position volume;
          remove position when volume reaches ~0.
        """
        try:
            order_id = getattr(deal, "order_id", None)
            deal_volume = getattr(deal, "volume", None)
            if order_id:
                async with self.trading._orders_lock:
                    updated_orders = []
                    for o in self.trading._orders:
                        if getattr(o, "id", None) != int(order_id):
                            updated_orders.append(o)
                            continue

                        ovol = getattr(o, "volume", None)
                        # If we have volumes, decrement for partial fills
                        if isinstance(ovol, (int, float)) and isinstance(deal_volume, (int, float)):
                            new_vol = float(ovol) - float(deal_volume)
                            if new_vol <= 1e-12:
                                continue
                            try:
                                setattr(o, "volume", new_vol)
                            except Exception:
                                pass
                            updated_orders.append(o)
                        else:
                            # If we can't determine, assume order is no longer pending
                            continue

                    self.trading._orders = updated_orders

            position_id = getattr(deal, "position_id", None)
            if position_id and isinstance(deal_volume, (int, float)):
                async with self.trading._positions_lock:
                    updated = []
                    for p in self.trading._positions:
                        if getattr(p, "id", None) != int(position_id):
                            updated.append(p)
                            continue

                        pvol = getattr(p, "volume", None)
                        if isinstance(pvol, (int, float)):
                            new_vol = float(pvol) - float(deal_volume)
                            # treat tiny values as closed
                            if new_vol <= 1e-12:
                                continue
                            try:
                                setattr(p, "volume", new_vol)
                            except Exception:
                                pass
                            updated.append(p)
                        else:
                            updated.append(p)
                    self.trading._positions = updated
        except Exception as exc:
            logger.debug(f"State cache updater deal cleanup failed: {exc}")
