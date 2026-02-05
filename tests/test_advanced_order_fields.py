from __future__ import annotations

import types
import pytest

from ctrader_async.api.trading import TradingAPI
from ctrader_async.enums import TradeSide, TimeInForce, OrderTriggerMethod


class _FakeProtocol:
    def __init__(self):
        self.calls = []

    async def send_request(self, req, **kwargs):
        self.calls.append((req, kwargs))
        return types.SimpleNamespace()


class _FakeSymbols:
    async def get_symbol(self, name: str):
        # minimal symbol info needed by TradingAPI
        return types.SimpleNamespace(
            id=1,
            name=name,
            digits=5,
            round_price=lambda p: float(p),
            lots_to_protocol_volume=lambda lots: 123,
            protocol_volume_to_lots=lambda v: 0.01,
        )

    async def get_symbol_name(self, symbol_id: int):
        return "EURUSD"


@pytest.mark.asyncio
async def test_new_order_req_wires_advanced_fields(monkeypatch):
    proto = _FakeProtocol()
    cfg = types.SimpleNamespace(account_id=1, request_timeout=1, rate_limit_trading=100)
    api = TradingAPI(proto, cfg, _FakeSymbols())

    # Avoid sleeps + refresh calls in order placement paths
    async def _noop(*_a, **_k):
        return

    monkeypatch.setattr(api, "refresh_orders", _noop)
    async def _none(*_a, **_k):
        return None

    monkeypatch.setattr(api, "_find_order_by_client_id", _none)

    await api.place_limit_order(
        "EURUSD",
        TradeSide.BUY,
        0.01,
        1.2345,
        time_in_force=TimeInForce.GOOD_TILL_CANCEL,
        slippage_in_points=7,
        relative_stop_loss=11,
        relative_take_profit=22,
        guaranteed_stop_loss=True,
        trailing_stop_loss=True,
        stop_trigger_method=OrderTriggerMethod.TRADE,
        position_id=999,
    )

    assert proto.calls, "Expected send_request call"
    req, kwargs = proto.calls[0]

    # request fields exist and set
    assert getattr(req, "slippageInPoints", None) == 7
    assert getattr(req, "relativeStopLoss", None) == 11
    assert getattr(req, "relativeTakeProfit", None) == 22
    assert getattr(req, "guaranteedStopLoss", None) is True
    assert getattr(req, "trailingStopLoss", None) is True
    assert getattr(req, "positionId", None) == 999
    assert int(getattr(req, "stopTriggerMethod", 0)) != 0


@pytest.mark.asyncio
async def test_amend_position_req_wires_advanced_fields(monkeypatch):
    proto = _FakeProtocol()
    cfg = types.SimpleNamespace(account_id=1, request_timeout=1, rate_limit_trading=100)
    api = TradingAPI(proto, cfg, _FakeSymbols())

    await api.modify_position(
        42,
        stop_loss=1.0,
        take_profit=2.0,
        guaranteed_stop_loss=True,
        trailing_stop_loss=True,
        stop_loss_trigger_method=OrderTriggerMethod.OPPOSITE,
    )

    req, kwargs = proto.calls[0]
    assert getattr(req, "positionId", None) == 42
    assert getattr(req, "guaranteedStopLoss", None) is True
    assert getattr(req, "trailingStopLoss", None) is True
    assert int(getattr(req, "stopLossTriggerMethod", 0)) != 0
