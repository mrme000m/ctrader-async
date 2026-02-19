from __future__ import annotations

import asyncio
import logging
import time
import types

import pytest

from ctc.client import CTraderClient
from ctc.utils.logging import JsonLogFormatter


def test_json_log_formatter_emits_structured_payload():
    formatter = JsonLogFormatter()
    record = logging.LogRecord(
        name="ctc.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )

    output = formatter.format(record)
    assert '"logger": "ctc.test"' in output
    assert '"level": "INFO"' in output
    assert '"message": "hello world"' in output
    assert '"timestamp":' in output


@pytest.mark.asyncio
async def test_stale_connection_watchdog_triggers_reconnect(monkeypatch):
    client = CTraderClient(
        client_id="id",
        client_secret="secret",
        access_token="token",
        account_id=1,
        stale_connection_timeout=0.1,
        watchdog_check_interval=0.01,
    )

    client._connected = True
    client._authenticated = True
    client._last_inbound_monotonic = time.monotonic() - 2.0
    client._transport = types.SimpleNamespace(is_connected=lambda: True)

    called = {"count": 0}

    async def _fake_connection_lost(_evt):
        called["count"] += 1

    monkeypatch.setattr(client, "_on_protocol_connection_lost", _fake_connection_lost)

    task = asyncio.create_task(client._stale_connection_watchdog_loop())
    await asyncio.sleep(0.65)
    client._closing = True
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert called["count"] >= 1


@pytest.mark.asyncio
async def test_token_auto_refresh_updates_tokens_and_reauths(monkeypatch):
    client = CTraderClient(
        client_id="id",
        client_secret="secret",
        access_token="old-access",
        account_id=1,
        token_auto_refresh_enabled=True,
        refresh_token="old-refresh",
        token_refresh_margin_seconds=0.0,
        token_refresh_default_expires_in=1,
    )

    client._connected = True
    client._authenticated = True
    client._token_expires_in = 0

    refreshed = {"count": 0}

    class _FakeSession:
        async def refresh_token(self, refresh_token: str):
            refreshed["count"] += 1
            assert refresh_token in ("old-refresh", "new-refresh")
            return {
                "access_token": "new-access",
                "refresh_token": "new-refresh",
                "expires_in": 999,
                "token_type": "Bearer",
            }

    client.session = _FakeSession()

    reauthed = {"count": 0}

    async def _fake_reauth():
        reauthed["count"] += 1

    monkeypatch.setattr(client, "_reauth_account_with_current_token", _fake_reauth)

    task = asyncio.create_task(client._token_auto_refresh_loop())
    await asyncio.sleep(0.7)
    client._closing = True
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert refreshed["count"] >= 1
    assert reauthed["count"] >= 1
    assert client.config.access_token == "new-access"
    assert client.config.refresh_token == "new-refresh"
