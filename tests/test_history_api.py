"""
Tests for Trading History API.
"""

import pytest
from datetime import datetime, timedelta
from ctc.models import Deal


class TestDealModel:
    """Test Deal model."""
    
    def test_deal_creation(self):
        """Test creating a Deal object."""
        deal = Deal(
            deal_id=12345,
            position_id=67890,
            order_id=11111,
            symbol_id=1,
            symbol_name="EURUSD",
            side="BUY",
            volume=1.0,
            execution_price=1.1234,
            commission=-5.0,
            swap=-1.5,
            pnl=50.0,
            timestamp=1609459200000
        )
        
        assert deal.deal_id == 12345
        assert deal.position_id == 67890
        assert deal.order_id == 11111
        assert deal.symbol_name == "EURUSD"
        assert deal.side == "BUY"
        assert deal.volume == 1.0
        assert deal.execution_price == 1.1234
        assert deal.commission == -5.0
        assert deal.swap == -1.5
        assert deal.pnl == 50.0
    
    def test_deal_datetime_conversion(self):
        """Test timestamp to datetime conversion."""
        deal = Deal(
            deal_id=1,
            timestamp=1609459200000  # 2021-01-01 00:00:00 UTC
        )
        
        dt = deal.datetime
        assert isinstance(dt, datetime)
        assert dt.year == 2021
        assert dt.month == 1
        assert dt.day == 1
    
    def test_deal_datetime_none(self):
        """Test datetime is None when no timestamp."""
        deal = Deal(deal_id=1)
        assert deal.datetime is None
    
    def test_deal_minimal(self):
        """Test creating deal with minimal info."""
        deal = Deal(deal_id=999)
        
        assert deal.deal_id == 999
        assert deal.position_id is None
        assert deal.symbol_name is None
        assert deal.volume is None
        assert deal.commission == 0.0
        assert deal.swap == 0.0
        assert deal.pnl == 0.0


class TestPerformanceCalculations:
    """Test performance calculation logic."""
    
    def test_win_rate_calculation(self):
        """Test win rate calculation."""
        deals = [
            Deal(deal_id=1, pnl=50.0),
            Deal(deal_id=2, pnl=-30.0),
            Deal(deal_id=3, pnl=20.0),
            Deal(deal_id=4, pnl=-10.0),
            Deal(deal_id=5, pnl=40.0),
        ]
        
        wins = sum(1 for d in deals if d.pnl > 0)
        total = len(deals)
        win_rate = (wins / total * 100)
        
        assert wins == 3
        assert win_rate == 60.0
    
    def test_total_pnl_calculation(self):
        """Test total PnL calculation."""
        deals = [
            Deal(deal_id=1, pnl=100.0),
            Deal(deal_id=2, pnl=-50.0),
            Deal(deal_id=3, pnl=30.0),
        ]
        
        total_pnl = sum(d.pnl for d in deals)
        assert total_pnl == 80.0
    
    def test_profit_factor_calculation(self):
        """Test profit factor calculation."""
        deals = [
            Deal(deal_id=1, pnl=100.0),
            Deal(deal_id=2, pnl=-40.0),
            Deal(deal_id=3, pnl=50.0),
            Deal(deal_id=4, pnl=-10.0),
        ]
        
        total_wins = sum(d.pnl for d in deals if d.pnl > 0)
        total_losses = abs(sum(d.pnl for d in deals if d.pnl < 0))
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        assert total_wins == 150.0
        assert total_losses == 50.0
        assert profit_factor == 3.0
    
    def test_average_win_loss(self):
        """Test average win and loss calculation."""
        deals = [
            Deal(deal_id=1, pnl=100.0),
            Deal(deal_id=2, pnl=-40.0),
            Deal(deal_id=3, pnl=60.0),
            Deal(deal_id=4, pnl=-20.0),
        ]
        
        wins = [d.pnl for d in deals if d.pnl > 0]
        losses = [abs(d.pnl) for d in deals if d.pnl < 0]
        
        avg_win = sum(wins) / len(wins) if wins else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        
        assert avg_win == 80.0
        assert avg_loss == 30.0
    
    def test_net_pnl_with_costs(self):
        """Test net PnL including commission and swap."""
        deals = [
            Deal(deal_id=1, pnl=100.0, commission=-5.0, swap=-2.0),
            Deal(deal_id=2, pnl=50.0, commission=-3.0, swap=-1.0),
        ]
        
        total_pnl = sum(d.pnl for d in deals)
        total_commission = sum(d.commission for d in deals)
        total_swap = sum(d.swap for d in deals)
        net_pnl = total_pnl + total_commission + total_swap
        
        assert total_pnl == 150.0
        assert total_commission == -8.0
        assert total_swap == -3.0
        assert net_pnl == 139.0


