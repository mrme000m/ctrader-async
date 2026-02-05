"""
Example: Streaming real-time tick data.
"""

import asyncio
from ctrader_async import CTraderClient


async def main():
    """Stream real-time tick data."""
    
    async with CTraderClient.from_env() as client:
        
        print("✅ Connected")
        print("\n📊 Streaming EURUSD ticks (press Ctrl+C to stop)...\n")
        
        # Stream ticks using async iterator
        async with client.market_data.stream_ticks("EURUSD") as stream:
            tick_count = 0
            
            async for tick in stream:
                tick_count += 1
                
                # Calculate spread in pips
                symbol = await client.symbols.get_symbol("EURUSD")
                spread_pips = (tick.ask - tick.bid) / symbol.pip_size if symbol else 0
                
                # Print tick data
                print(f"Tick #{tick_count:4d}: "
                      f"Bid={tick.bid:.5f} | "
                      f"Ask={tick.ask:.5f} | "
                      f"Mid={tick.mid_price:.5f} | "
                      f"Spread={spread_pips:.1f} pips")
                
                # Exit after 100 ticks for demo
                if tick_count >= 100:
                    print("\n✅ Received 100 ticks, stopping...")
                    break


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Stopped by user")
