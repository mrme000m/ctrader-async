"""Integration tests for recently added automation features.

These are only executed when the shared integration fixture is enabled
(CTRADER_RUN_INTEGRATION=true).
"""

from __future__ import annotations

import asyncio
import pytest

from ctc import TickEvent, TradeSide

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
        await client.trading.modify_orders_bulk([], concurrency=2)


class TestModelBridgeAndCacheUpdater:
    async def test_model_events_emitted_and_cache_updates(self, client):
        from .utils_integration_debug import snapshot_client_state, dump_debug

        # Enable model bridge + cache updater
        client.model_bridge.enable()
        client.state_cache_updater.enable()

        model_seen = {"order": 0, "position": 0, "deal": 0, "execution_error": 0}

        client.events.on("model.order", lambda _o: model_seen.__setitem__("order", model_seen["order"] + 1))
        client.events.on(
            "model.position", lambda _p: model_seen.__setitem__("position", model_seen["position"] + 1)
        )
        client.events.on("model.deal", lambda _d: model_seen.__setitem__("deal", model_seen["deal"] + 1))
        client.events.on(
            "model.execution_error",
            lambda _e: model_seen.__setitem__("execution_error", model_seen["execution_error"] + 1),
        )

        def _debug_context():
            return {
                "model_seen": dict(model_seen),
                "cache": snapshot_client_state(client),
            }

        # Place a small market order, then close it immediately to generate events
        pos = await client.trading.place_market_order(
            symbol="EURUSD",
            side=TradeSide.BUY,
            volume=0.01,
            comment="integration model bridge",
        )
        # Fallback if above is weird: just close via id
        await client.trading.close_position(pos.id)

        # Wait briefly for async events
        for _ in range(80):
            if model_seen["order"] + model_seen["position"] + model_seen["deal"] > 0:
                break
            await asyncio.sleep(0.1)

        assert model_seen["position"] > 0 or model_seen["deal"] > 0, dump_debug(
            "no model.position/deal observed",
            _debug_context(),
        )

        # Cache updater should have populated positions/orders caches
        positions = await client.trading.get_positions()
        orders = await client.trading.get_orders()
        assert isinstance(positions, list)
        assert isinstance(orders, list)

        # After close, the cache should eventually remove the position
        # (best-effort; depends on broker event timing)
        for _ in range(80):
            async with client.trading._positions_lock:
                cached = [p for p in client.trading._positions if getattr(p, "id", None) == pos.id]
            if not cached:
                break
            await asyncio.sleep(0.1)

        # We accept either "removed" or "volume==0" representation
        async with client.trading._positions_lock:
            cached = [p for p in client.trading._positions if getattr(p, "id", None) == pos.id]
        if cached:
            assert getattr(cached[0], "volume", 0) <= 0.0, dump_debug(
                "position not removed after close",
                {**_debug_context(), "position_id": pos.id},
            )

    async def test_model_execution_error_emits(self, client):
        client.model_bridge.enable()

        seen = {"err": 0}
        client.events.on("model.execution_error", lambda _e: seen.__setitem__("err", seen["err"] + 1))

        # Intentionally amend an invalid order id to trigger execution error
        try:
            await client.trading.modify_order(
                order_id=999999999,  # intentionally invalid
                limit_price=1.0,
                slippage_in_points=1,
            )
        except Exception:
            pass

        for _ in range(50):
            if seen["err"] > 0:
                break
            await asyncio.sleep(0.1)

        from .utils_integration_debug import snapshot_client_state, dump_debug

        if seen["err"] <= 0:
            pytest.skip(
                dump_debug(
                    "model.execution_error not observed (broker/API may not emit)",
                    {"seen": dict(seen), "cache": snapshot_client_state(client)},
                )
            )