"""
Example: Fetching historical candlestick data.
"""

import asyncio
from ctc import CTraderClient, TimeFrame


async def main():
    """Fetch and display historical data."""
    
    async with CTraderClient.from_env() as client:
        
        print("✅ Connected")
        
        # Fetch 1-hour candles
        print("\n📊 Fetching EURUSD H1 candles...")
        candles = await client.market_data.get_candles(
            symbol="EURUSD",
            timeframe=TimeFrame.H1,
            count=10  # Last 10 candles
        )
        
        print(f"\n✅ Received {len(candles)} candles:\n")
        print("Timestamp            | Open     | High     | Low      | Close    | Volume")
        print("-" * 80)
        
        for candle in candles:
            print(f"{candle.timestamp.strftime('%Y-%m-%d %H:%M')} | "
                  f"{candle.open:.5f} | "
                  f"{candle.high:.5f} | "
                  f"{candle.low:.5f} | "
                  f"{candle.close:.5f} | "
                  f"{candle.volume:7d}")
        
        # Calculate some statistics
        if candles:
            avg_range = sum(c.range for c in candles) / len(candles)
            bullish = sum(1 for c in candles if c.is_bullish)
            bearish = sum(1 for c in candles if c.is_bearish)
            
            print(f"\n📈 Statistics:")
            print(f"   Average Range: {avg_range:.5f}")
            print(f"   Bullish Candles: {bullish}")
            print(f"   Bearish Candles: {bearish}")


if __name__ == "__main__":
    asyncio.run(main())
