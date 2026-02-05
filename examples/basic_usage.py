"""
Basic usage example for cTrader async client.
"""

import asyncio
from ctrader_async import CTraderClient, TradeSide


async def main():
    """Basic usage example."""
    
    # Initialize client with credentials
    async with CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,  # Your account ID
        host_type="demo"  # or "live"
    ) as client:
        
        print("✅ Connected and authenticated")
        
        # Get account information
        account = await client.account.get_info()
        print(f"\n💰 Account Info:")
        print(f"   Balance: ${account.balance:,.2f}")
        print(f"   Equity: ${account.equity:,.2f}")
        print(f"   Margin: ${account.margin:,.2f}")
        print(f"   Free Margin: ${account.free_margin:,.2f}")
        
        # Get all symbols
        symbols = await client.symbols.get_all()
        print(f"\n📊 Available Symbols: {len(symbols)}")
        
        # Search for specific symbol
        eurusd = await client.symbols.get_symbol("EURUSD")
        if eurusd:
            print(f"\n💱 EURUSD Info:")
            print(f"   Digits: {eurusd.digits}")
            print(f"   Pip Size: {eurusd.pip_size}")
            print(f"   Lot Size: {eurusd.lot_size_units}")
        
        # Get open positions
        positions = await client.trading.get_positions()
        print(f"\n📈 Open Positions: {len(positions)}")
        for pos in positions:
            print(f"   {pos.symbol_name}: {pos.volume} lots, "
                  f"Side: {pos.side}, PnL: ${pos.pnl_net_unrealized:,.2f}")
        
        # Get pending orders
        orders = await client.trading.get_orders()
        print(f"\n📋 Pending Orders: {len(orders)}")
        for order in orders:
            print(f"   {order.symbol_name}: {order.volume} lots, "
                  f"Type: {order.order_type}, Price: {order.limit_price or order.stop_price}")


if __name__ == "__main__":
    asyncio.run(main())
