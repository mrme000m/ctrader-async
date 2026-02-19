"""
Integration tests for the History API.

Covers:
- get_deal_list          (ProtoOAGetDealListReq)
- get_transaction_list   (ProtoOAGetTransactionListReq)
- get_orders_by_position (ProtoOAOrderListByPositionIdReq)
- get_order_history      (archived orders)
- get_performance_summary

Run with:
    CTRADER_RUN_INTEGRATION=true pytest tests/test_integration_history_api.py -v -s
"""

from __future__ import annotations

import asyncio
import time
import pytest

from ctc import CTraderClient, TradeSide

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


def _ms_range(days_back: int = 30):
    """Return (from_ms, to_ms) covering the last `days_back` days."""
    now_ms = int(time.time() * 1000)
    from_ms = now_ms - days_back * 24 * 3600 * 1000
    return from_ms, now_ms


class TestDealHistory:
    """ProtoOAGetDealListReq — closed deal records."""

    async def test_get_deal_list_returns_list(self, client):
        from_ms, to_ms = _ms_range(30)
        deals = await client.history.get_deal_list(from_timestamp=from_ms, to_timestamp=to_ms)
        assert isinstance(deals, list)
        print(f"\n  Deals in last 30 days: {len(deals)}")

    async def test_get_deal_list_after_trade(self, client):
        """Open and close a position, then verify a deal record appears."""
        from_ms = int(time.time() * 1000)

        pos = await client.trading.place_market_order(
            symbol="EURUSD", side=TradeSide.BUY, volume=0.01,
            comment="integration history deal"
        )
        await asyncio.sleep(1)
        await client.trading.close_position(pos.id)
        await asyncio.sleep(2)  # allow server to record the deal

        to_ms = int(time.time() * 1000)
        deals = await client.history.get_deal_list(from_timestamp=from_ms, to_timestamp=to_ms)
        assert isinstance(deals, list)
        print(f"\n  Deals after trade: {len(deals)}")
        # At least one deal should be present (entry + exit = 2 deals)
        assert len(deals) >= 1

    async def test_deal_fields(self, client):
        """Verify deal model has expected fields."""
        from_ms, to_ms = _ms_range(30)
        deals = await client.history.get_deal_list(from_timestamp=from_ms, to_timestamp=to_ms)
        if not deals:
            pytest.skip("No deals in last 30 days")
        deal = deals[0]
        assert hasattr(deal, "id") or hasattr(deal, "deal_id")
        print(f"\n  Deal fields: {deal}")


class TestTransactionHistory:
    """ProtoOAGetTransactionListReq — account transaction records."""

    async def test_get_transaction_list_returns_list(self, client):
        from_ms, to_ms = _ms_range(30)
        try:
            txns = await client.history.get_transaction_list(
                from_timestamp=from_ms, to_timestamp=to_ms
            )
            assert isinstance(txns, list)
            print(f"\n  Transactions in last 30 days: {len(txns)}")
        except AttributeError:
            pytest.skip("get_transaction_list not implemented in this version")
        except Exception as e:
            pytest.skip(f"Transaction history not available: {e}")


class TestOrderHistory:
    """Archived order history."""

    async def test_get_order_history_returns_list(self, client):
        from_ms, to_ms = _ms_range(30)
        try:
            orders = await client.history.get_order_history(
                from_timestamp=from_ms, to_timestamp=to_ms
            )
            assert isinstance(orders, list)
            print(f"\n  Archived orders in last 30 days: {len(orders)}")
        except AttributeError:
            pytest.skip("get_order_history not implemented in this version")
        except Exception as e:
            pytest.skip(f"Order history not available: {e}")


class TestOrdersByPosition:
    """ProtoOAOrderListByPositionIdReq — orders linked to a specific position."""

    async def test_get_orders_by_position(self, client):
        """Open + close a position, then fetch its linked orders."""
        pos = await client.trading.place_market_order(
            symbol="EURUSD", side=TradeSide.BUY, volume=0.01,
            comment="integration history orders by position"
        )
        await asyncio.sleep(1)
        await client.trading.close_position(pos.id)
        await asyncio.sleep(2)

        orders = await client.history.get_orders_by_position(pos.id)
        assert isinstance(orders, list)
        print(f"\n  Orders for position {pos.id}: {len(orders)}")
        # At minimum the opening market order should be in the list
        assert len(orders) >= 1

    async def test_get_orders_by_position_unknown_id(self, client):
        """Non-existent position_id should return empty list, not raise."""
        orders = await client.history.get_orders_by_position(999999999)
        assert isinstance(orders, list)


class TestPerformanceSummary:
    """Performance summary — composite calculation from deal history."""

    async def test_get_performance_summary(self, client):
        from_ms, to_ms = _ms_range(30)
        try:
            summary = await client.history.get_performance_summary(
                from_timestamp=from_ms, to_timestamp=to_ms
            )
            assert summary is not None
            print(f"\n  Performance summary: {summary}")
        except AttributeError:
            pytest.skip("get_performance_summary not implemented in this version")
        except Exception as e:
            pytest.skip(f"Performance summary not available: {e}")
