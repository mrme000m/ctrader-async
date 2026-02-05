"""
Comprehensive integration tests for cTrader async client.

These tests connect to the real cTrader demo server and test all functionality.
Requires valid credentials in .env file.

Run with: pytest tests/test_integration.py -v -s
"""

import asyncio
import pytest
import os
import time
from pathlib import Path

# Ensure project root is on sys.path for imports
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ctrader_async import (
    CTraderClient,
    TradeSide,
    TimeFrame,
    TimeInForce,
)
from ctrader_async.utils.errors import (
    TradingError,
    MarketClosedError,
    OrderError,
)


# Mark all tests as integration tests
pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


# NOTE: `client` fixture is provided by `tests/conftest.py` (pytest-asyncio fixture)


class TestConnection:
    """Test connection and authentication."""
    
    @pytest.mark.asyncio
    async def test_connect_with_context_manager(self):
        """Test connecting with context manager."""
        async with CTraderClient.from_env() as client:
            assert client.is_connected
            assert client.is_authenticated
            assert client.is_ready
    
    @pytest.mark.asyncio
    async def test_connect_disconnect(self):
        """Test manual connect and disconnect."""
        client = CTraderClient.from_env()
        
        await client.connect()
        assert client.is_connected
        assert client.is_authenticated
        
        await client.disconnect()
        assert not client.is_connected
        assert not client.is_authenticated


class TestAccountAPI:
    """Test account management API."""
    
    @pytest.mark.asyncio
    async def test_get_account_info(self, client):
        """Test getting account information."""
        account = await client.account.get_info()
        
        assert account is not None
        assert account.balance > 0
        assert account.equity > 0
        assert account.free_margin >= 0
        assert account.account_id == client.config.account_id
        
        print(f"\n✅ Account Info:")
        print(f"   Balance: ${account.balance:,.2f}")
        print(f"   Equity: ${account.equity:,.2f}")
        print(f"   Margin: ${account.margin:,.2f}")
        print(f"   Free Margin: ${account.free_margin:,.2f}")
    
    @pytest.mark.asyncio
    async def test_get_account_info_cached(self, client):
        """Test account info caching."""
        account1 = await client.account.get_info()
        account2 = await client.account.get_info()  # Should use cache
        
        assert account1.balance == account2.balance


class TestSymbolsAPI:
    """Test symbol catalog API."""
    
    @pytest.mark.asyncio
    async def test_get_all_symbols(self, client):
        """Test getting all symbols."""
        symbols = await client.symbols.get_all()
        
        assert len(symbols) > 0
        print(f"\n✅ Loaded {len(symbols)} symbols")
    
    @pytest.mark.asyncio
    async def test_get_specific_symbol(self, client):
        """Test getting specific symbol."""
        eurusd = await client.symbols.get_symbol("EURUSD")
        
        assert eurusd is not None
        assert eurusd.name == "EURUSD"
        assert eurusd.digits >= 3
        assert eurusd.lot_size_units > 0
        
        print(f"\n✅ EURUSD Info:")
        print(f"   Digits: {eurusd.digits}")
        print(f"   Pip Size: {eurusd.pip_size}")
        print(f"   Lot Size: {eurusd.lot_size_units}")
    
    @pytest.mark.asyncio
    async def test_search_symbols(self, client):
        """Test symbol search."""
        eur_symbols = await client.symbols.search("EUR")
        
        assert len(eur_symbols) > 0
        # Some symbol names may contain separators/suffixes; ensure at least one match
        assert any("EUR" in s.name.upper() for s in eur_symbols)
        
        print(f"\n✅ Found {len(eur_symbols)} EUR symbols")


