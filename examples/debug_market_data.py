#!/usr/bin/env python3
"""
Debug script for ticker subscriptions and orderbook snapshots.

This script helps test and debug market data streaming functionality,
including real-time tick data and order book depth snapshots.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")

# Add the src directory to the path so we can import the client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ctc import CTraderClient, TradeSide
from ctc.models import Tick, DepthSnapshot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Symbol to debug (change as needed)
DEBUG_SYMBOL = "EURUSD"


async def debug_tick_subscription():
    """Debug tick subscription for a symbol."""
    print(f"\n=== Debugging Tick Subscription for {DEBUG_SYMBOL} ===\n")
    
    try:
        async with CTraderClient.from_env() as client:
            print(f"✓ Connected to cTrader")
            
            # Get symbol info first
            symbol_info = await client.symbols.get_symbol(DEBUG_SYMBOL)
            if not symbol_info:
                print(f"✗ Symbol {DEBUG_SYMBOL} not found")
                return
                
            print(f"✓ Symbol found: {symbol_info.name}")
            print(f"  - Digits: {symbol_info.digits}")
            print(f"  - Pip size: {symbol_info.pip_size}")
            print(f"  - Lot size: {symbol_info.lot_size_units}")
            
            # Subscribe to ticks using async context manager
            print(f"\n📡 Subscribing to tick stream...")
            tick_count = 0
            max_ticks = 10  # Limit for debugging
            
            try:
                async with client.market_data.stream_ticks(DEBUG_SYMBOL) as stream:
                    async for tick in stream:
                        tick_count += 1
                        
                        print(f"📈 Tick #{tick_count}:")
                        print(f"  - Time: {tick.timestamp}")
                        print(f"  - Bid: {tick.bid}")
                        print(f"  - Ask: {tick.ask}")
                        spread = tick.spread if tick.spread is not None else (tick.ask - tick.bid)
                        print(f"  - Spread: {spread:.{symbol_info.digits}f}")
                        
                        if tick_count >= max_ticks:
                            print(f"\n✅ Debug tick limit reached")
                            break
                            
            except asyncio.TimeoutError:
                print(f"\n⏰ Timeout waiting for ticks")
            except Exception as e:
                print(f"\n✗ Error in tick streaming: {e}")
                
            print(f"📡 Unsubscribed from tick stream")
                
    except Exception as e:
        print(f"✗ Error in tick subscription: {e}")
        logger.exception("Tick subscription error")


async def debug_orderbook_snapshot():
    """Debug orderbook snapshot for a symbol."""
    print(f"\n=== Debugging Orderbook Snapshot for {DEBUG_SYMBOL} ===\n")
    
    try:
        async with CTraderClient.from_env() as client:
            print(f"✓ Connected to cTrader")
            
            # Get symbol info first
            symbol_info = await client.symbols.get_symbol(DEBUG_SYMBOL)
            if not symbol_info:
                print(f"✗ Symbol {DEBUG_SYMBOL} not found")
                return
                
            print(f"✓ Symbol found: {symbol_info.name}")
            
            # Get orderbook snapshot using stream_depth
            print(f"\n📊 Getting orderbook snapshot...")
            try:
                async with client.market_data.stream_depth(DEBUG_SYMBOL, depth=10) as stream:
                    snapshot_count = 0
                    async for snapshot in stream:
                        snapshot_count += 1
                        print(f"✅ Orderbook snapshot #{snapshot_count}:")
                        print(f"  - Time: {snapshot.datetime}")
                        print(f"  - Bid levels: {len(snapshot.bids)}")
                        print(f"  - Ask levels: {len(snapshot.asks)}")
                        
                        # Show top 5 levels
                        print(f"\n📊 Top 5 Bid Levels:")
                        for i, bid in enumerate(snapshot.bids[:5]):
                            print(f"  {i+1}. Price: {bid.price:.{symbol_info.digits}f}, Volume: {bid.volume}")
                        
                        print(f"\n📊 Top 5 Ask Levels:")
                        for i, ask in enumerate(snapshot.asks[:5]):
                            print(f"  {i+1}. Price: {ask.price:.{symbol_info.digits}f}, Volume: {ask.volume}")
                        
                        # Calculate spread
                        if snapshot.bids and snapshot.asks:
                            best_bid = snapshot.bids[0].price
                            best_ask = snapshot.asks[0].price
                            spread = best_ask - best_bid
                            print(f"\n📊 Best Spread: {spread:.{symbol_info.digits}f}")
                            
                        # Show total volumes
                        total_bid_volume = snapshot.total_bid_volume(levels=10)
                        total_ask_volume = snapshot.total_ask_volume(levels=10)
                        print(f"\n📊 Total Volume (top 10 levels):")
                        print(f"  - Bid: {total_bid_volume}")
                        print(f"  - Ask: {total_ask_volume}")
                        
                        # Only get one snapshot for debugging
                        if snapshot_count >= 1:
                            break
                            
            except Exception as e:
                print(f"✗ Error getting orderbook snapshot: {e}")
                return
            
    except Exception as e:
        print(f"✗ Error getting orderbook snapshot: {e}")
        logger.exception("Orderbook snapshot error")


async def debug_orderbook_streaming():
    """Debug orderbook streaming for a symbol."""
    print(f"\n=== Debugging Orderbook Streaming for {DEBUG_SYMBOL} ===\n")
    
    try:
        async with CTraderClient.from_env() as client:
            print(f"✓ Connected to cTrader")
            
            # Get symbol info first
            symbol_info = await client.symbols.get_symbol(DEBUG_SYMBOL)
            if not symbol_info:
                print(f"✗ Symbol {DEBUG_SYMBOL} not found")
                return
                
            print(f"✓ Symbol found: {symbol_info.name}")
            
            # Subscribe to orderbook updates using async context manager
            print(f"\n📡 Subscribing to orderbook stream...")
            update_count = 0
            max_updates = 5  # Limit for debugging
            
            try:
                async with client.market_data.stream_depth(DEBUG_SYMBOL, depth=10) as stream:
                    async for snapshot in stream:
                        update_count += 1
                        
                        print(f"📊 Orderbook Update #{update_count}:")
                        print(f"  - Time: {snapshot.datetime}")
                        print(f"  - Bid levels: {len(snapshot.bids)}, Ask levels: {len(snapshot.asks)}")
                        
                        if snapshot.bids and snapshot.asks:
                            best_bid = snapshot.bids[0].price
                            best_ask = snapshot.asks[0].price
                            spread = best_ask - best_bid
                            print(f"  - Best Bid: {best_bid:.{symbol_info.digits}f}")
                            print(f"  - Best Ask: {best_ask:.{symbol_info.digits}f}")
                            print(f"  - Spread: {spread:.{symbol_info.digits}f}")
                        
                        if update_count >= max_updates:
                            print(f"\n✅ Debug orderbook limit reached")
                            break
                            
            except asyncio.TimeoutError:
                print(f"\n⏰ Timeout waiting for orderbook updates")
            except Exception as e:
                print(f"\n✗ Error in orderbook streaming: {e}")
                
            print(f"📡 Unsubscribed from orderbook stream")
                
    except Exception as e:
        print(f"✗ Error in orderbook streaming: {e}")
        logger.exception("Orderbook streaming error")


async def debug_multi_symbol_ticks():
    """Debug tick subscription for multiple symbols."""
    symbols = ["EURUSD", "GBPUSD", "USDJPY"]
    print(f"\n=== Debugging Multi-Symbol Tick Subscription ===\n")
    
    try:
        async with CTraderClient.from_env() as client:
            print(f"✓ Connected to cTrader")
            
            # Check which symbols are available
            available_symbols = []
            for symbol in symbols:
                symbol_info = await client.symbols.get_symbol(symbol)
                if symbol_info:
                    available_symbols.append(symbol)
                    print(f"✓ {symbol} available")
                else:
                    print(f"✗ {symbol} not available")
            
            if not available_symbols:
                print("No symbols available for debugging")
                return
                
            # Subscribe to multiple symbols
            print(f"\n📡 Subscribing to {len(available_symbols)} symbols...")
            tick_counts = {symbol: 0 for symbol in available_symbols}
            max_ticks_per_symbol = 3
            
            async def on_tick(symbol: str, tick: Tick):
                tick_counts[symbol] += 1
                
                print(f"📈 {symbol} Tick #{tick_counts[symbol]}:")
                print(f"  - Time: {tick.timestamp}")
                print(f"  - Bid: {tick.bid}, Ask: {tick.ask}")
                print(f"  - Spread: {tick.ask - tick.bid}")
                
                # Check if we've received enough ticks for all symbols
                if all(count >= max_ticks_per_symbol for count in tick_counts.values()):
                    raise StopAsyncIteration("Debug multi-symbol limit reached")
            
            # Start the subscription using async context manager
            async with client.market_data.stream_ticks_multi(available_symbols) as stream:
                try:
                    # Wait for ticks or timeout
                    await asyncio.wait_for(
                        _process_multi_symbol_ticks(stream, available_symbols, tick_counts, max_ticks_per_symbol),
                        timeout=30
                    )
                except asyncio.TimeoutError:
                    print(f"\n⏰ Timeout waiting for ticks")
                except StopAsyncIteration as e:
                    print(f"\n✅ {e}")
                    
            print(f"📡 Unsubscribed from multi-symbol tick stream")
                
            # Show summary
            print(f"\n📊 Tick Summary:")
            for symbol, count in tick_counts.items():
                print(f"  - {symbol}: {count} ticks")
                
    except Exception as e:
        print(f"✗ Error in multi-symbol tick subscription: {e}")
        logger.exception("Multi-symbol tick subscription error")


async def _process_multi_symbol_ticks(stream, available_symbols, tick_counts, max_ticks_per_symbol):
    """Process multi-symbol tick stream."""
    async for tick in stream:
        symbol = tick.symbol_name
        if symbol in tick_counts:
            tick_counts[symbol] += 1
            
            print(f"📈 {symbol} Tick #{tick_counts[symbol]}:")
            print(f"  - Time: {tick.timestamp}")
            print(f"  - Bid: {tick.bid}, Ask: {tick.ask}")
            spread = tick.spread if tick.spread is not None else (tick.ask - tick.bid)
            print(f"  - Spread: {spread}")
            
            # Check if we've received enough ticks for all symbols
            if all(count >= max_ticks_per_symbol for count in tick_counts.values()):
                raise StopAsyncIteration("Debug multi-symbol limit reached")


async def main():
    """Main debug function."""
    print("🐛 cTrader Market Data Debug Script")
    print("=" * 50)
    
    # Check environment variables
    required_vars = ["CTRADER_CLIENT_ID", "CTRADER_CLIENT_SECRET", "CTRADER_ACCOUNT_ID"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"✗ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set the required environment variables and try again.")
        return
    
    print("✓ Environment variables configured")
    
    # Run debug functions
    try:
        await debug_tick_subscription()
        await debug_orderbook_snapshot()
        await debug_orderbook_streaming()
        await debug_multi_symbol_ticks()
        
        print(f"\n✅ All debug tests completed successfully!")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Debug script interrupted by user")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        logger.exception("Main debug error")


if __name__ == "__main__":
    asyncio.run(main())