class TestSymbolBreakdown:
    """Test symbol-based analysis."""
    
    def test_group_by_symbol(self):
        """Test grouping deals by symbol."""
        deals = [
            Deal(deal_id=1, symbol_name="EURUSD", pnl=50.0),
            Deal(deal_id=2, symbol_name="GBPUSD", pnl=30.0),
            Deal(deal_id=3, symbol_name="EURUSD", pnl=-20.0),
            Deal(deal_id=4, symbol_name="GBPUSD", pnl=10.0),
        ]
        
        symbol_stats = {}
        for deal in deals:
            symbol = deal.symbol_name or "UNKNOWN"
            if symbol not in symbol_stats:
                symbol_stats[symbol] = {'deals': 0, 'pnl': 0.0}
            
            symbol_stats[symbol]['deals'] += 1
            symbol_stats[symbol]['pnl'] += deal.pnl
        
        assert symbol_stats['EURUSD']['deals'] == 2
        assert symbol_stats['EURUSD']['pnl'] == 30.0
        assert symbol_stats['GBPUSD']['deals'] == 2
        assert symbol_stats['GBPUSD']['pnl'] == 40.0


class TestTimeRangeQueries:
    """Test time range filtering."""
    
    def test_filter_by_date_range(self):
        """Test filtering deals by date range."""
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        two_days_ago = now - timedelta(days=2)
        
        deals = [
            Deal(deal_id=1, timestamp=int(two_days_ago.timestamp() * 1000)),
            Deal(deal_id=2, timestamp=int(yesterday.timestamp() * 1000)),
            Deal(deal_id=3, timestamp=int(now.timestamp() * 1000)),
        ]
        
        # Filter for last day
        from_ts = int(yesterday.timestamp() * 1000)
        recent_deals = [d for d in deals if d.timestamp and d.timestamp >= from_ts]
        
        assert len(recent_deals) == 2
    
    def test_daily_grouping(self):
        """Test grouping deals by day."""
        base_time = datetime(2021, 1, 1, 10, 0, 0)
        
        deals = [
            Deal(deal_id=1, timestamp=int(base_time.timestamp() * 1000)),
            Deal(deal_id=2, timestamp=int((base_time + timedelta(hours=2)).timestamp() * 1000)),
            Deal(deal_id=3, timestamp=int((base_time + timedelta(days=1)).timestamp() * 1000)),
        ]
        
        daily_stats = {}
        for deal in deals:
            if deal.datetime:
                date_key = deal.datetime.date()
                if date_key not in daily_stats:
                    daily_stats[date_key] = 0
                daily_stats[date_key] += 1
        
        assert len(daily_stats) == 2
        assert daily_stats[base_time.date()] == 2


class TestHistoryAPIIntegration:
    """Integration tests for HistoryAPI (would require live connection)."""
    
    @pytest.mark.skip(reason="Requires live cTrader connection")
    async def test_get_deals(self):
        """Test getting deal history."""
        # This would require actual cTrader credentials
        # Left as placeholder for integration testing
        pass
    
    @pytest.mark.skip(reason="Requires live cTrader connection")
    async def test_get_deals_by_position(self):
        """Test getting deals for specific position."""
        # This would require actual cTrader credentials
        # Left as placeholder for integration testing
        pass
    
    @pytest.mark.skip(reason="Requires live cTrader connection")
    async def test_get_order_details(self):
        """Test getting order details."""
        # This would require actual cTrader credentials
        # Left as placeholder for integration testing
        pass
    
    @pytest.mark.skip(reason="Requires live cTrader connection")
    async def test_get_performance_summary(self):
        """Test getting performance summary."""
        # This would require actual cTrader credentials
        # Left as placeholder for integration testing
        pass


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_deal_list(self):
        """Test handling empty deal list."""
        deals = []
        
        total_pnl = sum(d.pnl for d in deals)
        wins = sum(1 for d in deals if d.pnl > 0)
        win_rate = (wins / len(deals) * 100) if deals else 0
        
        assert total_pnl == 0
        assert wins == 0
        assert win_rate == 0
    
    def test_all_zero_pnl(self):
        """Test deals with zero PnL."""
        deals = [
            Deal(deal_id=1, pnl=0.0),
            Deal(deal_id=2, pnl=0.0),
            Deal(deal_id=3, pnl=0.0),
        ]
        
        wins = sum(1 for d in deals if d.pnl > 0)
        losses = sum(1 for d in deals if d.pnl < 0)
        
        assert wins == 0
        assert losses == 0
    
    def test_profit_factor_no_losses(self):
        """Test profit factor with no losses."""
        deals = [
            Deal(deal_id=1, pnl=100.0),
            Deal(deal_id=2, pnl=50.0),
        ]
        
        total_wins = sum(d.pnl for d in deals if d.pnl > 0)
        total_losses = abs(sum(d.pnl for d in deals if d.pnl < 0))
        profit_factor = (total_wins / total_losses) if total_losses > 0 else 0
        
        assert total_wins == 150.0
        assert total_losses == 0.0
        assert profit_factor == 0.0  # Or could be inf/undefined


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
