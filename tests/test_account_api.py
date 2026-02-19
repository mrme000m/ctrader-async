"""
Tests for Account Management API.
"""

import pytest
from datetime import datetime
from ctc.models import FullAccountInfo, LeverageTier, DynamicLeverage, PositionPnLRealtime


class TestFullAccountInfo:
    """Test FullAccountInfo model."""
    
    def test_full_account_info_creation(self):
        """Test creating a FullAccountInfo object."""
        info = FullAccountInfo(
            account_id=12345,
            balance=10000.50,
            equity=10200.75,
            margin=2000.0,
            free_margin=8200.75,
            currency="USD",
            account_type="HEDGED",
            money_digits=2,
            margin_level=510.04,
            leverage=100.0,
            unrealized_pnl=200.25,
            swap=-5.50,
            commission=-10.0
        )
        
        assert info.account_id == 12345
        assert info.balance == 10000.50
        assert info.equity == 10200.75
        assert info.margin == 2000.0
        assert info.free_margin == 8200.75
        assert info.currency == "USD"
        assert info.account_type == "HEDGED"
        assert info.margin_level == 510.04
        assert info.leverage == 100.0
        assert info.unrealized_pnl == 200.25
    
    def test_formatted_properties(self):
        """Test formatted property outputs."""
        info = FullAccountInfo(
            account_id=12345,
            balance=12345.6789,
            equity=12346.7890,
            margin=100.0,
            free_margin=12246.7890,
            currency="EUR",
            account_type="NETTED",
            money_digits=2,
            margin_level=12346.79
        )
        
        assert info.formatted_balance == "12345.68"
        assert info.formatted_equity == "12346.79"
        assert info.formatted_margin == "100.00"
        assert info.formatted_free_margin == "12246.79"
        assert info.formatted_margin_level == "12346.79%"
    
    def test_margin_call_risk_levels(self):
        """Test margin call risk level assessment."""
        # Low risk
        info_low = FullAccountInfo(
            account_id=1, balance=10000, equity=10000,
            margin=1000, free_margin=9000,
            currency="USD", account_type="HEDGED",
            margin_level=200.0
        )
        assert info_low.margin_call_risk == "LOW"
        
        # Medium risk
        info_med = FullAccountInfo(
            account_id=1, balance=10000, equity=10000,
            margin=6666, free_margin=3334,
            currency="USD", account_type="HEDGED",
            margin_level=150.0
        )
        assert info_med.margin_call_risk == "MEDIUM"
        
        # High risk
        info_high = FullAccountInfo(
            account_id=1, balance=10000, equity=10000,
            margin=10000, free_margin=0,
            currency="USD", account_type="HEDGED",
            margin_level=100.0
        )
        assert info_high.margin_call_risk == "HIGH"
        
        # Critical risk
        info_crit = FullAccountInfo(
            account_id=1, balance=10000, equity=5000,
            margin=10000, free_margin=-5000,
            currency="USD", account_type="HEDGED",
            margin_level=50.0
        )
        assert info_crit.margin_call_risk == "CRITICAL"
        
        # Unknown risk
        info_unknown = FullAccountInfo(
            account_id=1, balance=10000, equity=10000,
            margin=0, free_margin=10000,
            currency="USD", account_type="HEDGED",
            margin_level=None
        )
        assert info_unknown.margin_call_risk == "UNKNOWN"
    
    def test_datetime_conversion(self):
        """Test timestamp to datetime conversion."""
        info = FullAccountInfo(
            account_id=1, balance=10000, equity=10000,
            margin=1000, free_margin=9000,
            currency="USD", account_type="HEDGED",
            timestamp=1609459200000  # 2021-01-01 00:00:00 UTC
        )
        
        dt = info.last_update_datetime
        assert isinstance(dt, datetime)
        assert dt.year == 2021
        assert dt.month == 1
        assert dt.day == 1
    
    def test_repr(self):
        """Test string representation."""
        info = FullAccountInfo(
            account_id=12345,
            balance=10000.0,
            equity=10200.0,
            margin=2000.0,
            free_margin=8200.0,
            currency="USD",
            account_type="HEDGED",
            margin_level=510.0
        )
        
        repr_str = repr(info)
        assert "FullAccountInfo" in repr_str
        assert "USD" in repr_str
        assert "510.00%" in repr_str


class TestLeverageTier:
    """Test LeverageTier model."""
    
    def test_leverage_tier_creation(self):
        """Test creating a LeverageTier."""
        tier = LeverageTier(
            tier_id=1,
            volume_from=0.0,
            volume_to=1.0,
            leverage=500.0
        )
        
        assert tier.tier_id == 1
        assert tier.volume_from == 0.0
        assert tier.volume_to == 1.0
        assert tier.leverage == 500.0
    
    def test_margin_percent_calculation(self):
        """Test margin percent calculation."""
        tier_100 = LeverageTier(1, 0.0, 1.0, 100.0)
        assert tier_100.margin_percent == 1.0  # 1% margin
        
        tier_500 = LeverageTier(1, 0.0, 1.0, 500.0)
        assert tier_500.margin_percent == 0.2  # 0.2% margin
        
        tier_unlimited = LeverageTier(1, 0.0, None, 50.0)
        assert tier_unlimited.margin_percent == 2.0  # 2% margin
    
    def test_repr(self):
        """Test string representation."""
        tier = LeverageTier(1, 0.0, 1.0, 100.0)
        repr_str = repr(tier)
        assert "LeverageTier" in repr_str
        assert "1:100" in repr_str


