from __future__ import annotations

import types
import pytest

from ctrader_async.utils import EventBus
from ctrader_async.utils.model_bridge import ModelEventBridge
from ctrader_async.utils.typed_events import OrderUpdateEvent, PositionUpdateEvent


class _FakeSymbols:
    async def get_symbol_name(self, symbol_id: int):
        return "EURUSD"

    async def get_symbol(self, name: str):
        return types.SimpleNamespace(name=name, id=1, protocol_volume_to_lots=lambda v: v / 100.0)


class _FakeTrading:
    def _parse_order(self, order_data, symbol_info):
        return types.SimpleNamespace(kind="order", symbol=symbol_info.name)

    def _parse_position(self, pos_data, symbol_info):
        return types.SimpleNamespace(kind="position", symbol=symbol_info.name)


@pytest.mark.asyncio
async def test_model_bridge_emits_model_events():
    bus = EventBus()
    bridge = ModelEventBridge(bus, _FakeSymbols(), _FakeTrading())
    bridge.enable()

    got = {"order": 0, "position": 0}

    bus.on("model.order", lambda _o: got.__setitem__("order", got["order"] + 1))
    bus.on("model.position", lambda _p: got.__setitem__("position", got["position"] + 1))

    await bus.emit(
        "execution.order",
        OrderUpdateEvent(order_id=1, symbol_id=10, payload=object(), order=types.SimpleNamespace(), envelope=None),
    )
    await bus.emit(
        "execution.position",
        PositionUpdateEvent(position_id=1, symbol_id=10, payload=object(), position=types.SimpleNamespace(), envelope=None),
    )

    assert got["order"] == 1
    assert got["position"] == 1
