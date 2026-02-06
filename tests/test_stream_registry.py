from __future__ import annotations

import pytest

from ctrader_async.utils.stream_registry import StreamRegistry


class _S:
    def __init__(self):
        self.calls = 0

    async def resubscribe(self, protocol, symbols) -> None:
        self.calls += 1


@pytest.mark.asyncio
async def test_registry_resubscribes_all_best_effort():
    r = StreamRegistry()
    s1 = _S()
    s2 = _S()
    r.register(s1)
    r.register(s2)

    await r.resubscribe_all(protocol=object(), symbols=object())

    assert s1.calls == 1
    assert s2.calls == 1

    r.unregister(s1)
    await r.resubscribe_all(protocol=object(), symbols=object())
    assert s1.calls == 1
    assert s2.calls == 2
