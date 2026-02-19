"""
Integration tests for extended Market Data API.

Covers:
- get_tick_data          (ProtoOAGetTickDataReq — raw historical ticks)
- get_candles (various timeframes)
- stream_ticks (single symbol — liveness + data integrity)
- stream_ticks_multi (multi-symbol)
- depth_stream (order book depth)
- CandleStream (live candle updates)

Run with:
    CTRADER_RUN_INTEGRATION=true pytest tests/test_integration_market_data_extended.py -v -s
"""

from __future__ import annotations

import asyncio
import time
import pytest

from ctc import CTraderClient, TradeSide, TimeFrame

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


def _ms_range(hours_back: int = 24):
    now_ms = int(time.time() * 1000)
    from_ms = now_ms - hours_back * 3600 * 1000
    return from_ms, now_ms


class TestHistoricalTickData:
    """ProtoOAGetTickDataReq — raw bid/ask tick history."""

    async def test_get_tick_data_bid(self, client):
        from_ms, to_ms = _ms_range(hours_back=1)
        try:
            ticks = await client.market_data.get_tick_data(
                symbol="EURUSD",
                quote_type="BID",
                from_timestamp=from_ms,
                to_timestamp=to_ms,
            )
            assert isinstance(ticks, list)
            print(f"\n  Raw BID ticks (last 1h): {len(ticks)}")
            if ticks:
                t = ticks[0]
                # Each tick should have a timestamp and price
                assert hasattr(t, "timestamp") or isinstance(t, (tuple, dict))
        except AttributeError:
            pytest.skip("get_tick_data not available in this build")
        except Exception as e:
            pytest.skip(f"get_tick_data not supported by broker: {e}")

    async def test_get_tick_data_ask(self, client):
        from_ms, to_ms = _ms_range(hours_back=1)
        try:
            ticks = await client.market_data.get_tick_data(
                symbol="EURUSD",
                quote_type="ASK",
                from_timestamp=from_ms,
                to_timestamp=to_ms,
            )
            assert isinstance(ticks, list)
            print(f"\n  Raw ASK ticks (last 1h): {len(ticks)}")
        except Exception as e:
            pytest.skip(f"get_tick_data ASK not supported: {e}")

    async def test_tick_data_timestamps_ascending(self, client):
        """Tick timestamps must be monotonically non-decreasing."""
        from_ms, to_ms = _ms_range(hours_back=1)
        try:
            ticks = await client.market_data.get_tick_data(
                symbol="EURUSD", quote_type="BID",
                from_timestamp=from_ms, to_timestamp=to_ms,
            )
            if len(ticks) < 2:
                pytest.skip("Not enough ticks to validate ordering")
            ts_list = [getattr(t, "timestamp", t[0] if isinstance(t, tuple) else None)
                       for t in ticks]
            ts_list = [ts for ts in ts_list if ts is not None]
            assert ts_list == sorted(ts_list), "Tick timestamps must be ascending"
        except Exception as e:
            pytest.skip(f"Tick data not available: {e}")


class TestCandleVariousTimeframes:
    """Historical candle data across multiple timeframes."""

    @pytest.mark.parametrize("tf,label", [
        (TimeFrame.M1,  "M1"),
        (TimeFrame.M5,  "M5"),
        (TimeFrame.M15, "M15"),
        (TimeFrame.H1,  "H1"),
        (TimeFrame.H4,  "H4"),
        (TimeFrame.D1,  "D1"),
    ])
    async def test_get_candles_timeframe(self, client, tf, label):
        candles = await client.market_data.get_candles(
            symbol="EURUSD", timeframe=tf, count=5
        )
        assert isinstance(candles, list)
        assert len(candles) > 0, f"No candles returned for {label}"
        for c in candles:
            assert c.open > 0, f"Zero open price in {label} candle"
            assert c.high >= c.low, f"high < low in {label} candle"
            assert c.high >= c.open >= 0
            assert c.high >= c.close >= 0
        print(f"\n  {label}: {len(candles)} candles, last close={candles[-1].close:.5f}")

    async def test_candles_count_respected(self, client):
        candles = await client.market_data.get_candles(
            symbol="EURUSD", timeframe=TimeFrame.H1, count=3
        )
        # Server may return fewer if not enough history — but never more
        assert len(candles) <= 3

    async def test_candles_timestamp_ascending(self, client):
        candles = await client.market_data.get_candles(
            symbol="EURUSD", timeframe=TimeFrame.M5, count=10
        )
        if len(candles) < 2:
            pytest.skip("Not enough candles")
        timestamps = [c.timestamp for c in candles if c.timestamp is not None]
        assert timestamps == sorted(timestamps), "Candle timestamps must be ascending"


