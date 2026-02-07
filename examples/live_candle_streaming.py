"""
Example: Live Candle Streaming

This example demonstrates how to stream real-time candlestick data
as candles form using the CTraderClient.

Use cases:
- Real-time charting applications
- Indicator-based trading strategies
- Multi-timeframe analysis
- Candle pattern detection
- Price action trading
"""

import asyncio
import logging
from ctc import CTraderClient
from ctc.enums import TimeFrame

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def basic_candle_streaming():
    """Example: Basic live candle streaming."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"
    )
    
    async with client:
        print("=== Live Candle Streaming ===\n")
        print("Streaming 5-minute candles for EURUSD...")
        print("Press Ctrl+C to stop\n")
        
        try:
            async with client.market_data.stream_candles("EURUSD", TimeFrame.M5) as stream:
                async for candle in stream:
                    # Display candle data
                    timestamp = candle.datetime.strftime("%Y-%m-%d %H:%M") if candle.datetime else "N/A"
                    
                    print(f"\n{'='*60}")
                    print(f"Candle Update - {timestamp}")
                    print(f"{'='*60}")
                    print(f"Open:   {candle.open:.5f}")
                    print(f"High:   {candle.high:.5f}")
                    print(f"Low:    {candle.low:.5f}")
                    print(f"Close:  {candle.close:.5f}")
                    print(f"Volume: {candle.volume}")
                    
                    # Candle type
                    if candle.close > candle.open:
                        candle_type = "🟢 BULLISH"
                        body_size = candle.close - candle.open
                    elif candle.close < candle.open:
                        candle_type = "🔴 BEARISH"
                        body_size = candle.open - candle.close
                    else:
                        candle_type = "⚪ DOJI"
                        body_size = 0
                    
                    print(f"\nType:       {candle_type}")
                    print(f"Body Size:  {body_size:.5f}")
                    
                    # Candle range
                    candle_range = candle.high - candle.low
                    print(f"Range:      {candle.range:.5f}")
                    
        except KeyboardInterrupt:
            print("\n\nStopping candle stream...")


async def multi_timeframe_analysis():
    """Example: Monitor multiple timeframes simultaneously."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"
    )
    
    async with client:
        print("=== Multi-Timeframe Analysis ===\n")
        
        symbol = "EURUSD"
        timeframes = [TimeFrame.M1, TimeFrame.M5, TimeFrame.M15]
        
        async def monitor_timeframe(tf: TimeFrame):
            """Monitor a specific timeframe."""
            async with client.market_data.stream_candles(symbol, tf) as stream:
                async for candle in stream:
                    timestamp = candle.datetime.strftime("%H:%M") if candle.datetime else "N/A"
                    direction = "🟢" if candle.close > candle.open else "🔴" if candle.close < candle.open else "⚪"
                    
                    print(f"[{tf.name}] {timestamp}: {direction} O={candle.open:.5f} "
                          f"H={candle.high:.5f} L={candle.low:.5f} C={candle.close:.5f}")
        
        # Run all timeframes concurrently
        tasks = [monitor_timeframe(tf) for tf in timeframes]
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            print("\nStopping multi-timeframe monitoring...")


