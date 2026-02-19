from __future__ import annotations

import asyncio
import types
import pytest

from ctc.client import CTraderClient


@pytest.mark.asyncio
async def test_client_auto_enables_bridges(monkeypatch):
    """
    Verify that auto_model_bridge=True and auto_cache_updater=True cause both
    subsystems to be enabled after connect().  All network/server interactions
    are replaced with no-op fakes so no real connection is attempted.
    """
    c = CTraderClient(
        client_id="x",
        client_secret="y",
        access_token="z",
        account_id=1,
        host_type="demo",
        auto_model_bridge=True,
        auto_cache_updater=True,
    )

    # ------------------------------------------------------------------
    # Fake TCP transport — no real socket
    # ------------------------------------------------------------------
    class _FakeTCP:
        def __init__(self, *a, **k):
            self._connected = True

        async def connect(self, *a, **k):
            return

        async def close(self):
            return

        def is_connected(self):
            return True

    monkeypatch.setattr("ctc.client.TCPTransport", _FakeTCP)

    # ------------------------------------------------------------------
    # Fake ProtocolHandler — satisfies every call made during connect()
    # ------------------------------------------------------------------
    class _FakeProtocol:
        def __init__(self, *a, **k):
            self.dispatcher = types.SimpleNamespace(
                register_default=lambda *a, **k: None,
                register=lambda *a, **k: None,
                unregister=lambda *a, **k: None,
            )
            self.hooks = types.SimpleNamespace(
                register=lambda *a, **k: None,
            )
            self.events = types.SimpleNamespace(
                on=lambda *a, **k: None,
                off=lambda *a, **k: None,
                emit=_async_noop,
            )

        async def start(self):
            return

        async def send_request(self, *a, **k):
            return None

    async def _async_noop(*a, **k):
        return

    monkeypatch.setattr("ctc.client.ProtocolHandler", _FakeProtocol)

    # ------------------------------------------------------------------
    # Fake authenticator
    # ------------------------------------------------------------------
    class _FakeAuth:
        def __init__(self, *a, **k):
            pass

        async def authenticate(self, **k):
            return True

    monkeypatch.setattr("ctc.client.Authenticator", _FakeAuth)

    # ------------------------------------------------------------------
    # Fake symbol catalog
    # ------------------------------------------------------------------
    class _FakeSymbols:
        def __init__(self, *a, **k):
            self._symbols_by_name = {"EURUSD": object()}

        async def load(self):
            return

    monkeypatch.setattr("ctc.client.SymbolCatalog", _FakeSymbols)

    # ------------------------------------------------------------------
    # Fake asset catalog — satisfies assets.load() call in connect()
    # ------------------------------------------------------------------
    class _FakeAssets:
        def __init__(self, *a, **k):
            pass

        async def load(self):
            return

    monkeypatch.setattr("ctc.client.AssetCatalog", _FakeAssets)

    # ------------------------------------------------------------------
    # Fake trading / market / account APIs
    # ------------------------------------------------------------------
    class _FakeTrading:
        def __init__(self, *a, **k):
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

    monkeypatch.setattr("ctc.client.TradingAPI", _FakeTrading)
    monkeypatch.setattr("ctc.client.MarketDataAPI", _FakeMarket)
    monkeypatch.setattr("ctc.client.AccountAPI", _FakeAccount)

    # ------------------------------------------------------------------
    # Misc patches
    # ------------------------------------------------------------------
    monkeypatch.setattr("ctc.client.get_host", lambda *_: "localhost")

    await c.connect()

    assert c.model_bridge is not None
    assert c.state_cache_updater is not None
    assert c.model_bridge._enabled is True
    assert c.state_cache_updater._enabled is True