class TestMarketOrderTrading:
    """Test market order operations."""
    
    @pytest.mark.asyncio
    async def test_place_market_order(self, client):
        """Test placing a market order."""
        # Place a small market order
        position = await client.trading.place_market_order(
            symbol="EURUSD",
            side=TradeSide.BUY,
            volume=0.01,  # Micro lot
            comment="Integration test - market order"
        )
        
        assert position is not None
        assert position.id > 0
        assert position.symbol_name == "EURUSD"
        assert position.volume == 0.01
        assert position.side == "BUY"
        assert position.entry_price > 0
        
        print(f"\n✅ Market Order Placed:")
        print(f"   Position ID: {position.id}")
        print(f"   Entry Price: {position.entry_price}")
        
        # Close the position
        await asyncio.sleep(1)
        await client.trading.close_position(position.id)
        print(f"   ✅ Position closed")
    
    @pytest.mark.asyncio
    async def test_market_order_with_sltp(self, client):
        """Test market order with SL/TP."""
        # Get current price range
        eurusd = await client.symbols.get_symbol("EURUSD")
        
        # Place order with SL/TP
        position = await client.trading.place_market_order(
            symbol="EURUSD",
            side=TradeSide.BUY,
            volume=0.01,
            stop_loss=1.0000,  # Far from market
            take_profit=1.5000,  # Far from market
            comment="Integration test - with SL/TP"
        )
        
        assert position is not None
        assert position.stop_loss is not None
        assert position.take_profit is not None
        
        print(f"\n✅ Market Order with SL/TP:")
        print(f"   Position ID: {position.id}")
        print(f"   Entry: {position.entry_price}")
        print(f"   Stop Loss: {position.stop_loss}")
        print(f"   Take Profit: {position.take_profit}")
        
        # Close position
        await asyncio.sleep(1)
        await client.trading.close_position(position.id)
        print(f"   ✅ Position closed")


class TestLimitOrderTrading:
    """Test limit order operations."""
    
    @pytest.mark.asyncio
    async def test_place_limit_order(self, client):
        """Test placing a limit order."""
        # Place a limit order far from market (won't execute)
        order = await client.trading.place_limit_order(
            symbol="EURUSD",
            side=TradeSide.BUY,
            volume=0.01,
            price=0.9500,  # Far below market
            comment="Integration test - limit order"
        )
        
        assert order is not None
        assert order.symbol_name == "EURUSD"
        assert order.volume == 0.01
        assert order.side == "BUY"
        assert order.limit_price == 0.9500
        
        print(f"\n✅ Limit Order Placed:")
        print(f"   Order ID: {order.id}")
        print(f"   Limit Price: {order.limit_price}")
        
        # Cancel the order
        if order.id > 0:
            await asyncio.sleep(1)
            await client.trading.cancel_order(order.id)
            print(f"   ✅ Order cancelled")
    
    @pytest.mark.asyncio
    async def test_limit_order_with_sltp(self, client):
        """Test limit order with SL/TP."""
        order = await client.trading.place_limit_order(
            symbol="EURUSD",
            side=TradeSide.BUY,
            volume=0.01,
            price=0.9500,
            stop_loss=0.9400,
            take_profit=0.9600,
            time_in_force=TimeInForce.GOOD_TILL_CANCEL,
            comment="Integration test - limit with SL/TP"
        )
        
        assert order is not None
        assert order.limit_price == 0.9500
        assert order.stop_loss == 0.9400
        assert order.take_profit == 0.9600
        
        print(f"\n✅ Limit Order with SL/TP:")
        print(f"   Order ID: {order.id}")
        print(f"   Limit: {order.limit_price}")
        print(f"   SL: {order.stop_loss}")
        print(f"   TP: {order.take_profit}")
        
        # Cancel
        if order.id > 0:
            await asyncio.sleep(1)
            await client.trading.cancel_order(order.id)
            print(f"   ✅ Order cancelled")


