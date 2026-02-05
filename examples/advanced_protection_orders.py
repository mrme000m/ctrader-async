"""Example: Advanced protection fields (trailing SL, guaranteed SL, relative SL/TP).

This example demonstrates protobuf-supported advanced fields exposed by TradingAPI:

- `guaranteed_stop_loss`
- `trailing_stop_loss`
- `relative_stop_loss` / `relative_take_profit` (points)
- `stop_trigger_method`
- `position_id` targeting (useful for NETTED vs HEDGED accounts; broker-dependent)

Notes:
- Availability of Guaranteed Stop Loss and Trailing Stop depends on broker + symbol.
- Relative SL/TP units are *points* in the cTrader protocol.
- This example places a small pending order (limit) so you can inspect it without immediate fills.
"""

from __future__ import annotations

import asyncio
import time

from ctrader_async import CTraderClient, TradeSide, OrderTriggerMethod


async def main() -> None:
    async with CTraderClient.from_env(auto_enable_features=True) as client:
        info = await client.account.get_info(refresh=True)
        print("✅ Connected")
        print("account_type=", info.account_type)

        symbol = "EURUSD"

        # Fetch a quote-ish price by taking the latest tick for a moment.
        # (For real strategies, use a proper tick stream.)
        last_tick = None
        async with client.market_data.stream_ticks(symbol) as stream:
            last_tick = await asyncio.wait_for(stream.__anext__(), timeout=10.0)

        price = float(last_tick.bid)  # place a buy limit at/near bid for demo

        # If your account is NETTED, you may want to target a specific position id when modifying exposure.
        # This is broker-dependent; many workflows do NOT require positionId on new orders.
        position_id = None
        if (info.account_type or "").upper() == "NETTED":
            positions = await client.trading.get_positions()
            if positions:
                position_id = positions[0].id

        print(f"Placing limit order on {symbol} at {price}...")

        order = await client.trading.place_limit_order(
            symbol=symbol,
            side=TradeSide.BUY,
            volume=0.01,
            price=price,
            # Example: use RELATIVE SL/TP in points (protocol units).
            # These are not pips; they are points in cTrader.
            relative_stop_loss=50,
            relative_take_profit=100,
            guaranteed_stop_loss=False,  # set True only if broker/symbol supports GSL
            trailing_stop_loss=True,
            stop_trigger_method=OrderTriggerMethod.TRADE,
            # Optional position targeting
            position_id=position_id,
            comment="advanced protection demo",
        )

        print("✅ Order submitted")
        print("order_id=", getattr(order, "id", None), "client_order_id=", getattr(order, "client_order_id", None))

        # Let it sit briefly so you can view it in cTrader UI, then cancel.
        await asyncio.sleep(2.0)

        if getattr(order, "id", 0):
            try:
                await client.trading.cancel_order(int(order.id))
                print("🧹 Cancelled demo order")
            except Exception as exc:
                print("⚠️ Could not cancel demo order:", exc)


if __name__ == "__main__":
    asyncio.run(main())