async def candle_pattern_detection():
    """Example: Detect basic candle patterns."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"
    )
    
    async with client:
        print("=== Candle Pattern Detection ===\n")
        print("Monitoring for patterns on EURUSD 15-minute candles...\n")
        
        # Store last few candles for pattern detection
        candle_buffer = []
        buffer_size = 3
        
        async with client.market_data.stream_candles("EURUSD", TimeFrame.M15) as stream:
            async for candle in stream:
                # Add to buffer
                candle_buffer.append(candle)
                if len(candle_buffer) > buffer_size:
                    candle_buffer.pop(0)
                
                # Skip if buffer not full
                if len(candle_buffer) < 2:
                    continue
                
                current = candle_buffer[-1]
                previous = candle_buffer[-2]
                
                timestamp = current.datetime.strftime("%H:%M") if current.datetime else "N/A"
                
                # Detect patterns
                patterns = []
                
                # Doji pattern (small body)
                body_size = abs(current.close - current.open)
                candle_range = current.high - current.low
                if candle_range > 0 and (body_size / candle_range) < 0.1:
                    patterns.append("DOJI - Potential reversal or indecision")
                
                # Hammer pattern (long lower wick, small body at top)
                lower_wick = min(current.open, current.close) - current.low
                upper_wick = current.high - max(current.open, current.close)
                if candle_range > 0:
                    if (lower_wick / candle_range) > 0.6 and (body_size / candle_range) < 0.3:
                        patterns.append("HAMMER - Potential bullish reversal")
                    
                    # Shooting star (long upper wick, small body at bottom)
                    if (upper_wick / candle_range) > 0.6 and (body_size / candle_range) < 0.3:
                        patterns.append("SHOOTING STAR - Potential bearish reversal")
                
                # Engulfing pattern
                if len(candle_buffer) >= 2:
                    # Bullish engulfing
                    if (previous.close < previous.open and  # Previous bearish
                        current.close > current.open and     # Current bullish
                        current.open < previous.close and    # Opens below previous close
                        current.close > previous.open):      # Closes above previous open
                        patterns.append("BULLISH ENGULFING - Strong buy signal")
                    
                    # Bearish engulfing
                    if (previous.close > previous.open and  # Previous bullish
                        current.close < current.open and     # Current bearish
                        current.open > previous.close and    # Opens above previous close
                        current.close < previous.open):      # Closes below previous open
                        patterns.append("BEARISH ENGULFING - Strong sell signal")
                
                # Display patterns
                if patterns:
                    print(f"\n{'='*60}")
                    print(f"⚠️  PATTERNS DETECTED at {timestamp}")
                    print(f"{'='*60}")
                    for pattern in patterns:
                        print(f"  • {pattern}")
                    print(f"Current: O={current.open:.5f} H={current.high:.5f} "
                          f"L={current.low:.5f} C={current.close:.5f}")
                else:
                    # Just log the candle
                    direction = "🟢" if current.close > current.open else "🔴"
                    print(f"[{timestamp}] {direction} O={current.open:.5f} H={current.high:.5f} "
                          f"L={current.low:.5f} C={current.close:.5f}")


async def indicator_based_strategy():
    """Example: Simple moving average crossover using live candles."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"
    )
    
    async with client:
        print("=== SMA Crossover Strategy ===\n")
        print("Monitoring EURUSD with 5-period and 20-period SMAs...\n")
        
        # Store candle closes for SMA calculation
        closes = []
        fast_period = 5
        slow_period = 20
        
        async with client.market_data.stream_candles("EURUSD", TimeFrame.M5) as stream:
            async for candle in stream:
                # Add close price to buffer
                closes.append(candle.close)
                
                # Keep only what we need
                if len(closes) > slow_period:
                    closes.pop(0)
                
                # Calculate SMAs
                if len(closes) >= slow_period:
                    sma_fast = sum(closes[-fast_period:]) / fast_period
                    sma_slow = sum(closes[-slow_period:]) / slow_period
                    
                    timestamp = candle.datetime.strftime("%H:%M") if candle.datetime else "N/A"
                    
                    print(f"[{timestamp}] Close={candle.close:.5f} | "
                          f"SMA({fast_period})={sma_fast:.5f} | "
                          f"SMA({slow_period})={sma_slow:.5f}")
                    
                    # Detect crossovers
                    if len(closes) >= slow_period + 1:
                        prev_sma_fast = sum(closes[-fast_period-1:-1]) / fast_period
                        prev_sma_slow = sum(closes[-slow_period-1:-1]) / slow_period
                        
                        # Bullish crossover
                        if prev_sma_fast <= prev_sma_slow and sma_fast > sma_slow:
                            print(f"\n🟢 BULLISH CROSSOVER DETECTED!")
                            print(f"   Fast SMA crossed above Slow SMA")
                            print(f"   Consider BUY signal\n")
                        
                        # Bearish crossover
                        elif prev_sma_fast >= prev_sma_slow and sma_fast < sma_slow:
                            print(f"\n🔴 BEARISH CROSSOVER DETECTED!")
                            print(f"   Fast SMA crossed below Slow SMA")
                            print(f"   Consider SELL signal\n")


async def multi_symbol_candles():
    """Example: Monitor candles for multiple symbols."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"
    )
    
    async with client:
        print("=== Multi-Symbol Candle Monitoring ===\n")
        
        symbols = ["EURUSD", "GBPUSD", "USDJPY"]
        timeframe = TimeFrame.M5
        
        async def monitor_symbol(symbol: str):
            """Monitor candles for a symbol."""
            async with client.market_data.stream_candles(symbol, timeframe) as stream:
                async for candle in stream:
                    timestamp = candle.datetime.strftime("%H:%M") if candle.datetime else "N/A"
                    direction = "🟢" if candle.close > candle.open else "🔴" if candle.close < candle.open else "⚪"
                    
                    print(f"[{symbol}] {timestamp}: {direction} "
                          f"O={candle.open:.5f} H={candle.high:.5f} "
                          f"L={candle.low:.5f} C={candle.close:.5f}")
        
        # Monitor all symbols concurrently
        tasks = [monitor_symbol(symbol) for symbol in symbols]
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            print("\nStopping multi-symbol monitoring...")


async def candle_volatility_tracker():
    """Example: Track candle volatility (range) over time."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"
    )
    
    async with client:
        print("=== Candle Volatility Tracker ===\n")
        print("Tracking average candle range for EURUSD...\n")
        
        ranges = []
        window_size = 20
        
        async with client.market_data.stream_candles("EURUSD", TimeFrame.M15) as stream:
            async for candle in stream:
                # Calculate candle range
                candle_range = candle.high - candle.low
                ranges.append(candle_range)
                
                if len(ranges) > window_size:
                    ranges.pop(0)
                
                # Calculate average range
                avg_range = sum(ranges) / len(ranges)
                
                timestamp = candle.datetime.strftime("%H:%M") if candle.datetime else "N/A"
                
                # Determine if current candle is above/below average
                if candle_range > avg_range * 1.5:
                    volatility_status = "🔥 HIGH VOLATILITY"
                elif candle_range < avg_range * 0.5:
                    volatility_status = "😴 LOW VOLATILITY"
                else:
                    volatility_status = "📊 NORMAL"
                
                print(f"[{timestamp}] Range={candle_range:.5f} | "
                      f"Avg({window_size})={avg_range:.5f} | {volatility_status}")


if __name__ == "__main__":
    # Run different examples
    import sys
    
    if len(sys.argv) > 1:
        example = sys.argv[1]
        examples = {
            "basic": basic_candle_streaming,
            "multi-tf": multi_timeframe_analysis,
            "patterns": candle_pattern_detection,
            "sma": indicator_based_strategy,
            "multi-symbol": multi_symbol_candles,
            "volatility": candle_volatility_tracker,
        }
        
        if example in examples:
            asyncio.run(examples[example]())
        else:
            print(f"Unknown example: {example}")
            print(f"Available examples: {', '.join(examples.keys())}")
    else:
        # Run basic example by default
        asyncio.run(basic_candle_streaming())
