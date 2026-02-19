"""
Example: Using BetterStack logging with cTrader client.

This example demonstrates how to use BetterStack integration for:
- Structured log ingestion to BetterStack
- Automatic error tracking
- Heartbeat monitoring
- Debug and audit logging

Setup:
    1. Sign up at https://betterstack.com
    2. Create a new source and get your ingest host and source token
    3. Set environment variables:
       export BETTERSTACK_INGEST_HOST="in.logtail.com"
       export BETTERSTACK_SOURCE_TOKEN="your_source_token_here"
       
    Optional (for uptime monitoring):
       export BETTERSTACK_UPTIME_HEARTBEAT_URL="https://uptime.betterstack.com/..."

Usage:
    # Run with BetterStack logging enabled
    BETTERSTACK_INGEST_HOST=in.logtail.com \
    BETTERSTACK_SOURCE_TOKEN=your_token \
    python examples/with_betterstack_logging.py
    
    # Run with debug mode
    CTRADER_DEBUG=1 \
    BETTERSTACK_INGEST_HOST=in.logtail.com \
    BETTERSTACK_SOURCE_TOKEN=your_token \
    python examples/with_betterstack_logging.py
"""

import asyncio
import logging
import os

import ctc

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("betterstack_example")


async def main():
    """Run example with BetterStack logging."""
    
    # Check if BetterStack is configured
    if ctc.betterstack_enabled():
        logger.info("✅ BetterStack integration is enabled")
        
        # Setup BetterStack logging for all ctc loggers
        if ctc.setup_betterstack_logging:
            handler = ctc.setup_betterstack_logging(level=logging.INFO)
            if handler:
                logger.info("📡 BetterStack logging handler configured")
    else:
        logger.warning("⚠️  BetterStack not configured - set BETTERSTACK_INGEST_HOST and BETTERSTACK_SOURCE_TOKEN")
        logger.info("Continuing without BetterStack integration...")
    
    # Print debug status
    debug_status = ctc.get_debug_status()
    logger.info(f"Debug status: {debug_status}")
    
    # Configuration from environment
    client_id = os.getenv("CTRADER_CLIENT_ID", "your_client_id")
    client_secret = os.getenv("CTRADER_CLIENT_SECRET", "your_client_secret")
    access_token = os.getenv("CTRADER_ACCESS_TOKEN", "your_access_token")
    account_id = int(os.getenv("CTRADER_ACCOUNT_ID", "0"))
    host_type = os.getenv("CTRADER_HOST_TYPE", "demo")
    
    if account_id == 0:
        logger.error("Please set CTRADER_ACCOUNT_ID environment variable")
        return
    
    logger.info(f"Connecting to cTrader {host_type} environment...")
    
    try:
        # Create client with BetterStack enabled (auto-detects from env vars)
        async with ctc.CTraderClient(
            client_id=client_id,
            client_secret=client_secret,
            access_token=access_token,
            account_id=account_id,
            host_type=host_type,
            # Enable BetterStack explicitly (optional if env vars are set)
            betterstack_enabled=True,
            betterstack_service_name="ctrader-example",
            betterstack_environment="demo",
        ) as client:
            
            logger.info("✅ Client connected successfully!")
            
            # Get account info
            account_info = await client.account.get_info()
            logger.info(f"Account balance: {account_info.balance} {account_info.currency}")
            
            # List available symbols
            symbols = await client.symbols.get_all_symbols()
            logger.info(f"Available symbols: {len(symbols)}")
            
            # Example: Get EURUSD tick
            try:
                tick = await client.market_data.get_last_tick("EURUSD")
                logger.info(f"EURUSD tick: bid={tick.bid}, ask={tick.ask}")
            except Exception as e:
                logger.warning(f"Could not get EURUSD tick: {e}")
            
            # Send custom log to BetterStack if enabled
            if ctc.betterstack_enabled() and hasattr(client, '_betterstack'):
                await client._send_betterstack_log({
                    "message": "Example script completed successfully",
                    "level": "info",
                    "event": "example.completed",
                    "symbols_count": len(symbols),
                })
                logger.info("📤 Custom log sent to BetterStack")
            
            logger.info("Disconnecting...")
        
        logger.info("✅ Example completed successfully!")
        
    except ctc.AuthenticationError as e:
        logger.error(f"❌ Authentication failed: {e}")
        logger.info("Please check your credentials and try again")
        
    except ctc.ConnectionError as e:
        logger.error(f"❌ Connection failed: {e}")
        
    except Exception as e:
        logger.exception("❌ Unexpected error occurred")
        raise


async def manual_betterstack_example():
    """Example of manual BetterStack logging without client integration."""
    
    from ctc.integrations import (
        BetterStackConfig,
        BetterStackHandler,
        send_betterstack_log,
        send_betterstack_heartbeat,
    )
    
    # Create configuration programmatically
    config = BetterStackConfig(
        ingest_host=os.getenv("BETTERSTACK_INGEST_HOST"),
        source_token=os.getenv("BETTERSTACK_SOURCE_TOKEN"),
        heartbeat_url=os.getenv("BETTERSTACK_UPTIME_HEARTBEAT_URL"),
        service_name="manual-example",
        environment="development",
    )
    
    if not config.is_configured():
        logger.warning("BetterStack not configured, skipping manual example")
        return
    
    # Create handler
    handler = BetterStackHandler(config)
    await handler.initialize()
    
    try:
        # Send structured logs
        await handler.send_log({
            "message": "Manual example started",
            "level": "info",
            "event": "manual_example.start",
        })
        
        # Simulate some work
        await asyncio.sleep(1)
        
        await handler.send_log({
            "message": "Manual example completed",
            "level": "info",
            "event": "manual_example.complete",
        })
        
        # Send heartbeat
        if config.heartbeat_url:
            success = await handler.send_heartbeat()
            logger.info(f"Heartbeat sent: {'✅' if success else '❌'}")
        
        # Example: Capture an exception
        try:
            1 / 0
        except ZeroDivisionError:
            await handler.capture_exception()
            logger.info("Exception captured and sent to BetterStack")
        
    finally:
        await handler.shutdown()


if __name__ == "__main__":
    print("=" * 60)
    print("cTrader + BetterStack Integration Example")
    print("=" * 60)
    print()
    
    # Run the main example
    asyncio.run(main())
    
    print()
    print("=" * 60)
    print("Manual BetterStack Example")
    print("=" * 60)
    print()
    
    # Run the manual example
    asyncio.run(manual_betterstack_example())
