"""
Integration tests for the Risk Management API.

Covers:
- get_expected_margin
- get_position_pnl / get_position_pnl_realtime
- get_dynamic_leverage
- get_margin_calls
- update_margin_call
- validate_trade_risk
- subscribe_margin_events  (unsubscribe handle)
- subscribe_margin_call_events (unsubscribe handle)

Run with:
    CTRADER_RUN_INTEGRATION=true pytest tests/test_integration_risk_api.py -v -s
"""

from __future__ import annotations

import asyncio
import pytest

from ctc import CTraderClient, TradeSide
from ctc.models import MarginInfo, PositionPnL

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


class TestExpectedMargin:
    """ProtoOAExpectedMarginReq — margin estimate before placing a trade."""

    async def test_expected_margin_eurusd_buy(self, client):
        margin = await client.risk.get_expected_margin("EURUSD", 0.01, "BUY")
        assert isinstance(margin, MarginInfo)
        assert margin.margin > 0
        assert margin.symbol_id > 0
        assert margin.money_digits >= 2
        print(f"\n  EURUSD 0.01 BUY margin: {margin.formatted_margin}")

    async def test_expected_margin_sell_side(self, client):
        margin = await client.risk.get_expected_margin("EURUSD", 0.01, "SELL")
        assert margin.margin > 0

    async def test_expected_margin_larger_volume(self, client):
        margin_small = await client.risk.get_expected_margin("EURUSD", 0.01)
        margin_large = await client.risk.get_expected_margin("EURUSD", 0.10)
        # Larger volume must require at least as much margin
        assert margin_large.margin >= margin_small.margin

    async def test_expected_margin_invalid_symbol_raises(self, client):
        with pytest.raises(Exception):
            await client.risk.get_expected_margin("NOSUCHSYMBOL_XYZ", 1.0)


class TestPositionPnL:
    """Position PnL via trading positions + server realtime query."""

    async def test_get_position_pnl(self, client):
        """Open a position, fetch PnL, close it."""
        pos = await client.trading.place_market_order(
            symbol="EURUSD", side=TradeSide.BUY, volume=0.01,
            comment="integration risk pnl"
        )
        await asyncio.sleep(1)

        pnl = await client.risk.get_position_pnl(pos.id)
        assert pnl is not None
        assert isinstance(pnl, PositionPnL)
        assert pnl.position_id == pos.id
        # Gross PnL should be a real number (could be negative)
        assert isinstance(pnl.gross_unrealized_pnl, float)
        assert pnl.total_costs >= 0
        print(f"\n  PnL: gross={pnl.formatted_gross_pnl}  net={pnl.formatted_net_pnl}")

        await client.trading.close_position(pos.id)

    async def test_get_position_pnl_realtime(self, client):
        """Server-calculated unrealized PnL via ProtoOAGetPositionUnrealizedPnLReq."""
        pos = await client.trading.place_market_order(
            symbol="EURUSD", side=TradeSide.BUY, volume=0.01,
            comment="integration risk pnl realtime"
        )
        await asyncio.sleep(1)

        try:
            pnl = await client.risk.get_position_pnl_realtime(pos.id)
            if pnl is not None:
                assert isinstance(pnl.gross_unrealized_pnl, float)
                print(f"\n  Realtime gross PnL: {pnl.formatted_gross_pnl}")
            else:
                # Some brokers do not return this; acceptable
                pytest.skip("Broker did not return realtime PnL for this position")
        except Exception as e:
            # ProtoOA may not support this endpoint on all accounts
            pytest.skip(f"get_position_pnl_realtime not supported: {e}")
        finally:
            await client.trading.close_position(pos.id)

    async def test_get_position_pnl_unknown_returns_none(self, client):
        """Non-existent position_id must return None."""
        pnl = await client.risk.get_position_pnl(999999999)
        assert pnl is None


