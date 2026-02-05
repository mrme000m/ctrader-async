from __future__ import annotations

import types
import pytest

from ctrader_async.api.trading import TradingAPI


class _FakeProtocol:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    async def send_request(self, req, **kwargs):
        self.calls.append((type(req).__name__, kwargs.get("request_type"), req))
        if not self._responses:
            raise AssertionError("No more fake responses")
        return self._responses.pop(0)


class _FakeSymbols:
    def __init__(self):
        self._by_id = {1: types.SimpleNamespace(id=1, name="EURUSD", digits=5, lot_size=100000 * 100)}

    async def get_symbol_name(self, symbol_id: int):
        info = self._by_id.get(int(symbol_id))
        return info.name if info else None

    async def get_symbol(self, name: str):
        # Provide conversions consistent with ctrader_async.models.Symbol
        return types.SimpleNamespace(
            id=1,
            name=name,
            digits=5,
            lot_size=100000 * 100,
            lot_size_units=100000.0,
            protocol_volume_to_lots=lambda v: (float(v) / 100.0) / 100000.0,
        )


def _deal_pb(
    *,
    dealId=1,
    symbolId=1,
    volume=100000 * 100,  # 1 lot in proto units (cents of base)
    executionPrice=1.2345,
    orderId=10,
    positionId=20,
    executionTimestamp=1700000000000,
):
    return types.SimpleNamespace(
        dealId=dealId,
        symbolId=symbolId,
        volume=volume,
        orderId=orderId,
        positionId=positionId,
        executionPrice=executionPrice,
        executionTimestamp=executionTimestamp,
        tradeSide="BUY",
        commission=0,
        swap=0,
        moneyDigits=2,
    )


@pytest.mark.asyncio
async def test_get_deals_history_paginates_and_parses():
    # fake two pages
    res1 = types.SimpleNamespace(deal=[_deal_pb(dealId=1), _deal_pb(dealId=2)], hasMore=True)
    res2 = types.SimpleNamespace(deal=[_deal_pb(dealId=3)], hasMore=False)

    proto = _FakeProtocol([res1, res2])
    cfg = types.SimpleNamespace(account_id=1, request_timeout=1, rate_limit_trading=100)
    api = TradingAPI(proto, cfg, _FakeSymbols())

    deals = await api.get_deals_history(from_timestamp=1, to_timestamp=2, max_rows=2)

    assert [d.deal_id for d in deals] == [1, 2, 3]
    # 1 lot parsed
    assert deals[0].volume == pytest.approx(1.0)
    assert deals[0].execution_price == pytest.approx(1.2345)
    assert deals[0].symbol_name == "EURUSD"

    # called twice
    assert len(proto.calls) == 2


@pytest.mark.asyncio
async def test_iter_deals_history_streams_results():
    res = types.SimpleNamespace(deal=[_deal_pb(dealId=1), _deal_pb(dealId=2)], hasMore=False)
    proto = _FakeProtocol([res])
    cfg = types.SimpleNamespace(account_id=1, request_timeout=1, rate_limit_trading=100)
    api = TradingAPI(proto, cfg, _FakeSymbols())

    got = []
    async for d in api.iter_deals_history(from_timestamp=1, to_timestamp=2, max_rows=50):
        got.append(d.deal_id)

    assert got == [1, 2]
