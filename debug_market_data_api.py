#!/usr/bin/env python3
"""
Market Data API Debug Script

Tests: get_candles, get_tick_data, stream_ticks (brief),
       stream_depth (brief), candle field verification.
"""

import asyncio
import logging
from dotenv import load_dotenv
from ctc import CTraderClient
from ctc.enums import TimeFrame

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    load_dotenv()
    client = CTraderClient.from_env()
    await client.connect()

    logger.info("=" * 60)
    logger.info("📊 MARKET DATA API DEBUG")
    logger.info("=" * 60)

    try:
        # ── 1. Historical candles (XAUUSD, H1, 10 bars) ─────────────────
        logger.info("\n🕯️  1. Historical candles (XAUUSD H1, 10 bars)")
        candles = await client.market_data.get_candles("XAUUSD", TimeFrame.H1, count=10)
        logger.info(f"   Received {len(candles)} candles")
        for c in candles[-3:]:
            logger.info(
                f"   {c.timestamp.strftime('%Y-%m-%d %H:%M')} "
                f"O={c.open} H={c.high} L={c.low} C={c.close} V={c.volume} "
                f"{'▲' if c.is_bullish else '▼'}"
            )

        # ── 2. Historical candles (EURUSD, M15) ─────────────────────────
        logger.info("\n🕯️  2. Historical candles (EURUSD M15, 5 bars)")
        candles_eu = await client.market_data.get_candles("EURUSD", TimeFrame.M15, count=5)
        logger.info(f"   Received {len(candles_eu)} candles")
        for c in candles_eu[-3:]:
            logger.info(
                f"   {c.timestamp.strftime('%Y-%m-%d %H:%M')} "
                f"O={c.open} H={c.high} L={c.low} C={c.close} V={c.volume}"
            )

        # ── 3. Tick data (historical BID ticks, EURUSD, 1h) ─────────────
        logger.info("\n📈 3. Historical tick data (EURUSD BID, 1h window, up to 100 ticks)")
        ticks = await client.market_data.get_tick_data("EURUSD", quote_type="BID", count=100)
        logger.info(f"   Received {len(ticks)} ticks")
        if ticks:
            logger.info(f"   First tick: ts={ticks[0]['timestamp']} price={ticks[0]['price']}")
            logger.info(f"   Last tick : ts={ticks[-1]['timestamp']} price={ticks[-1]['price']}")
            prices = [t['price'] for t in ticks]
            logger.info(f"   Price range: {min(prices):.5f} – {max(prices):.5f}")

        # ── 4. Live tick streaming (XAUUSD, 3 ticks) ────────────────────
        logger.info("\n📡 4. Live tick streaming (XAUUSD, 3 ticks)")
        tick_count = 0
        try:
            async with asyncio.timeout(10):
                async with client.market_data.stream_ticks("XAUUSD") as stream:
                    async for tick in stream:
                        logger.info(
                            f"   Tick: bid={tick.bid} ask={tick.ask} "
                            f"spread={tick.ask - tick.bid:.5f} "
                            f"mid={tick.mid_price:.5f}"
                        )
                        tick_count += 1
                        if tick_count >= 3:
                            break
        except asyncio.TimeoutError:
            logger.warning("   ⚠️ Tick stream timeout (market may be closed)")

        # ── 5. Live depth streaming (EURUSD, 1 snapshot) ────────────────
        logger.info("\n📚 5. Live depth streaming (EURUSD, 1 snapshot)")
        snap_count = 0
        try:
            async with asyncio.timeout(10):
                async with client.market_data.stream_depth("EURUSD", depth=5) as stream:
                    async for snap in stream:
                        logger.info(f"   Depth snapshot for {snap.symbol_name}:")
                        logger.info(f"   Best bid: {snap.best_bid.price if snap.best_bid else 'N/A'} "
                                    f"({snap.best_bid.volume if snap.best_bid else 0:.2f} lots)")
                        logger.info(f"   Best ask: {snap.best_ask.price if snap.best_ask else 'N/A'} "
                                    f"({snap.best_ask.volume if snap.best_ask else 0:.2f} lots)")
                        logger.info(f"   Spread: {snap.spread}")
                        logger.info(f"   Total bid vol (5 levels): {snap.total_bid_volume(5):.2f}")
                        logger.info(f"   Total ask vol (5 levels): {snap.total_ask_volume(5):.2f}")
                        snap_count += 1
                        if snap_count >= 1:
                            break
        except asyncio.TimeoutError:
            logger.warning("   ⚠️ Depth stream timeout (market may be closed)")
        except AttributeError as e:
            logger.warning(f"   ⚠️ Depth stream not supported in this transport: {e}")

        logger.info("\n" + "=" * 60)
        logger.info("✅ Market Data API debug complete")

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
