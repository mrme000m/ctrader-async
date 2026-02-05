from __future__ import annotations

import types
import pytest

from ctrader_async.client import CTraderClient


@pytest.mark.asyncio
async def test_client_auto_enables_bridges(monkeypatch):
    # Patch connect internals to avoid real networking; we only validate the auto-enable logic
    c = CTraderClient(
        client_id="x",
        client_secret="y",
        access_token="z",
        account_id=1,
        host_type="demo",
        auto_model_bridge=True,
        auto_cache_updater=True,
    )

    # Patch TCPTransport construction to return a fake transport with async connect
    class _FakeTCP:
        def __init__(self, *a, **k):
            self._connected = True

        async def connect(self, *a, **k):
            return

        async def close(self):
            return

        def is_connected(self):
            return True

    monkeypatch.setattr("ctrader_async.client.TCPTransport", _FakeTCP)

    class _FakeProtocol:
        def __init__(self):
            self.dispatcher = types.SimpleNamespace(register_default=lambda *a, **k: None, register=lambda *a, **k: None)

        async def start(self):
            return

    c._protocol = _FakeProtocol()

    # Monkeypatch network/auth/symbol load steps to no-op
    monkeypatch.setattr("ctrader_async.client.get_host", lambda *_: "localhost")

    async def _noop(*args, **kwargs):
        return

    # authenticator
    class _FakeAuth:
        def __init__(self, *a, **k):
            pass

        async def authenticate(self, **k):
            return True

    monkeypatch.setattr("ctrader_async.client.Authenticator", _FakeAuth)

    # symbol catalog
    class _FakeSymbols:
        def __init__(self, *a, **k):
            self._symbols_by_name = {"EURUSD": object()}

        async def load(self):
            return

    monkeypatch.setattr("ctrader_async.client.SymbolCatalog", _FakeSymbols)

    # APIs
    class _FakeTrading:
        def __init__(self, *a, **k):
            import asyncio
            self._orders = []
            self._positions = []
            self._orders_lock = asyncio.Lock()
            self._positions_lock = asyncio.Lock()

    class _FakeMarket:
        def __init__(self, *a, **k):
            pass

    class _FakeAccount:
        def __init__(self, *a, **k):
            pass

    monkeypatch.setattr("ctrader_async.client.TradingAPI", _FakeTrading)
    monkeypatch.setattr("ctrader_async.client.MarketDataAPI", _FakeMarket)
    monkeypatch.setattr("ctrader_async.client.AccountAPI", _FakeAccount)

    # Patch ProtocolHandler construction to reuse existing protocol
    monkeypatch.setattr("ctrader_async.client.ProtocolHandler", lambda *_a, **_k: c._protocol)

    await c.connect()

    assert c.model_bridge is not None
    assert c.state_cache_updater is not None
    # both should be enabled
    assert c.model_bridge._enabled is True
    assert c.state_cache_updater._enabled is True