class TestStopOrderTrading:
    """Test stop order operations."""
    
    @pytest.mark.asyncio
    async def test_place_stop_order(self, client):
        """Test placing a stop order."""
        # Place a stop order far from market (won't execute)
        order = await client.trading.place_stop_order(
            symbol="EURUSD",
            side=TradeSide.BUY,
            volume=0.01,
            stop_price=1.5000,  # Far above market
            comment="Integration test - stop order"
        )
        
        assert order is not None
        assert order.symbol_name == "EURUSD"
        assert order.volume == 0.01
        assert order.side == "BUY"
        assert order.stop_price == 1.5000
        
        print(f"\n✅ Stop Order Placed:")
        print(f"   Order ID: {order.id}")
        print(f"   Stop Price: {order.stop_price}")
        
        # Cancel
        if order.id > 0:
            await asyncio.sleep(1)
            await client.trading.cancel_order(order.id)
            print(f"   ✅ Order cancelled")
    
    @pytest.mark.asyncio
    async def test_stop_order_with_sltp(self, client):
        """Test stop order with SL/TP."""
        order = await client.trading.place_stop_order(
            symbol="EURUSD",
            side=TradeSide.BUY,
            volume=0.01,
            stop_price=1.5000,
            stop_loss=1.4900,
            take_profit=1.5100,
            comment="Integration test - stop with SL/TP"
        )
        
        assert order is not None
        assert order.stop_price == 1.5000
        assert order.stop_loss == 1.4900
        assert order.take_profit == 1.5100
        
        print(f"\n✅ Stop Order with SL/TP:")
        print(f"   Order ID: {order.id}")
        print(f"   Stop: {order.stop_price}")
        print(f"   SL: {order.stop_loss}")
        print(f"   TP: {order.take_profit}")
        
        # Cancel
        if order.id > 0:
            await asyncio.sleep(1)
            await client.trading.cancel_order(order.id)
            print(f"   ✅ Order cancelled")


class TestStopLimitOrderTrading:
    """Test stop-limit order operations."""
    
    @pytest.mark.asyncio
    async def test_place_stop_limit_order(self, client):
        """Test placing a stop-limit order."""
        order = await client.trading.place_stop_limit_order(
            symbol="EURUSD",
            side=TradeSide.BUY,
            volume=0.01,
            stop_price=1.5000,  # Far above market
            limit_price=1.5010,  # Limit after stop
            comment="Integration test - stop-limit order"
        )
        
        assert order is not None
        assert order.symbol_name == "EURUSD"
        assert order.volume == 0.01
        assert order.side == "BUY"
        assert order.stop_price == 1.5000
        assert order.limit_price == 1.5010
        
        print(f"\n✅ Stop-Limit Order Placed:")
        print(f"   Order ID: {order.id}")
        print(f"   Stop Price: {order.stop_price}")
        print(f"   Limit Price: {order.limit_price}")
        
        # Cancel
        if order.id > 0:
            await asyncio.sleep(1)
            await client.trading.cancel_order(order.id)
            print(f"   ✅ Order cancelled")
    
    @pytest.mark.asyncio
    async def test_stop_limit_order_full(self, client):
        """Test stop-limit order with all parameters."""
        order = await client.trading.place_stop_limit_order(
            symbol="EURUSD",
            side=TradeSide.SELL,
            volume=0.01,
            stop_price=0.5000,  # Far below market
            limit_price=0.4990,
            stop_loss=0.5100,
            take_profit=0.4900,
            time_in_force=TimeInForce.GOOD_TILL_CANCEL,
            comment="Integration test - full stop-limit"
        )
        
        assert order is not None
        assert order.stop_price == 0.5000
        assert order.limit_price == 0.4990
        assert order.stop_loss == 0.5100
        assert order.take_profit == 0.4900
        
        print(f"\n✅ Full Stop-Limit Order:")
        print(f"   Order ID: {order.id}")
        print(f"   Stop: {order.stop_price}, Limit: {order.limit_price}")
        print(f"   SL: {order.stop_loss}, TP: {order.take_profit}")
        
        # Cancel
        if order.id > 0:
            await asyncio.sleep(1)
            await client.trading.cancel_order(order.id)
            print(f"   ✅ Order cancelled")


