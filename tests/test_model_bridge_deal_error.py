from __future__ import annotations

import types
import pytest

from ctc.utils import EventBus
from ctc.utils.model_bridge import ModelEventBridge, NormalizedExecutionError
from ctc.models import Deal
from ctc.utils.typed_events import DealEvent, ExecutionErrorEvent


class _FakeSymbols:
    pass


class _FakeTrading:
    pass


@pytest.mark.asyncio
async def test_model_bridge_emits_model_deal_and_error():
    bus = EventBus()
    bridge = ModelEventBridge(bus, _FakeSymbols(), _FakeTrading())
    bridge.enable()

    got = {"deal": None, "raw": None, "err": None}

    def on_deal(d: Deal):
        got["deal"] = d

    def on_raw(_d):
        got["raw"] = _d

    def on_err(e: NormalizedExecutionError):
        got["err"] = e

    bus.on("model.deal", on_deal)
    bus.on("model.deal.raw", on_raw)
    bus.on("model.execution_error", on_err)

    await bus.emit(
        "execution.deal",
        DealEvent(
            deal_id=1,
            order_id=2,
            position_id=3,
            symbol_id=4,
            payload=object(),
            deal=types.SimpleNamespace(dealId=1),
            envelope=None,
        ),
    )

    await bus.emit(
        "execution.error",
        ExecutionErrorEvent(error_code="ERR", payload=types.SimpleNamespace(), envelope=None),
    )

    assert isinstance(got["deal"], Deal)
    assert got["deal"].deal_id == 1
    assert got["raw"] is not None
    assert isinstance(got["err"], NormalizedExecutionError)
    assert got["err"].error_code == "ERR"