class TestDynamicLeverage:
    """ProtoOAGetDynamicLeverageByIDReq."""

    async def test_get_dynamic_leverage_eurusd(self, client):
        lev = await client.risk.get_dynamic_leverage("EURUSD")
        if lev is None:
            pytest.skip("Broker does not provide dynamic leverage for EURUSD")
        assert lev.symbol_id > 0
        assert len(lev.tiers) > 0
        for tier in lev.tiers:
            assert tier.leverage > 0
        print(f"\n  EURUSD leverage tiers: {len(lev.tiers)}")
        for t in lev.tiers:
            print(f"    {t}")

    async def test_leverage_for_volume(self, client):
        lev = await client.risk.get_dynamic_leverage("EURUSD")
        if lev is None:
            pytest.skip("Dynamic leverage not available")
        lev_val = lev.get_leverage_for_volume(1.0)
        assert lev_val > 0


class TestMarginCalls:
    """ProtoOAMarginCallListReq."""

    async def test_get_margin_calls_returns_list(self, client):
        calls = await client.risk.get_margin_calls()
        assert isinstance(calls, list)
        # May be empty on a healthy demo account — that's fine
        print(f"\n  Margin calls: {len(calls)}")
        for mc in calls:
            print(f"    {mc.margin_call_type}: level={mc.formatted_margin_level}")


class TestUpdateMarginCall:
    """ProtoOAMarginCallUpdateReq."""

    async def test_update_margin_call_threshold(self, client):
        """Set a margin call threshold — broker may reject on demo; skip if so."""
        try:
            await client.risk.update_margin_call("MARGIN_CALL", 100.0)
            print("\n  Margin call threshold updated to 100%")
        except Exception as e:
            pytest.skip(f"update_margin_call rejected by broker: {e}")


class TestValidateTradingRisk:
    """validate_trade_risk — composite risk check."""

    async def test_validate_acceptable_risk(self, client):
        result = await client.risk.validate_trade_risk(
            symbol="EURUSD", volume=0.01, side="BUY", max_risk_percent=100.0
        )
        assert "valid" in result
        assert "margin_required" in result
        assert "margin_available" in result
        assert "margin_sufficient" in result
        assert "risk_percent" in result
        assert "risk_acceptable" in result
        assert "warnings" in result
        assert result["margin_required"] > 0
        assert result["margin_available"] > 0
        print(f"\n  validate_trade_risk: valid={result['valid']}  risk={result['risk_percent']:.2f}%")

    async def test_validate_very_large_volume_fails(self, client):
        """A huge volume should fail margin check on a demo account."""
        result = await client.risk.validate_trade_risk(
            symbol="EURUSD", volume=1000.0, side="BUY", max_risk_percent=2.0
        )
        # Either margin insufficient or risk too high
        assert not result["valid"] or len(result["warnings"]) > 0


class TestMarginEventSubscription:
    """subscribe_margin_events / subscribe_margin_call_events wiring."""

    async def test_subscribe_margin_events_returns_unsubscribe(self, client):
        """Verify the subscribe call returns a callable unsubscribe handle."""
        calls: list = []
        unsub = client.risk.subscribe_margin_events(
            lambda pos_id, margin, digits: calls.append((pos_id, margin, digits))
        )
        assert callable(unsub)
        # Unsubscribe should not raise
        unsub()

    async def test_subscribe_margin_call_events_returns_unsubscribe(self, client):
        unsub = client.risk.subscribe_margin_call_events(
            lambda etype, eq, mg, lvl: None
        )
        assert callable(unsub)
        unsub()

    async def test_margin_event_fires_on_position_open(self, client):
        """
        Open a position — the broker should push a ProtoOAMarginChangedEvent
        which the client converts to risk.margin_changed on the event bus.
        """
        events: list = []
        unsub = client.risk.subscribe_margin_events(
            lambda pos_id, margin, digits: events.append((pos_id, margin))
        )

        pos = await client.trading.place_market_order(
            symbol="EURUSD", side=TradeSide.BUY, volume=0.01,
            comment="integration risk margin event"
        )

        # Wait up to 5 s for the server-push event
        for _ in range(50):
            if events:
                break
            await asyncio.sleep(0.1)

        unsub()
        await client.trading.close_position(pos.id)

        if not events:
            pytest.skip(
                "ProtoOAMarginChangedEvent not received within 5 s "
                "(broker may not push this on demo)"
            )

        pos_id, used_margin = events[0]
        assert pos_id > 0
        assert used_margin >= 0
        print(f"\n  Margin changed: pos={pos_id}  used_margin={used_margin:.2f}")
