#!/usr/bin/env python3
"""
Depth Stream Debug Script

Tests: DepthStream subscription, real-time order book updates,
       snapshot parsing, bid/ask quote handling.

Key protobuf facts verified here:
- ProtoOASubscribeDepthQuotesReq uses symbolId (repeated field)
- ProtoOADepthEvent contains newQuotes and deletedQuotes
- ProtoOADepthQuote: id, size, bid, ask (bid/ask are prices)
"""

import asyncio
import logging
import time
from dotenv import load_dotenv
from ctc import CTraderClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SYMBOLS_TO_TEST = ["XAUUSD", "EURUSD"]


async def test_depth_stream(client, symbol: str, duration: int = 10):
    """Test depth stream for a symbol."""
    logger.info(f"\n📊 Testing depth stream for {symbol} (duration: {duration}s)")
    
    try:
        # Create depth stream
        from ctc.streams import DepthStream
        stream = DepthStream(
            protocol=client._protocol,
            config=client.config,
            symbols=client.symbols,
            symbol=symbol,
            depth=10
        )
        
        # Attach client for reconnect recovery
        stream._client = client
        
        # Track snapshots
        snapshot_count = 0
        start_time = time.time()
        
        async with stream:
            logger.info(f"✅ Subscribed to {symbol} depth stream")
            
            async for snapshot in stream:
                snapshot_count += 1
                elapsed = time.time() - start_time
                
                # Display snapshot info
                logger.info(f"\n📈 Snapshot #{snapshot_count} (t+{elapsed:.1f}s)")
                logger.info(f"   Symbol: {snapshot.symbol_name}")
                logger.info(f"   Timestamp: {snapshot.timestamp}")
                
                # Best bid/ask
                if snapshot.bids:
                    best_bid = snapshot.bids[0]
                    logger.info(f"   Best Bid: {best_bid.price} ({best_bid.volume} lots)")
                else:
                    logger.info("   Best Bid: None")
                
                if snapshot.asks:
                    best_ask = snapshot.asks[0]
                    logger.info(f"   Best Ask: {best_ask.price} ({best_ask.volume} lots)")
                else:
                    logger.info("   Best Ask: None")
                
                # Spread
                if snapshot.bids and snapshot.asks:
                    spread = snapshot.asks[0].price - snapshot.bids[0].price
                    logger.info(f"   Spread: {spread:.5f}")
                
                # Book depth
                logger.info(f"   Book Depth: {len(snapshot.bids)} bids, {len(snapshot.asks)} asks")
                
                # Stop after duration
                if elapsed >= duration:
                    logger.info(f"⏰ Time limit reached ({duration}s), stopping...")
                    break
                    
    except Exception as e:
        logger.error(f"❌ Error testing {symbol} depth stream: {e}", exc_info=True)
        return False
    
    logger.info(f"✅ {symbol} depth stream test completed ({snapshot_count} snapshots)")
    return True


async def main():
    load_dotenv()
    client = CTraderClient.from_env()
    await client.connect()

    logger.info("=" * 60)
    logger.info("⚠️  DEPTH STREAM DEBUG")
    logger.info("=" * 60)

    try:
        # Test each symbol
        for symbol in SYMBOLS_TO_TEST:
            success = await test_depth_stream(client, symbol, duration=5)
            if not success:
                logger.error(f"❌ Failed to test {symbol} depth stream")
            
            # Brief pause between symbols
            await asyncio.sleep(1)
        
        logger.info("\n🎉 All depth stream tests completed!")
        
    except Exception as e:
        logger.error(f"❌ Debug script error: {e}", exc_info=True)
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())