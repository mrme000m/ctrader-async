"""Example: Streaming tick data for multiple symbols.

Demonstrates `MarketDataAPI.stream_ticks_multi(..., coalesce_latest=True)`, which is useful
when you want to monitor many symbols without unbounded buffering.

Notes:
- If your consumer is slower than the producer, `coalesce_latest=True` keeps only the latest
  tick per symbol.
"""

import asyncio

from ctc import CTraderClient


async def main() -> None:
    async with CTraderClient.from_env() as client:
        print("✅ Connected")

        symbols = ["EURUSD", "GBPUSD", "USDJPY"]
        print(f"\n📊 Streaming ticks for: {', '.join(symbols)} (Ctrl+C to stop)\n")

        async with client.market_data.stream_ticks_multi(symbols, coalesce_latest=True) as stream:
            n = 0
            async for tick in stream:
                n += 1
                print(f"#{n:4d} {tick.symbol_name:<6} bid={tick.bid:.5f} ask={tick.ask:.5f} ts={tick.timestamp}")
                if n >= 200:
                    print("\n✅ Received 200 ticks, stopping...")
                    break


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Stopped by user")
