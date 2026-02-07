"""
Tests for order book depth streaming functionality.
"""

import pytest
from datetime import datetime
from ctc.models import DepthQuote, DepthSnapshot


class TestDepthQuote:
    """Test DepthQuote model."""
    
    def test_depth_quote_creation(self):
        """Test creating a DepthQuote."""
        quote = DepthQuote(
            id=123,
            price=1.1234,
            volume=10.5,
            side="BUY"
        )
        
        assert quote.id == 123
        assert quote.price == 1.1234
        assert quote.volume == 10.5
        assert quote.side == "BUY"
    
    def test_depth_quote_ask_side(self):
        """Test creating an ask-side quote."""
        quote = DepthQuote(
            id=456,
            price=1.1236,
            volume=8.2,
            side="ASK"
        )
        
        assert quote.side == "ASK"


class TestDepthSnapshot:
    """Test DepthSnapshot model."""
    
    def test_depth_snapshot_creation(self):
        """Test creating a DepthSnapshot."""
        bids = [
            DepthQuote(1, 1.1234, 10.5, "BUY"),
            DepthQuote(2, 1.1233, 8.0, "BUY"),
            DepthQuote(3, 1.1232, 6.5, "BUY"),
        ]
        asks = [
            DepthQuote(4, 1.1236, 7.0, "ASK"),
            DepthQuote(5, 1.1237, 9.5, "ASK"),
            DepthQuote(6, 1.1238, 12.0, "ASK"),
        ]
        
        snapshot = DepthSnapshot(
            symbol_id=1,
            symbol_name="EURUSD",
            bids=bids,
            asks=asks,
            timestamp=1000000
        )
        
        assert snapshot.symbol_id == 1
        assert snapshot.symbol_name == "EURUSD"
        assert len(snapshot.bids) == 3
        assert len(snapshot.asks) == 3
        assert snapshot.timestamp == 1000000
    
    def test_best_bid(self):
        """Test getting best bid."""
        bids = [
            DepthQuote(1, 1.1234, 10.5, "BUY"),
            DepthQuote(2, 1.1233, 8.0, "BUY"),
        ]
        asks = [DepthQuote(3, 1.1236, 7.0, "ASK")]
        
        snapshot = DepthSnapshot(1, "EURUSD", bids, asks, 1000000)
        
        assert snapshot.best_bid is not None
        assert snapshot.best_bid.price == 1.1234
        assert snapshot.best_bid.volume == 10.5
    
    def test_best_ask(self):
        """Test getting best ask."""
        bids = [DepthQuote(1, 1.1234, 10.5, "BUY")]
        asks = [
            DepthQuote(2, 1.1236, 7.0, "ASK"),
            DepthQuote(3, 1.1237, 9.5, "ASK"),
        ]
        
        snapshot = DepthSnapshot(1, "EURUSD", bids, asks, 1000000)
        
        assert snapshot.best_ask is not None
        assert snapshot.best_ask.price == 1.1236
        assert snapshot.best_ask.volume == 7.0
    
    def test_spread(self):
        """Test spread calculation."""
        bids = [DepthQuote(1, 1.1234, 10.5, "BUY")]
        asks = [DepthQuote(2, 1.1236, 7.0, "ASK")]
        
        snapshot = DepthSnapshot(1, "EURUSD", bids, asks, 1000000)
        
        assert snapshot.spread is not None
        assert abs(snapshot.spread - 0.0002) < 0.0001
    
    def test_spread_empty_book(self):
        """Test spread with empty order book."""
        snapshot = DepthSnapshot(1, "EURUSD", [], [], 1000000)
        assert snapshot.spread is None
    
    def test_total_bid_volume(self):
        """Test total bid volume calculation."""
        bids = [
            DepthQuote(1, 1.1234, 10.5, "BUY"),
            DepthQuote(2, 1.1233, 8.0, "BUY"),
            DepthQuote(3, 1.1232, 6.5, "BUY"),
        ]
        asks = [DepthQuote(4, 1.1236, 7.0, "ASK")]
        
        snapshot = DepthSnapshot(1, "EURUSD", bids, asks, 1000000)
        
        # Test all levels
        total = snapshot.total_bid_volume()
        assert abs(total - 25.0) < 0.01
        
        # Test top 2 levels
        total_2 = snapshot.total_bid_volume(2)
        assert abs(total_2 - 18.5) < 0.01
    
    def test_total_ask_volume(self):
        """Test total ask volume calculation."""
        bids = [DepthQuote(1, 1.1234, 10.5, "BUY")]
        asks = [
            DepthQuote(2, 1.1236, 7.0, "ASK"),
            DepthQuote(3, 1.1237, 9.5, "ASK"),
            DepthQuote(4, 1.1238, 12.0, "ASK"),
        ]
        
        snapshot = DepthSnapshot(1, "EURUSD", bids, asks, 1000000)
        
        # Test all levels
        total = snapshot.total_ask_volume()
        assert abs(total - 28.5) < 0.01
        
        # Test top 2 levels
        total_2 = snapshot.total_ask_volume(2)
        assert abs(total_2 - 16.5) < 0.01
    
    def test_datetime_property(self):
        """Test datetime conversion."""
        snapshot = DepthSnapshot(
            1, "EURUSD", [], [], 
            timestamp=1609459200000  # 2021-01-01 00:00:00 UTC
        )
        
        dt = snapshot.datetime
        assert isinstance(dt, datetime)
        assert dt.year == 2021
        assert dt.month == 1
        assert dt.day == 1
    
    def test_empty_snapshot(self):
        """Test snapshot with no quotes."""
        snapshot = DepthSnapshot(1, "EURUSD", [], [], 1000000)
        
        assert snapshot.best_bid is None
        assert snapshot.best_ask is None
        assert snapshot.spread is None
        assert snapshot.total_bid_volume() == 0
        assert snapshot.total_ask_volume() == 0


class TestDepthStreamIntegration:
    """Integration tests for DepthStream (would require live connection)."""
    
    @pytest.mark.skip(reason="Requires live cTrader connection")
    async def test_depth_stream_subscription(self):
        """Test subscribing to depth stream."""
        # This would require actual cTrader credentials
        # Left as placeholder for integration testing
        pass
    
    @pytest.mark.skip(reason="Requires live cTrader connection")
    async def test_depth_stream_receiving_data(self):
        """Test receiving depth data from stream."""
        # This would require actual cTrader credentials
        # Left as placeholder for integration testing
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
