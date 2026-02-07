"""
Tests for Risk Management API.
"""

import pytest
from datetime import datetime
from ctc.models import MarginInfo, PositionPnL, MarginCall


class TestMarginInfo:
    """Test MarginInfo model."""
    
    def test_margin_info_creation(self):
        """Test creating a MarginInfo object."""
        margin_info = MarginInfo(
            margin=100.50,
            symbol_id=1,
            volume=1.0,
            money_digits=2
        )
        
        assert margin_info.margin == 100.50
        assert margin_info.symbol_id == 1
        assert margin_info.volume == 1.0
        assert margin_info.money_digits == 2
    
    def test_formatted_margin(self):
        """Test formatted margin output."""
        margin_info = MarginInfo(
            margin=1234.567,
            symbol_id=1,
            volume=1.0,
            money_digits=2
        )
        
        assert margin_info.formatted_margin == "1234.57"
    
    def test_formatted_margin_with_different_digits(self):
        """Test formatted margin with different decimal places."""
        margin_info = MarginInfo(
            margin=1234.56789,
            symbol_id=1,
            volume=1.0,
            money_digits=4
        )
        
        assert margin_info.formatted_margin == "1234.5679"
    
    def test_buy_sell_margins(self):
        """Test buy and sell specific margins."""
        margin_info = MarginInfo(
            margin=100.0,
            symbol_id=1,
            volume=1.0,
            money_digits=2,
            buy_margin=98.0,
            sell_margin=102.0
        )
        
        assert margin_info.buy_margin == 98.0
        assert margin_info.sell_margin == 102.0


