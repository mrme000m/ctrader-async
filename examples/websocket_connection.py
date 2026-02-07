"""
Example: WebSocket Connection

This example demonstrates how to use WebSocket transport instead of TCP.
WebSocket is useful for:
- Firewall-friendly environments
- Proxy/reverse proxy scenarios
- Cloud deployments behind load balancers
- Web-based trading applications

Note: Requires the 'websockets' library:
    pip install websockets
"""

import asyncio
import logging
from ctc import CTraderClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def websocket_basic_example():
    """Basic WebSocket connection example."""
    
    # Create client with WebSocket transport
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo",
        use_websocket=True  # Enable WebSocket transport
    )
    
    async with client:
        print("=== WebSocket Connection Example ===\n")
        print(f"Connected via WebSocket: {client.is_connected}")
        print(f"Authenticated: {client.is_authenticated}\n")
        
        # Get account info
        account = await client.account.get_account_info()
        print(f"Account: {account.account_id}")
        print(f"Balance: {account.balance} {account.currency}")
        print(f"Equity: {account.equity}")
        print()
        
        # Get positions
        positions = await client.trading.get_positions()
        print(f"Open Positions: {len(positions)}")
        for pos in positions:
            print(f"  {pos.symbol_name}: {pos.volume} lots, PnL: {pos.pnl_net_unrealized}")


async def websocket_with_custom_settings():
    """WebSocket with custom ping settings."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo",
        use_websocket=True,
        # WebSocket-specific settings
        websocket_ping_interval=30.0,  # Ping every 30 seconds
        websocket_ping_timeout=15.0,    # 15 second timeout
    )
    
    async with client:
        print("=== WebSocket with Custom Settings ===\n")
        print("Using custom ping settings:")
        print("  Ping Interval: 30s")
        print("  Ping Timeout: 15s")
        print()
        
        # Stream ticks to test WebSocket stability
        print("Streaming ticks over WebSocket...")
        
        async with client.market_data.stream_ticks("EURUSD") as stream:
            count = 0
            async for tick in stream:
                print(f"Tick #{count+1}: Bid={tick.bid:.5f}, Ask={tick.ask:.5f}")
                count += 1
                
                if count >= 10:
                    break
        
        print("\n✅ WebSocket connection stable!")


async def websocket_vs_tcp_comparison():
    """Compare WebSocket and TCP connections."""
    
    print("=== WebSocket vs TCP Comparison ===\n")
    
    # Test TCP connection
    print("1. Testing TCP connection...")
    tcp_client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo",
        use_websocket=False  # TCP
    )
    
    import time
    tcp_start = time.time()
    
    async with tcp_client:
        tcp_connect_time = time.time() - tcp_start
        print(f"   TCP Connected in {tcp_connect_time:.2f}s")
        
        # Get account info
        tcp_api_start = time.time()
        await tcp_client.account.get_account_info()
        tcp_api_time = time.time() - tcp_api_start
        print(f"   API call took {tcp_api_time:.3f}s")
    
    print()
    
    # Test WebSocket connection
    print("2. Testing WebSocket connection...")
    ws_client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo",
        use_websocket=True  # WebSocket
    )
    
    ws_start = time.time()
    
    async with ws_client:
        ws_connect_time = time.time() - ws_start
        print(f"   WebSocket Connected in {ws_connect_time:.2f}s")
        
        # Get account info
        ws_api_start = time.time()
        await ws_client.account.get_account_info()
        ws_api_time = time.time() - ws_api_start
        print(f"   API call took {ws_api_time:.3f}s")
    
    print()
    print("Summary:")
    print(f"  TCP connection time: {tcp_connect_time:.2f}s")
    print(f"  WebSocket connection time: {ws_connect_time:.2f}s")
    print(f"  Both transports work identically for the API!")


async def websocket_streaming_example():
    """Stream real-time data over WebSocket."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo",
        use_websocket=True
    )
    
    async with client:
        print("=== WebSocket Streaming Example ===\n")
        print("Streaming multiple data types over WebSocket...\n")
        
        # Stream ticks
        print("1. Streaming ticks for EURUSD:")
        async with client.market_data.stream_ticks("EURUSD") as stream:
            count = 0
            async for tick in stream:
                print(f"   Tick: Bid={tick.bid:.5f}, Ask={tick.ask:.5f}")
                count += 1
                if count >= 5:
                    break
        
        print()
        
        # Stream order book depth
        print("2. Streaming order book depth:")
        try:
            async with client.market_data.stream_depth("EURUSD", depth=5) as stream:
                count = 0
                async for snapshot in stream:
                    print(f"   Depth: Spread={snapshot.spread:.5f}, "
                          f"Best Bid={snapshot.best_bid.price:.5f}, "
                          f"Best Ask={snapshot.best_ask.price:.5f}")
                    count += 1
                    if count >= 3:
                        break
        except Exception as e:
            print(f"   Depth streaming: {e}")
        
        print()
        
        # Stream candles
        print("3. Streaming live candles:")
        from ctc.enums import TimeFrame
        try:
            async with client.market_data.stream_candles("EURUSD", TimeFrame.M1) as stream:
                count = 0
                async for candle in stream:
                    print(f"   Candle: O={candle.open:.5f} H={candle.high:.5f} "
                          f"L={candle.low:.5f} C={candle.close:.5f}")
                    count += 1
                    if count >= 3:
                        break
        except Exception as e:
            print(f"   Candle streaming: {e}")
        
        print("\n✅ All streaming works over WebSocket!")


async def websocket_reconnect_example():
    """Test WebSocket reconnection."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo",
        use_websocket=True,
        reconnect_enabled=True,
        reconnect_max_attempts=5
    )
    
    async with client:
        print("=== WebSocket Reconnection Example ===\n")
        print("WebSocket supports automatic reconnection just like TCP!\n")
        
        # Setup reconnect event handlers
        client.events.on("client.reconnect.attempt", 
                        lambda e: print("⚠️  Reconnection attempt..."))
        client.events.on("client.reconnect.success", 
                        lambda e: print("✅ Reconnected successfully!"))
        
        # Stream data
        print("Streaming ticks (connection will auto-recover if interrupted)...")
        
        async with client.market_data.stream_ticks("EURUSD") as stream:
            count = 0
            async for tick in stream:
                print(f"Tick #{count+1}: Bid={tick.bid:.5f}")
                count += 1
                
                if count >= 20:
                    break
        
        print("\n✅ WebSocket reconnection works seamlessly!")


if __name__ == "__main__":
    # Run different examples
    import sys
    
    if len(sys.argv) > 1:
        example = sys.argv[1]
        examples = {
            "basic": websocket_basic_example,
            "custom": websocket_with_custom_settings,
            "compare": websocket_vs_tcp_comparison,
            "streaming": websocket_streaming_example,
            "reconnect": websocket_reconnect_example,
        }
        
        if example in examples:
            asyncio.run(examples[example]())
        else:
            print(f"Unknown example: {example}")
            print(f"Available examples: {', '.join(examples.keys())}")
    else:
        # Run basic example by default
        asyncio.run(websocket_basic_example())
