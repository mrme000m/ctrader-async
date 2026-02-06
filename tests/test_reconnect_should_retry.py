from __future__ import annotations

import pytest

from ctc.utils.reconnect import ReconnectManager, ReconnectConfig
from ctc.utils.errors import AuthenticationError


@pytest.mark.asyncio
async def test_reconnect_manager_should_retry_blocks_fatal():
    mgr = ReconnectManager(ReconnectConfig(enabled=True, max_attempts=5, base_delay=0.0, max_delay=0.0, jitter=False))

    calls = 0

    async def connect():
        nonlocal calls
        calls += 1
        raise AuthenticationError("bad creds")

    with pytest.raises(AuthenticationError):
        await mgr.connect_with_retry(connect, should_retry=lambda e: not isinstance(e, AuthenticationError))

    assert calls == 1
