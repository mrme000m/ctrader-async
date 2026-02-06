from __future__ import annotations

import types
import pytest

from ctc.api.trading import TradingAPI
from ctc.enums import OrderTriggerMethod


class _FakeProtocol:
    def __init__(self):
        self.last_req = None

    async def send_request(self, req, **kwargs):
        self.last_req = req
        return types.SimpleNamespace()


class _FakeSymbols:
    async def get_symbol(self, name: str):
        return types.SimpleNamespace(name=name, id=1, lots_to_protocol_volume=lambda x: 100)


@pytest.mark.asyncio
async def test_modify_order_sets_advanced_fields():
    proto = _FakeProtocol()
    cfg = types.SimpleNamespace(account_id=1, request_timeout=1, rate_limit_trading=100)
    api = TradingAPI(proto, cfg, _FakeSymbols())

    # Seed cache with an order symbol for volume conversion
    async with api._orders_lock:
        api._orders = [types.SimpleNamespace(id=10, symbol_name="EURUSD")]

    await api.modify_order(
        10,
        volume=0.01,
        limit_price=1.2,
        slippage_in_points=5,
        relative_stop_loss=10,
        relative_take_profit=20,
        guaranteed_stop_loss=True,
        trailing_stop_loss=False,
        stop_trigger_method=OrderTriggerMethod.TRADE,
    )

    req = proto.last_req
    assert req.orderId == 10
    assert req.slippageInPoints == 5
    assert req.relativeStopLoss == 10
    assert req.relativeTakeProfit == 20
    assert req.guaranteedStopLoss is True
    assert req.trailingStopLoss is False