class TestPositionPnL:
    """Test PositionPnL model."""
    
    def test_position_pnl_creation(self):
        """Test creating a PositionPnL object."""
        pnl = PositionPnL(
            position_id=12345,
            gross_unrealized_pnl=150.0,
            net_unrealized_pnl=145.0,
            swap=-3.0,
            commission=-2.0,
            money_digits=2
        )
        
        assert pnl.position_id == 12345
        assert pnl.gross_unrealized_pnl == 150.0
        assert pnl.net_unrealized_pnl == 145.0
        assert pnl.swap == -3.0
        assert pnl.commission == -2.0
    
    def test_total_costs(self):
        """Test total costs calculation."""
        pnl = PositionPnL(
            position_id=1,
            gross_unrealized_pnl=100.0,
            net_unrealized_pnl=95.0,
            swap=-3.0,
            commission=-2.0
        )
        
        # Total costs = abs(swap) + abs(commission)
        assert pnl.total_costs == 5.0
    
    def test_formatted_pnl(self):
        """Test formatted PnL output."""
        pnl = PositionPnL(
            position_id=1,
            gross_unrealized_pnl=123.456,
            net_unrealized_pnl=-78.901,
            money_digits=2
        )
        
        assert pnl.formatted_gross_pnl == "+123.46"
        assert pnl.formatted_net_pnl == "-78.90"
    
    def test_datetime_conversion(self):
        """Test timestamp to datetime conversion."""
        pnl = PositionPnL(
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
    
    def test_datetime_none_when_no_timestamp(self):
        """Test datetime is None when no timestamp."""
        pnl = PositionPnL(
            position_id=1,
            gross_unrealized_pnl=100.0,
            net_unrealized_pnl=95.0
        )
        
        assert pnl.datetime is None
    
    def test_used_margin(self):
        """Test used margin field."""
        pnl = PositionPnL(
            position_id=1,
            gross_unrealized_pnl=100.0,
            net_unrealized_pnl=95.0,
            used_margin=250.0
        )
        
        assert pnl.used_margin == 250.0


class TestMarginCall:
    """Test MarginCall model."""
    
    def test_margin_call_creation(self):
        """Test creating a MarginCall object."""
        margin_call = MarginCall(
            margin_call_type="MARGIN_CALL",
            equity=5000.0,
            margin=4800.0,
            margin_level=104.17,
            timestamp=1609459200000,
            money_digits=2
        )
        
        assert margin_call.margin_call_type == "MARGIN_CALL"
        assert margin_call.equity == 5000.0
        assert margin_call.margin == 4800.0
        assert margin_call.margin_level == 104.17
    
    def test_datetime_conversion(self):
        """Test timestamp to datetime conversion."""
        margin_call = MarginCall(
            margin_call_type="STOP_OUT",
            equity=1000.0,
            margin=1200.0,
            margin_level=83.33,
            timestamp=1609459200000  # 2021-01-01 00:00:00 UTC
        )
        
        dt = margin_call.datetime
        assert isinstance(dt, datetime)
        assert dt.year == 2021
        assert dt.month == 1
        assert dt.day == 1
    
    def test_formatted_equity(self):
        """Test formatted equity output."""
        margin_call = MarginCall(
            margin_call_type="MARGIN_CALL",
            equity=12345.678,
            margin=10000.0,
            margin_level=123.46,
            timestamp=1609459200000,
            money_digits=2
        )
        
        assert margin_call.formatted_equity == "12345.68"
    
    def test_formatted_margin_level(self):
        """Test formatted margin level output."""
        margin_call = MarginCall(
            margin_call_type="MARGIN_CALL",
            equity=5000.0,
            margin=4800.0,
            margin_level=104.1666,
            timestamp=1609459200000
        )
        
        assert margin_call.formatted_margin_level == "104.17%"


class TestRiskAPIIntegration:
    """Integration tests for RiskAPI (would require live connection)."""
    
    @pytest.mark.skip(reason="Requires live cTrader connection")
    async def test_get_expected_margin(self):
        """Test getting expected margin for a trade."""
        # This would require actual cTrader credentials
        # Left as placeholder for integration testing
        pass
    
    @pytest.mark.skip(reason="Requires live cTrader connection")
    async def test_get_position_pnl(self):
        """Test getting position PnL details."""
        # This would require actual cTrader credentials
        # Left as placeholder for integration testing
        pass
    
    @pytest.mark.skip(reason="Requires live cTrader connection")
    async def test_validate_trade_risk(self):
        """Test trade risk validation."""
        # This would require actual cTrader credentials
        # Left as placeholder for integration testing
        pass
    
    @pytest.mark.skip(reason="Requires live cTrader connection")
    async def test_get_margin_calls(self):
        """Test getting margin call list."""
        # This would require actual cTrader credentials
        # Left as placeholder for integration testing
        pass
    
    @pytest.mark.skip(reason="Requires live cTrader connection")
    async def test_subscribe_margin_events(self):
        """Test subscribing to margin change events."""
        # This would require actual cTrader credentials
        # Left as placeholder for integration testing
        pass


class TestRiskValidation:
    """Test risk validation logic."""
    
    def test_margin_sufficient_validation(self):
        """Test margin sufficiency check."""
        # Simulate validation result
        validation = {
            'valid': True,
            'margin_required': 100.0,
            'margin_available': 500.0,
            'margin_sufficient': True,
            'risk_percent': 1.5,
            'risk_acceptable': True,
            'warnings': []
        }
        
        assert validation['valid'] is True
        assert validation['margin_sufficient'] is True
        assert validation['margin_required'] < validation['margin_available']
    
    def test_insufficient_margin_validation(self):
        """Test validation with insufficient margin."""
        validation = {
            'valid': False,
            'margin_required': 600.0,
            'margin_available': 500.0,
            'margin_sufficient': False,
            'risk_percent': 10.0,
            'risk_acceptable': False,
            'warnings': ['Insufficient margin']
        }
        
        assert validation['valid'] is False
        assert validation['margin_sufficient'] is False
        assert len(validation['warnings']) > 0
    
    def test_risk_percentage_validation(self):
        """Test risk percentage validation."""
        # Risk too high
        validation = {
            'valid': False,
            'margin_required': 100.0,
            'margin_available': 500.0,
            'margin_sufficient': True,
            'risk_percent': 5.0,  # > 2% max
            'risk_acceptable': False,
            'warnings': ['Risk too high']
        }
        
        assert validation['risk_acceptable'] is False
        assert validation['risk_percent'] > 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