class TestPositionManagement:
    """Test position management operations."""
    
    @pytest.mark.asyncio
    async def test_modify_position(self, client):
        """Test modifying position SL/TP."""
        # Open position
        position = await client.trading.place_market_order(
            symbol="EURUSD",
            side=TradeSide.BUY,
            volume=0.01,
            comment="Integration test - modify position"
        )
        
        await asyncio.sleep(1)
        
        # Modify SL/TP
        await client.trading.modify_position(
            position.id,
            stop_loss=1.0000,
            take_profit=1.5000
        )
        
        print(f"\n✅ Position Modified:")
        print(f"   Position ID: {position.id}")
        print(f"   New SL: 1.0000")
        print(f"   New TP: 1.5000")
        
        # Close
        await asyncio.sleep(1)
        await client.trading.close_position(position.id)
        print(f"   ✅ Position closed")
    
    @pytest.mark.asyncio
    async def test_get_positions(self, client):
        """Test getting all positions."""
        # Open a position
        position = await client.trading.place_market_order(
            symbol="EURUSD",
            side=TradeSide.BUY,
            volume=0.01
        )
        
        await asyncio.sleep(1)
        
        # Get positions
        positions = await client.trading.get_positions()
        
        assert len(positions) > 0
        assert any(p.id == position.id for p in positions)
        
        print(f"\n✅ Found {len(positions)} open position(s)")
        
        # Cleanup
        await client.trading.close_position(position.id)
    
    @pytest.mark.asyncio
    async def test_partial_close(self, client):
        """Test partial position close."""
        # Open larger position
        position = await client.trading.place_market_order(
            symbol="EURUSD",
            side=TradeSide.BUY,
            volume=0.02
        )
        
        await asyncio.sleep(1)
        
        # Close half
        await client.trading.close_position(position.id, volume=0.01)
        
        print(f"\n✅ Partial Close:")
        print(f"   Closed 0.01 lots of 0.02")
        
        # Close remaining
        await asyncio.sleep(1)
        await client.trading.close_position(position.id)
        print(f"   ✅ Remaining position closed")


class TestOrderManagement:
    """Test order management operations."""
    
    @pytest.mark.asyncio
    async def test_get_orders(self, client):
        """Test getting all pending orders."""
        # Place an order
        order = await client.trading.place_limit_order(
            symbol="EURUSD",
            side=TradeSide.BUY,
            volume=0.01,
            price=0.9500
        )
        
        await asyncio.sleep(1)
        
        # Get orders
        orders = await client.trading.get_orders()
        
        assert len(orders) > 0
        
        print(f"\n✅ Found {len(orders)} pending order(s)")
        
        # Cleanup
        if order.id > 0:
            await client.trading.cancel_order(order.id)
    
    @pytest.mark.asyncio
    async def test_cancel_all_orders(self, client):
        """Test cancelling all orders."""
        # Place multiple orders
        await client.trading.place_limit_order(
            symbol="EURUSD", side=TradeSide.BUY,
            volume=0.01, price=0.9500
        )
        await client.trading.place_limit_order(
            symbol="EURUSD", side=TradeSide.BUY,
            volume=0.01, price=0.9400
        )
        
        await asyncio.sleep(1)
        
        # Cancel all
        await client.trading.cancel_all_orders()
        
        await asyncio.sleep(1)
        
        # Verify
        orders = await client.trading.get_orders()
        assert len(orders) == 0
        
        print(f"\n✅ All orders cancelled")


class TestMarketData:
    """Test market data API."""
    
    @pytest.mark.asyncio
    async def test_get_candles(self, client):
        """Test getting historical candles."""
        candles = await client.market_data.get_candles(
            symbol="EURUSD",
            timeframe=TimeFrame.H1,
            count=10
        )
        
        assert len(candles) > 0
        assert all(c.open > 0 for c in candles)
        assert all(c.high >= c.low for c in candles)
        
        print(f"\n✅ Retrieved {len(candles)} H1 candles")
        print(f"   Latest: O={candles[-1].open:.5f} H={candles[-1].high:.5f}")
    
    @pytest.mark.asyncio
    async def test_stream_ticks(self, client):
        """Test streaming tick data."""
        print(f"\n✅ Streaming ticks for 5 seconds...")
        
        tick_count = 0
        start_time = time.time()
        
        async with client.market_data.stream_ticks("EURUSD") as stream:
            async for tick in stream:
                tick_count += 1
                print(f"   Tick #{tick_count}: Bid={tick.bid:.5f}, Ask={tick.ask:.5f}")
                
                # Stop after 5 seconds or 10 ticks
                if time.time() - start_time > 5 or tick_count >= 10:
                    break
        
        assert tick_count > 0
        print(f"✅ Received {tick_count} ticks")


