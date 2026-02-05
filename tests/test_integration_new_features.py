"""Integration tests for recently added automation features.

These are only executed when the shared integration fixture is enabled
(CTRADER_RUN_INTEGRATION=true).
"""

from __future__ import annotations

import asyncio
import pytest

from ctrader_async import TickEvent

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


class TestTypedEvents:
    async def test_tick_typed_event_emits(self, client):
        # Subscribe to at least one tick and assert TickEvent arrives
        got: list[TickEvent] = []

        def on_tick(evt: TickEvent):
            got.append(evt)

        client.events.on("tick", on_tick)

        async with client.market_data.stream_ticks("EURUSD") as _:
            # wait a bit for events
            for _ in range(50):
                if got:
                    break
                await asyncio.sleep(0.1)

        assert got, "Expected at least one TickEvent"
        assert got[0].tick.symbol_name


class TestMultiTickStreamFanout:
    async def test_stream_ticks_multi_and_fanout(self, client):
        async with client.market_data.stream_ticks_multi(["EURUSD", "GBPUSD"], coalesce_latest=True) as stream:
            fanout = stream.fanout_by_symbol(maxsize=10)
            await fanout.start()

            eur_q = fanout.queue("EURUSD")

            tick = await asyncio.wait_for(eur_q.get(), timeout=10.0)
            assert tick.symbol_name.upper() == "EURUSD"

            await fanout.stop()


class TestBulkTradingOps:
    async def test_bulk_helpers_exist_and_run(self, client):
        # Ensure bulk helpers execute without error on empty sets
        await client.trading.close_positions_bulk([], concurrency=2)
        await client.trading.cancel_orders_bulk([], concurrency=2)
        await client.trading.modify_positions_bulk([], concurrency=2)
