from __future__ import annotations

import types
import pytest

from ctrader_async.utils.typed_events import execution_events_from_payload
from ctrader_async.api.trading import TradingAPI


def test_execution_events_from_payload_splits_events():
    payload = types.SimpleNamespace(
        errorCode="ERR",
        order=types.SimpleNamespace(orderId=1, tradeData=types.SimpleNamespace(symbolId=10)),
        position=types.SimpleNamespace(positionId=2, tradeData=types.SimpleNamespace(symbolId=10)),
        deal=types.SimpleNamespace(dealId=3, orderId=1, positionId=2, symbolId=10),
    )
    events = execution_events_from_payload(payload, envelope=object())
    names = [n for n, _ in events]
    assert "execution" in names
    assert "execution.error" in names
    assert "execution.order" in names
    assert "execution.position" in names
    assert "execution.deal" in names


class _FakeProtocol:
    def __init__(self):
        self.calls = []

    async def send_request(self, req, **kwargs):
        self.calls.append((type(req).__name__, kwargs.get("request_type")))
        return types.SimpleNamespace()


class _FakeSymbols:
    async def get_symbol(self, name: str):
        return types.SimpleNamespace(name=name, id=1, lots_to_protocol_volume=lambda x: 100)


@pytest.mark.asyncio
async def test_bulk_ops_call_underlying_methods(monkeypatch):
    # Instantiate TradingAPI with fakes
    proto = _FakeProtocol()
    cfg = types.SimpleNamespace(account_id=1, request_timeout=1, rate_limit_trading=100)
    api = TradingAPI(proto, cfg, _FakeSymbols())

    closed = []
    cancelled = []

    async def close_position(pid, volume=None):
        closed.append(pid)

    async def cancel_order(oid):
        cancelled.append(oid)

    monkeypatch.setattr(api, "close_position", close_position)
    monkeypatch.setattr(api, "cancel_order", cancel_order)

    await api.close_positions_bulk([1, 2, 3], concurrency=2)
    await api.cancel_orders_bulk([10, 11], concurrency=1)

    modified = []

    async def modify_position(pid, *, stop_loss=None, take_profit=None):
        modified.append((pid, stop_loss, take_profit))

    monkeypatch.setattr(api, "modify_position", modify_position)
    await api.modify_positions_bulk([(1, 1.0, None), (2, None, 2.0)], concurrency=2)

    assert set(closed) == {1, 2, 3}
    assert set(cancelled) == {10, 11}
    assert set(modified) == {(1, 1.0, None), (2, None, 2.0)}
