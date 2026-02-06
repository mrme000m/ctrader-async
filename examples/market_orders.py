"""
Example: Placing different types of orders.
"""

import asyncio
from ctc import CTraderClient, TradeSide, TimeInForce


async def main():
    """Place different order types."""

    async with CTraderClient.from_env() as client:

        # --- Optional observability knobs ---
        # Enable library debug logs:
        #
        # import logging
        # logging.basicConfig(level=logging.INFO)
        # logging.getLogger("ctc").setLevel(logging.DEBUG)
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

        print("✅ Connected")
        
        # 1. Place a market order with SL/TP
        print("\n📈 Placing market order...")
        position = await client.trading.place_market_order(
            symbol="EURUSD",
            side=TradeSide.BUY,
            volume=0.01,  # 0.01 lots (micro lot)
            stop_loss=1.0900,
            take_profit=1.1100,
            comment="Market order example"
        )
        print(f"✅ Position opened: #{position.id}")
        print(f"   Entry Price: {position.entry_price}")
        print(f"   Stop Loss: {position.stop_loss}")
        print(f"   Take Profit: {position.take_profit}")
        
        # 2. Place a limit order
        print("\n📋 Placing limit order...")
        order = await client.trading.place_limit_order(
            symbol="EURUSD",
            side=TradeSide.BUY,
            volume=0.01,
            price=1.0950,  # Buy at 1.0950 or better
            stop_loss=1.0900,
            take_profit=1.1100,
            time_in_force=TimeInForce.GOOD_TILL_CANCEL,
            comment="Limit order example"
        )
        print(f"✅ Limit order created: #{order.id}")
        print(f"   Limit Price: {order.limit_price}")
        
        # 3. Modify position SL/TP
        print("\n✏️  Modifying position...")
        await client.trading.modify_position(
            position.id,
            stop_loss=1.0950,  # Move SL to break-even
            take_profit=1.1200  # Extend TP
        )
        print("✅ Position modified")
        
        # 4. Wait a moment
        await asyncio.sleep(2)
        
        # 5. Close position
        print("\n🔚 Closing position...")
        await client.trading.close_position(position.id)
        print("✅ Position closed")
        
        # 6. Cancel pending order
        print("\n❌ Cancelling order...")
        await client.trading.cancel_order(order.id)
        print("✅ Order cancelled")


if __name__ == "__main__":
    asyncio.run(main())