class TestBulkOperations:
    """Test bulk operations."""
    
    @pytest.mark.asyncio
    async def test_close_all_positions(self, client):
        """Test closing all positions."""
        # Open multiple positions
        await client.trading.place_market_order(
            symbol="EURUSD", side=TradeSide.BUY, volume=0.01
        )
        await client.trading.place_market_order(
            symbol="EURUSD", side=TradeSide.BUY, volume=0.01
        )
        
        await asyncio.sleep(1)
        
        # Close all
        await client.trading.close_all_positions()
        
        await asyncio.sleep(1)
        
        # Verify
        positions = await client.trading.get_positions()
        assert len(positions) == 0
        
        print(f"\n✅ All positions closed")


class TestAllOrderTypes:
    """Comprehensive test of all 4 order types in sequence."""
    
    @pytest.mark.asyncio
    async def test_all_order_types_sequence(self, client):
        """Test all 4 order types in sequence."""
        print("\n" + "="*70)
        print("COMPREHENSIVE ORDER TYPE TEST")
        print("="*70)
        
        # 1. MARKET ORDER
        print("\n1️⃣  Testing MARKET ORDER...")
        market_pos = await client.trading.place_market_order(
            symbol="EURUSD",
            side=TradeSide.BUY,
            volume=0.01,
            stop_loss=1.0000,
            take_profit=1.5000,
            comment="Test: Market Order"
        )
        print(f"   ✅ Market order executed at {market_pos.entry_price}")
        await asyncio.sleep(1)
        await client.trading.close_position(market_pos.id)
        print(f"   ✅ Position closed")
        
        # 2. LIMIT ORDER
        print("\n2️⃣  Testing LIMIT ORDER...")
        limit_order = await client.trading.place_limit_order(
            symbol="EURUSD",
            side=TradeSide.BUY,
            volume=0.01,
            price=0.9500,
            stop_loss=0.9400,
            take_profit=0.9600,
            comment="Test: Limit Order"
        )
        print(f"   ✅ Limit order placed at {limit_order.limit_price}")
        await asyncio.sleep(1)
        if limit_order.id > 0:
            await client.trading.cancel_order(limit_order.id)
            print(f"   ✅ Order cancelled")
        
        # 3. STOP ORDER
        print("\n3️⃣  Testing STOP ORDER...")
        stop_order = await client.trading.place_stop_order(
            symbol="EURUSD",
            side=TradeSide.BUY,
            volume=0.01,
            stop_price=1.5000,
            stop_loss=1.4900,
            take_profit=1.5100,
            comment="Test: Stop Order"
        )
        print(f"   ✅ Stop order placed at {stop_order.stop_price}")
        await asyncio.sleep(1)
        if stop_order.id > 0:
            await client.trading.cancel_order(stop_order.id)
            print(f"   ✅ Order cancelled")
        
        # 4. STOP-LIMIT ORDER
        print("\n4️⃣  Testing STOP-LIMIT ORDER...")
        stop_limit = await client.trading.place_stop_limit_order(
            symbol="EURUSD",
            side=TradeSide.BUY,
            volume=0.01,
            stop_price=1.5000,
            limit_price=1.5010,
            stop_loss=1.4900,
            take_profit=1.5100,
            comment="Test: Stop-Limit Order"
        )
        print(f"   ✅ Stop-limit placed: Stop={stop_limit.stop_price}, Limit={stop_limit.limit_price}")
        await asyncio.sleep(1)
        if stop_limit.id > 0:
            await client.trading.cancel_order(stop_limit.id)
            print(f"   ✅ Order cancelled")
        
        print("\n" + "="*70)
        print("✅ ALL 4 ORDER TYPES TESTED SUCCESSFULLY!")
        print("="*70)


if __name__ == "__main__":
    """Run tests directly for quick testing."""
    import sys
    
    print("\n" + "="*70)
    print("cTrader Async Client - Integration Tests")
    print("="*70)
    
    # Run with pytest
    sys.exit(pytest.main([__file__, "-v", "-s"]))
