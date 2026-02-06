"""Example: Reconnect + stream recovery.

This demonstrates that tick stream iterators stay alive and are resubscribed after reconnect.

We simulate a connection drop by calling `client.disconnect()` and then `client.connect()`.
In real deployments, the reconnect loop is triggered by a transport/protocol error.

Notes:
- Requires valid CTRADER_* env vars.
- Uses a short run window; adjust as needed.
"""

from __future__ import annotations

import asyncio

from ctc import CTraderClient


async def main() -> None:
    async with CTraderClient.from_env(auto_enable_features=True) as client:
        print("✅ Connected")

        async def consumer() -> None:
            async with client.market_data.stream_ticks("EURUSD") as stream:
                n = 0
                async for tick in stream:
                    n += 1
                    print("tick", n, tick.symbol_name, tick.bid, tick.ask)
                    if n >= 20:
                        break

        consumer_task = asyncio.create_task(consumer())

        # Let a few ticks arrive
        await asyncio.sleep(2.0)

        print("\n⚠️  Simulating connection drop: disconnect() -> connect()\n")
        await client.disconnect()
        await asyncio.sleep(1.0)
        await client.connect()
        print("✅ Reconnected")

        # After reconnect, active streams should be resubscribed.
        await consumer_task


if __name__ == "__main__":
    asyncio.run(main())
