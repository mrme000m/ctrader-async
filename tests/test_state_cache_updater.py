from __future__ import annotations

import types
import pytest

from ctc.utils import EventBus
from ctc.utils.state_cache import TradingStateCacheUpdater


@pytest.mark.asyncio
async def test_state_cache_updater_updates_caches():
    bus = EventBus()
    trading = types.SimpleNamespace(
        _orders=[],
        _positions=[],
        _orders_lock=types.SimpleNamespace(__aenter__=None),
    )

    # Use real asyncio locks
    import asyncio

    trading._orders_lock = asyncio.Lock()
    trading._positions_lock = asyncio.Lock()

    updater = TradingStateCacheUpdater(bus, trading)
    updater.enable()

    await bus.emit("model.order", types.SimpleNamespace(id=1, volume=1.0))
    await bus.emit("model.position", types.SimpleNamespace(id=2, volume=1.0))

    assert [o.id for o in trading._orders] == [1]
    assert [p.id for p in trading._positions] == [2]

    # Replace by id
    await bus.emit("model.order", types.SimpleNamespace(id=1, x=2, volume=1.0))
    assert len(trading._orders) == 1
    assert getattr(trading._orders[0], "x", None) == 2

    # Deal cleanup decrements order volume
    await bus.emit("model.deal", types.SimpleNamespace(order_id=1, volume=0.25))
    assert len(trading._orders) == 1
    assert abs(trading._orders[0].volume - 0.75) < 1e-9

    # Another deal removes remaining volume
    await bus.emit("model.deal", types.SimpleNamespace(order_id=1, volume=0.75))
    assert trading._orders == []

    # Deal decrement closes position when volume matches
    await bus.emit("model.deal", types.SimpleNamespace(position_id=2, volume=1.0))
    assert trading._positions == []

    # Re-add and then zero volume removes position
    await bus.emit("model.position", types.SimpleNamespace(id=2, volume=1.0))
    await bus.emit("model.position", types.SimpleNamespace(id=2, volume=0.0))
    assert trading._positions == []
