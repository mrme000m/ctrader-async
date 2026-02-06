from __future__ import annotations

import asyncio
import types

import pytest

from ctc.utils import EventBus
from ctc.utils.typed_events import TickEvent
from ctc.models import Tick
from ctc.streams.multi_tick_stream import MultiTickStream


class _FakeSymbols:
    def __init__(self, mapping: dict[str, int]):
        self._name_to_id = {k.upper(): v for k, v in mapping.items()}
        self._id_to_name = {v: k for k, v in mapping.items()}

    async def get_symbol(self, name: str):
        sid = self._name_to_id.get(name.upper())
        if sid is None:
            return None
        return types.SimpleNamespace(id=sid, name=name)


class _FakeDispatcher:
    def __init__(self):
        self.handlers = {}

    def register(self, payload_type: int, handler):
        self.handlers.setdefault(payload_type, []).append(handler)

    def unregister(self, payload_type: int, handler):
        if handler in self.handlers.get(payload_type, []):
            self.handlers[payload_type].remove(handler)


class _FakeProtocol:
    def __init__(self):
        self.dispatcher = _FakeDispatcher()
        self.sent = []

    async def send_request(self, req, **kwargs):
        self.sent.append((req, kwargs))
        return types.SimpleNamespace()


class _FakeEnvelope:
    def __init__(self, symbol_id: int, bid: int, ask: int, ts: int):
        self.payloadType = 0
        self.clientMsgId = ""
        # provide a payload-like object
        self._payload = types.SimpleNamespace(symbolId=symbol_id, bid=bid, ask=ask, timestamp=ts)


@pytest.mark.asyncio
async def test_eventbus_tick_event_emission():
    bus = EventBus()
    got = []

    async def handler(evt: TickEvent):
        got.append(evt.tick.symbol_name)

    bus.on("tick", handler)

    tick = Tick(symbol_id=1, symbol_name="EURUSD", bid=1.0, ask=1.1, timestamp=123)
    await bus.emit("tick", TickEvent(tick=tick, symbol_id=1, symbol_name="EURUSD", timestamp=123))

    assert got == ["EURUSD"]


@pytest.mark.asyncio
async def test_multitickstream_coalesces_latest(monkeypatch):
    # Patch ProtocolFraming.extract_payload used by stream
    from ctc.transport import ProtocolFraming

    monkeypatch.setattr(ProtocolFraming, "extract_payload", lambda env: env._payload)

    proto = _FakeProtocol()
    cfg = types.SimpleNamespace(account_id=1, tick_queue_size=2)
    syms = _FakeSymbols({"EURUSD": 101, "GBPUSD": 102})

    stream = MultiTickStream(proto, cfg, syms, ["EURUSD", "GBPUSD"], coalesce_latest=True)

    await stream.__aenter__()

    # Find registered handler (payload type resolved from actual pb2 in runtime,
    # but our stream registers whatever ProtoOASpotEvent().payloadType is.
    # We just call the handler directly.
    spot_handlers = list(proto.dispatcher.handlers.values())[0]
    on_spot = spot_handlers[0]

    # Send two ticks for same symbol quickly -> should keep only latest
    await on_spot(_FakeEnvelope(101, 100000, 100010, 1))
    await on_spot(_FakeEnvelope(101, 100020, 100030, 2))

    # Flush task runs asynchronously; give it a tick
    await asyncio.sleep(0)

    t = await asyncio.wait_for(stream.__anext__(), timeout=1)
    assert isinstance(t, Tick)
    assert t.symbol_id == 101
    assert t.timestamp == 2

    await stream.__aexit__(None, None, None)
