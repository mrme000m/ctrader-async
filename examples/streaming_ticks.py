"""Example: Streaming real-time tick data.

Notes:
- This example is intentionally minimal.
- For production workloads, avoid performing network I/O per tick.
"""

import asyncio

from ctrader_async import CTraderClient


async def main():
    """Stream real-time tick data."""

    async with CTraderClient.from_env() as client:
        print("✅ Connected")
        print("\n📊 Streaming EURUSD ticks (press Ctrl+C to stop)...\n")

        # --- Optional observability knobs ---
        # Enable library debug logs:
        #
        # import logging
        # logging.basicConfig(level=logging.INFO)
        # logging.getLogger("ctrader_async").setLevel(logging.DEBUG)
        #
        # Capture per-request timings via hooks:
        #
        # import time
        # inflight: dict[str, float] = {}
        #
        # async def post_send(ctx):
        #     inflight[ctx.data["client_msg_id"]] = time.perf_counter()
        #
        # async def post_resp(ctx):
        #     msg_id = ctx.data["client_msg_id"]
        #     dt = time.perf_counter() - inflight.pop(msg_id, time.perf_counter())
        #     print("request", ctx.data["request_type"], "took", dt)
        #
        # client.hooks.register("protocol.post_send_request", post_send)
        # client.hooks.register("protocol.post_response", post_resp)

        # Best practice: do not perform I/O per tick. Cache symbol metadata once.
        symbol = await client.symbols.get_symbol("EURUSD")
        pip_size = symbol.pip_size if symbol else 0.0001

        # Stream ticks using async iterator
        async with client.market_data.stream_ticks("EURUSD") as stream:
            tick_count = 0

            async for tick in stream:
                tick_count += 1

                # Calculate spread in pips
                spread_pips = (tick.ask - tick.bid) / pip_size

                # Print tick data
                print(
                    f"Tick #{tick_count:4d}: "
                    f"Bid={tick.bid:.5f} | "
                    f"Ask={tick.ask:.5f} | "
                    f"Mid={tick.mid_price:.5f} | "
                    f"Spread={spread_pips:.1f} pips"
                )

                # Exit after 100 ticks for demo
                if tick_count >= 100:
                    print("\n✅ Received 100 ticks, stopping...")
                    break


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Stopped by user")
