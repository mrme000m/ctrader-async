from __future__ import annotations

import asyncio
import types
import pytest

from ctrader_async.streams.tick_stream import TickStream
from ctrader_async.streams.multi_tick_stream import MultiTickStream


class _Dummy:
    def __init__(self):
        self.dispatcher = types.SimpleNamespace(register=lambda *a, **k: None, unregister=lambda *a, **k: None)
        self.events = types.SimpleNamespace(emit=lambda *a, **k: None)

    async def send_request(self, *a, **k):
        return types.SimpleNamespace()


class _Symbols:
    async def get_symbol(self, name):
        return types.SimpleNamespace(id=1, name=name)


@pytest.mark.asyncio
async def test_tickstream_does_not_stop_iteration_when_temporarily_unsubscribed(monkeypatch):
    s = TickStream(_Dummy(), types.SimpleNamespace(account_id=1, tick_queue_size=10), _Symbols(), "EURUSD")

    # avoid real subscribe
    monkeypatch.setattr(s, "_subscribe", lambda: asyncio.sleep(0))
    monkeypatch.setattr(s, "_unsubscribe", lambda: asyncio.sleep(0))

    await s.__aenter__()
    assert s._active is True

    # simulate temporary unsubscribe during resubscribe
    s._subscribed = False

    # put an item; __anext__ should still return it (not StopAsyncIteration)
    await s._queue.put(types.SimpleNamespace())
    item = await asyncio.wait_for(s.__anext__(), timeout=1)
    assert item is not None

    await s.__aexit__(None, None, None)


@pytest.mark.asyncio
async def test_multitickstream_does_not_stop_iteration_when_temporarily_unsubscribed(monkeypatch):
    s = MultiTickStream(_Dummy(), types.SimpleNamespace(account_id=1, tick_queue_size=10), _Symbols(), ["EURUSD"])

    monkeypatch.setattr(s, "_subscribe", lambda: asyncio.sleep(0))
    monkeypatch.setattr(s, "_unsubscribe", lambda: asyncio.sleep(0))

    await s.__aenter__()
    assert s._active is True
    s._subscribed = False

    await s._queue.put(types.SimpleNamespace())
    item = await asyncio.wait_for(s.__anext__(), timeout=1)
    assert item is not None

    await s.__aexit__(None, None, None)