class TestDynamicLeverage:
    """Test DynamicLeverage model."""
    
    def test_dynamic_leverage_creation(self):
        """Test creating DynamicLeverage."""
        tiers = [
            LeverageTier(1, 0.0, 1.0, 500.0),
            LeverageTier(2, 1.0, 5.0, 200.0),
            LeverageTier(3, 5.0, None, 100.0),
        ]
        
        dyn_lev = DynamicLeverage(
            symbol_id=123,
            symbol_name="EURUSD",
            tiers=tiers,
            total_volume=0.0
        )
        
        assert dyn_lev.symbol_id == 123
        assert dyn_lev.symbol_name == "EURUSD"
        assert len(dyn_lev.tiers) == 3
    
    def test_get_leverage_for_volume(self):
        """Test leverage lookup for different volumes."""
        tiers = [
            LeverageTier(1, 0.0, 1.0, 500.0),
            LeverageTier(2, 1.0, 5.0, 200.0),
            LeverageTier(3, 5.0, None, 100.0),
        ]
        
        dyn_lev = DynamicLeverage(
            symbol_id=123,
            symbol_name="EURUSD",
            tiers=tiers
        )
        
        # Volume in tier 1
        assert dyn_lev.get_leverage_for_volume(0.5) == 500.0
        # Volume in tier 2
        assert dyn_lev.get_leverage_for_volume(3.0) == 200.0
        # Volume in tier 3
        assert dyn_lev.get_leverage_for_volume(10.0) == 100.0
        # Edge case: exactly at tier boundary uses first matching tier
        assert dyn_lev.get_leverage_for_volume(1.0) == 500.0
        # Just above tier 1 boundary
        assert dyn_lev.get_leverage_for_volume(1.01) == 200.0
    
    def test_calculate_margin(self):
        """Test margin calculation."""
        tiers = [
            LeverageTier(1, 0.0, 1.0, 100.0),
        ]
        
        dyn_lev = DynamicLeverage(
            symbol_id=123,
            symbol_name="EURUSD",
            tiers=tiers
        )
        
        # $100,000 notional at 1:100 leverage = $1,000 margin
        margin = dyn_lev.calculate_margin(1.0, 100000.0)
        assert margin == 1000.0
        
        # $200,000 notional at 1:100 leverage = $2,000 margin
        margin = dyn_lev.calculate_margin(2.0, 200000.0)
        assert margin == 2000.0
    
    def test_empty_tiers(self):
        """Test behavior with empty tiers list."""
        dyn_lev = DynamicLeverage(
            symbol_id=123,
            symbol_name="EURUSD",
            tiers=[]
        )
        
        # Should return default leverage of 100
        assert dyn_lev.get_leverage_for_volume(1.0) == 100.0


class TestPositionPnLRealtime:
    """Test PositionPnLRealtime model."""
    
    def test_position_pnl_realtime_creation(self):
        """Test creating PositionPnLRealtime."""
        pnl = PositionPnLRealtime(
            position_id=12345,
            gross_unrealized_pnl=150.0,
            net_unrealized_pnl=145.0,
            swap=-3.0,
            commission=-2.0,
            money_digits=2,
            timestamp=1609459200000
        )
        
        assert pnl.position_id == 12345
        assert pnl.gross_unrealized_pnl == 150.0
        assert pnl.net_unrealized_pnl == 145.0
        assert pnl.swap == -3.0
        assert pnl.commission == -2.0
    
    def test_formatted_pnl(self):
        """Test formatted PnL output."""
        pnl = PositionPnLRealtime(
            position_id=1,
            gross_unrealized_pnl=123.456,
            net_unrealized_pnl=-78.901,
            money_digits=2
        )
        
        assert pnl.formatted_gross_pnl == "+123.46"
        assert pnl.formatted_net_pnl == "-78.90"
    
    def test_total_costs(self):
        """Test total costs calculation."""
        pnl = PositionPnLRealtime(
            position_id=1,
            gross_unrealized_pnl=100.0,
            net_unrealized_pnl=95.0,
            swap=-3.0,
            commission=-2.0
        )
        
        # Total costs = abs(swap) + abs(commission)
        assert pnl.total_costs == 5.0
    
    def test_datetime_conversion(self):
        """Test timestamp to datetime conversion."""
        pnl = PositionPnLRealtime(
            position_id=1,
            gross_unrealized_pnl=100.0,
            net_unrealized_pnl=95.0,
            timestamp=1609459200000  # 2021-01-01 00:00:00 UTC
        )
        
        dt = pnl.datetime
        assert isinstance(dt, datetime)
        assert dt.year == 2021
        assert dt.month == 1
        assert dt.day == 1


class TestAccountAPIIntegration:
    """Integration tests for AccountAPI (would require live connection)."""
    
    @pytest.mark.skip(reason="Requires live cTrader connection")
    async def test_get_full_account_info(self):
        """Test getting full account info."""
        pass
    
    @pytest.mark.skip(reason="Requires live cTrader connection")
    async def test_get_margin_status(self):
        """Test getting margin status."""
        pass
    
    @pytest.mark.skip(reason="Requires live cTrader connection")
    async def test_refresh_cache(self):
        """Test cache refresh."""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