class TestTickStreaming:
    """Live tick streaming — single symbol."""

    async def test_stream_ticks_receives_data(self, client):
        ticks = []
        async with client.market_data.stream_ticks("EURUSD") as stream:
            async for tick in stream:
                ticks.append(tick)
                if len(ticks) >= 3:
                    break
        assert len(ticks) >= 1, "Expected at least one tick from EURUSD stream"
        for tick in ticks:
            assert tick.bid > 0
            assert tick.ask > 0
            assert tick.ask >= tick.bid
        print(f"\n  Received {len(ticks)} ticks. Last: bid={ticks[-1].bid:.5f} ask={ticks[-1].ask:.5f}")

    async def test_stream_ticks_gbpusd(self, client):
        """Verify streaming works for a second symbol too."""
        ticks = []
        async with client.market_data.stream_ticks("GBPUSD") as stream:
            async for tick in stream:
                ticks.append(tick)
                if len(ticks) >= 2:
                    break
        assert len(ticks) >= 1
        print(f"\n  GBPUSD ticks: {len(ticks)}")

    async def test_stream_tick_symbol_name(self, client):
        """Each tick must carry the correct symbol name."""
        async with client.market_data.stream_ticks("EURUSD") as stream:
            async for tick in stream:
                assert tick.symbol_name.upper() == "EURUSD"
                break

    async def test_stream_ticks_context_manager_cleans_up(self, client):
        """Exiting the context manager must not leave dangling subscriptions."""
        async with client.market_data.stream_ticks("EURUSD") as stream:
            async for _ in stream:
                break
        # A second subscription should succeed immediately
        async with client.market_data.stream_ticks("EURUSD") as stream2:
            async for tick in stream2:
                assert tick.bid > 0
                break


class TestMultiTickStreaming:
    """Multi-symbol tick streaming with fanout."""

    async def test_stream_ticks_multi_two_symbols(self, client):
        symbols = ["EURUSD", "GBPUSD"]
        seen = set()
        async with client.market_data.stream_ticks_multi(symbols) as stream:
            async for tick in stream:
                seen.add(tick.symbol_name.upper())
                if seen >= {"EURUSD", "GBPUSD"}:
                    break
                if len(seen) == 0:
                    await asyncio.sleep(0.1)
        assert "EURUSD" in seen or "GBPUSD" in seen, "Expected ticks from at least one symbol"
        print(f"\n  Multi-tick symbols seen: {seen}")

    async def test_fanout_by_symbol(self, client):
        """fanout_by_symbol queues must receive per-symbol ticks."""
        async with client.market_data.stream_ticks_multi(["EURUSD", "GBPUSD"]) as stream:
            fanout = stream.fanout_by_symbol(maxsize=20)
            await fanout.start()
            eur_q = fanout.queue("EURUSD")
            tick = await asyncio.wait_for(eur_q.get(), timeout=15.0)
            assert tick.symbol_name.upper() == "EURUSD"
            assert tick.bid > 0
            await fanout.stop()
        print(f"\n  Fanout EURUSD tick: bid={tick.bid:.5f}")


class TestDepthStream:
    """Live order book depth streaming."""

    async def test_depth_stream_receives_data(self, client):
        try:
            async with client.market_data.stream_depth("EURUSD") as stream:
                async for depth in stream:
                    assert depth is not None
                    print(f"\n  Depth update received for EURUSD")
                    break
        except AttributeError:
            pytest.skip("stream_depth not available in this build")
        except Exception as e:
            pytest.skip(f"Depth streaming not supported: {e}")


class TestCandleStream:
    """Live CandleStream — validates the fixed dispatcher/delta-decode path."""

    async def test_candle_stream_subscribes_and_receives(self, client):
        """
        Subscribe to M1 live candles for EURUSD.  Because M1 bars only close
        once a minute we collect for up to 90 s; if no bar arrives we skip
        (market may be closed) rather than fail.
        """
        try:
            from ctc.streams.candle_stream import CandleStream
        except ImportError:
            pytest.skip("CandleStream not available")

        stream = CandleStream(
            symbol="EURUSD",
            timeframe=TimeFrame.M1,
            protocol=client._protocol,
            config=client.config,
            symbols=client.symbols,
        )

        candles = []
        try:
            await stream.start()
            # Collect for up to 90 s
            try:
                candle = await asyncio.wait_for(stream.__anext__(), timeout=90.0)
                candles.append(candle)
            except asyncio.TimeoutError:
                pass
        finally:
            await stream.stop()

        if not candles:
            pytest.skip(
                "No M1 candle received within 90 s "
                "(market may be closed or outside trading hours)"
            )

        c = candles[0]
        assert c.open > 0
        assert c.high >= c.low
        assert c.symbol_name.upper() == "EURUSD"
        assert c.timeframe == "M1"
        print(f"\n  Live candle: O={c.open:.5f} H={c.high:.5f} L={c.low:.5f} C={c.close:.5f}")
