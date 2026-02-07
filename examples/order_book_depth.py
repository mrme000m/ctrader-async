"""
Example: Order Book Depth Streaming

This example demonstrates how to stream real-time Level II market data
(order book depth) using the CTraderClient.

Level II data shows bid and ask prices at multiple price levels with
their respective volumes, allowing you to see market depth and liquidity.

Use cases:
- Market microstructure analysis
- Liquidity analysis
- Order book imbalance strategies
- VWAP/TWAP execution algorithms
- Institutional trading strategies
"""

import asyncio
import logging
from ctc import CTraderClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def main():
    """Stream order book depth for a symbol."""
    
    # Initialize client
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,  # Your account ID
        host_type="demo"
    )
    
    async with client:
        print("Connected to cTrader")
        
        # Stream depth for EURUSD with 10 price levels
        symbol = "EURUSD"
        depth_levels = 10
        
        print(f"\nStreaming order book depth for {symbol} ({depth_levels} levels)...")
        print("Press Ctrl+C to stop\n")
        
        try:
            async with client.market_data.stream_depth(symbol, depth=depth_levels) as stream:
                async for snapshot in stream:
                    print(f"\n{'='*60}")
                    print(f"Order Book Snapshot - {symbol} at {snapshot.datetime}")
                    print(f"{'='*60}")
                    
                    # Display best bid and ask
                    if snapshot.best_bid and snapshot.best_ask:
                        print(f"\nBest Bid: {snapshot.best_bid.price:.5f} ({snapshot.best_bid.volume:.2f} lots)")
                        print(f"Best Ask: {snapshot.best_ask.price:.5f} ({snapshot.best_ask.volume:.2f} lots)")
                        print(f"Spread:   {snapshot.spread:.5f}")
                    
                    # Display bid side (buy orders)
                    print(f"\n{'BIDS (Buy Orders)':-^60}")
                    print(f"{'Price':>12} | {'Volume (lots)':>15} | {'Quote ID':>10}")
                    print("-" * 60)
                    for bid in snapshot.bids[:5]:  # Top 5 bids
                        print(f"{bid.price:>12.5f} | {bid.volume:>15.2f} | {bid.id:>10}")
                    
                    # Display ask side (sell orders)
                    print(f"\n{'ASKS (Sell Orders)':-^60}")
                    print(f"{'Price':>12} | {'Volume (lots)':>15} | {'Quote ID':>10}")
                    print("-" * 60)
                    for ask in snapshot.asks[:5]:  # Top 5 asks
                        print(f"{ask.price:>12.5f} | {ask.volume:>15.2f} | {ask.id:>10}")
                    
                    # Calculate and display volume analytics
                    print(f"\n{'Volume Analytics':-^60}")
                    bid_vol_3 = snapshot.total_bid_volume(3)
                    ask_vol_3 = snapshot.total_ask_volume(3)
                    bid_vol_all = snapshot.total_bid_volume()
                    ask_vol_all = snapshot.total_ask_volume()
                    
                    print(f"Total Bid Volume (Top 3): {bid_vol_3:.2f} lots")
                    print(f"Total Ask Volume (Top 3): {ask_vol_3:.2f} lots")
                    print(f"Total Bid Volume (All):   {bid_vol_all:.2f} lots")
                    print(f"Total Ask Volume (All):   {ask_vol_all:.2f} lots")
                    
                    # Order book imbalance
                    if bid_vol_3 + ask_vol_3 > 0:
                        imbalance = (bid_vol_3 - ask_vol_3) / (bid_vol_3 + ask_vol_3)
                        print(f"Order Book Imbalance (Top 3): {imbalance:+.2%}")
                        
                        if imbalance > 0.2:
                            print("  → More buying pressure (bullish)")
                        elif imbalance < -0.2:
                            print("  → More selling pressure (bearish)")
                        else:
                            print("  → Balanced order book")
                    
                    # Add a small delay to make output readable
                    await asyncio.sleep(0.5)
                    
        except KeyboardInterrupt:
            print("\n\nStopping depth stream...")
        except Exception as e:
            print(f"\nError: {e}")
            raise


async def analyze_order_book_example():
    """Example: Analyze order book for trading signals."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"
    )
    
    async with client:
        symbol = "EURUSD"
        
        print(f"Analyzing order book for {symbol}...")
        
        async with client.market_data.stream_depth(symbol, depth=20) as stream:
            async for snapshot in stream:
                # Calculate order book metrics
                bid_vol = snapshot.total_bid_volume(5)
                ask_vol = snapshot.total_ask_volume(5)
                
                if bid_vol + ask_vol == 0:
                    continue
                
                # Order book imbalance ratio
                imbalance = (bid_vol - ask_vol) / (bid_vol + ask_vol)
                
                # Spread analysis
                spread = snapshot.spread
                
                # Simple trading signal
                if imbalance > 0.3 and spread and spread < 0.0002:
                    print(f"🟢 BULLISH SIGNAL: Strong bid support, imbalance: {imbalance:+.2%}")
                elif imbalance < -0.3 and spread and spread < 0.0002:
                    print(f"🔴 BEARISH SIGNAL: Strong ask resistance, imbalance: {imbalance:+.2%}")
                
                # Wide spread warning
                if spread and spread > 0.0005:
                    print(f"⚠️  Wide spread detected: {spread:.5f}")
                
                await asyncio.sleep(1)


async def multi_symbol_depth_example():
    """Example: Monitor depth for multiple symbols."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"
    )
    
    async with client:
        symbols = ["EURUSD", "GBPUSD", "USDJPY"]
        
        # Create depth streams for each symbol
        async def monitor_symbol(symbol: str):
            async with client.market_data.stream_depth(symbol, depth=10) as stream:
                async for snapshot in stream:
                    spread = snapshot.spread
                    bid_vol = snapshot.total_bid_volume(3)
                    ask_vol = snapshot.total_ask_volume(3)
                    
                    print(f"{symbol}: Spread={spread:.5f}, "
                          f"Bid Vol={bid_vol:.2f}, Ask Vol={ask_vol:.2f}")
                    
                    await asyncio.sleep(2)
        
        # Run all monitors concurrently
        tasks = [monitor_symbol(s) for s in symbols]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    # Run the main example
    asyncio.run(main())
    
    # Uncomment to run other examples:
    # asyncio.run(analyze_order_book_example())
    # asyncio.run(multi_symbol_depth_example())
