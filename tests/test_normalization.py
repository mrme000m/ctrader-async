from __future__ import annotations

import types
import pytest

from ctc.utils.typed_events import OrderUpdateEvent, PositionUpdateEvent
from ctc.utils.normalization import normalize_order_update, normalize_position_update


class _FakeSymbols:
    async def get_symbol_name(self, symbol_id: int):
        return "EURUSD"

    async def get_symbol(self, name: str):
        return types.SimpleNamespace(
            name=name,
            id=1,
            protocol_volume_to_lots=lambda v: v / 100.0,
        )


class _FakeTrading:
    def _parse_order(self, order_data, symbol_info):
        return types.SimpleNamespace(parsed="order", symbol=symbol_info.name)

    def _parse_position(self, pos_data, symbol_info):
        return types.SimpleNamespace(parsed="position", symbol=symbol_info.name)


@pytest.mark.asyncio
async def test_normalize_order_update_uses_trading_parse():
    evt = OrderUpdateEvent(order_id=1, symbol_id=10, payload=object(), order=types.SimpleNamespace(), envelope=None)
    out = await normalize_order_update(evt, symbols=_FakeSymbols(), trading=_FakeTrading())
    assert out.parsed == "order"


@pytest.mark.asyncio
async def test_normalize_position_update_uses_trading_parse():
    evt = PositionUpdateEvent(position_id=1, symbol_id=10, payload=object(), position=types.SimpleNamespace(), envelope=None)
    out = await normalize_position_update(evt, symbols=_FakeSymbols(), trading=_FakeTrading())
    assert out.parsed == "position"
