"""
Demo script that places XAUUSD orders and fetches positions, orders, and deal history.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None

if load_dotenv:
    load_dotenv()

from ctc import CTraderClient, TradeSide, TimeInForce


def _prefixed_env(key: str) -> Optional[str]:
    """Get environment variable with CTC or CTRADER prefix."""
    for prefix in ("CTC", "CTRADER"):
        value = os.environ.get(f"{prefix}_{key}")
        if value:
            return value
    return None


def _require_env(key: str) -> str:
    """Require an environment variable."""
    value = _prefixed_env(key)
    if not value:
        env_names = ", ".join(f"{prefix}_{key}" for prefix in ("CTC", "CTRADER"))
        raise SystemExit(f"Please set one of the environment variables: {env_names}.")
    return value


async def place_market_order(client: CTraderClient):
    """Place a 0.02 XAUUSD market order."""
    print("\n📈 Placing XAUUSD market order (0.02 lots)...")
    try:
        position = await client.trading.place_market_order(
            symbol="XAUUSD",
            side=TradeSide.BUY,
            volume=0.02,
            comment="Market order demo"
        )
        print(f"✅ Market order executed - Position #{position.id}")
        print(f"   Entry Price: {position.entry_price}")
        print(f"   Volume: {position.volume} lots")
        return position
    except Exception as e:
        print(f"❌ Failed to place market order: {e}")
        return None


async def place_limit_order(client: CTraderClient):
    """Place a 0.02 XAUUSD limit order with SL/TP."""
    print("\n📋 Placing XAUUSD limit order (0.02 lots)...")
    print("   Limit Price: 5188.96")
    print("   Stop Loss: 5182.19")
    print("   Take Profit: 5195.19")
    
    try:
        order = await client.trading.place_limit_order(
            symbol="XAUUSD",
            side=TradeSide.BUY,
            volume=0.02,
            price=5188.96,
            stop_loss=5182.19,
            take_profit=5195.19,
            time_in_force=TimeInForce.GOOD_TILL_CANCEL,
            comment="Limit order with SL/TP demo"
        )
        print(f"✅ Limit order created - Order #{order.id}")
        print(f"   Limit Price: {order.limit_price}")
        print(f"   Stop Loss: {order.stop_loss}")
        print(f"   Take Profit: {order.take_profit}")
        return order
    except Exception as e:
        print(f"❌ Failed to place limit order: {e}")
        return None


async def fetch_positions(client: CTraderClient):
    """Fetch and display open positions."""
    print("\n📊 Fetching open positions...")
    try:
        positions = await client.trading.get_positions()
        if not positions:
            print("   No open positions found")
            return []
        
        print(f"   Found {len(positions)} open position(s):")
        for pos in positions:
            symbol = pos.symbol_name or f"Symbol#{pos.symbol_id}"
            pnl = pos.pnl_net_unrealized
            print(f"   - Position #{pos.id}: {symbol} {pos.volume} lots @ {pos.entry_price}")
            print(f"     PnL: {pnl} | SL: {pos.stop_loss} | TP: {pos.take_profit}")
        return positions
    except Exception as e:
        print(f"❌ Failed to fetch positions: {e}")
        return []


async def fetch_orders(client: CTraderClient):
    """Fetch and display orders."""
    print("\n📋 Fetching orders...")
    try:
        orders = await client.trading.get_orders()
        if not orders:
            print("   No orders found")
            return []
        
        print(f"   Found {len(orders)} order(s):")
        for order in orders:
            order_type = "LIMIT" if hasattr(order, 'limit_price') else "STOP" if hasattr(order, 'stop_price') else "UNKNOWN"
            price = getattr(order, 'limit_price', None) or getattr(order, 'stop_price', None)
            symbol = order.symbol_name or f"Symbol#{order.symbol_id}"
            status = order.status or order.order_status or "Unknown"
            print(f"   - Order #{order.id}: {symbol} {order.volume} lots {order.side} {order_type}")
            print(f"     Price: {price} | Status: {status}")
        return orders
    except Exception as e:
        print(f"❌ Failed to fetch orders: {e}")
        return []


async def fetch_deal_history(client: CTraderClient, days: int = 7):
    """Fetch and display deal history."""
    print(f"\n📈 Fetching deal history (last {days} days)...")
    try:
        from datetime import datetime, timedelta, timezone
        to_timestamp = datetime.now(timezone.utc)
        from_timestamp = to_timestamp - timedelta(days=days)
        
        deals = await client.history.get_deals(
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp
        )
        
        if not deals:
            print("   No deals found in the specified period")
            return []
        
        print(f"   Found {len(deals)} deal(s):")
        for deal in deals[:10]:  # Show only first 10 deals
            deal_id = getattr(deal, 'deal_id', getattr(deal, 'id', 'Unknown'))
            symbol = deal.symbol_name or f"Symbol#{deal.symbol_id}" if deal.symbol_id else "Unknown"
            print(f"   - Deal #{deal_id}: {symbol} {deal.volume} lots {deal.side} @ {deal.execution_price}")
            print(f"     Time: {deal.datetime} | PnL: {deal.pnl}")
        
        if len(deals) > 10:
            print(f"   ... and {len(deals) - 10} more deals")
        return deals
    except Exception as e:
        print(f"❌ Failed to fetch deal history: {e}")
        return []


async def main():
    """Main function to run the demo."""
    # Get credentials from environment
    client_id = _require_env("CLIENT_ID")
    client_secret = _require_env("CLIENT_SECRET")
    access_token = _require_env("ACCESS_TOKEN")
    account_id_str = _require_env("ACCOUNT_ID")
    
    try:
        account_id = int(account_id_str)
    except ValueError:
        raise SystemExit("CTC_ACCOUNT_ID must be an integer")
    
    host_type = _prefixed_env("HOST_TYPE") or "demo"
    
    print("🚀 Starting XAUUSD Trading Demo")
    print(f"   Account ID: {account_id}")
    print(f"   Host Type: {host_type}")
    
    async with CTraderClient(
        client_id=client_id,
        client_secret=client_secret,
        access_token=access_token,
        account_id=account_id,
        host_type=host_type,
    ) as client:
        print("✅ Connected to cTrader")
        
        # 1. Fetch current state before placing orders
        print("\n" + "="*50)
        print("CURRENT STATE BEFORE PLACING ORDERS")
        print("="*50)
        await fetch_positions(client)
        await fetch_orders(client)
        await fetch_deal_history(client, days=7)
        
        # 2. Place orders
        print("\n" + "="*50)
        print("PLACING NEW ORDERS")
        print("="*50)
        market_position = await place_market_order(client)
        limit_order = await place_limit_order(client)
        
        # 3. Wait a moment for orders to process
        print("\n⏳ Waiting 3 seconds for orders to process...")
        await asyncio.sleep(3)
        
        # 4. Fetch updated state
        print("\n" + "="*50)
        print("UPDATED STATE AFTER PLACING ORDERS")
        print("="*50)
        await fetch_positions(client)
        await fetch_orders(client)
        
        # 5. Clean up - close position and cancel order
        print("\n" + "="*50)
        print("CLEANING UP")
        print("="*50)
        
        if market_position:
            print(f"\n🔚 Closing position #{market_position.id}...")
            try:
                await client.trading.close_position(market_position.id)
                print("✅ Position closed")
            except Exception as e:
                print(f"❌ Failed to close position: {e}")
        
        if limit_order:
            print(f"\n❌ Cancelling limit order #{limit_order.id}...")
            try:
                await client.trading.cancel_order(limit_order.id)
                print("✅ Order cancelled")
            except Exception as e:
                print(f"❌ Failed to cancel order: {e}")
        
        # 6. Final state check
        print("\n" + "="*50)
        print("FINAL STATE")
        print("="*50)
        await fetch_positions(client)
        await fetch_orders(client)
        
        print("\n🎉 Demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())