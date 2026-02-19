#!/usr/bin/env python3
"""
History API Debug Script

Tests: get_deals, get_deals_by_position, get_order_details,
       get_orders_by_position, get_deal_offsets, get_performance_summary.
"""

import asyncio
import logging
from dotenv import load_dotenv
from ctc import CTraderClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    load_dotenv()
    client = CTraderClient.from_env()
    await client.connect()

    logger.info("=" * 60)
    logger.info("📜 HISTORY API DEBUG")
    logger.info("=" * 60)

    try:
        # ── 1. Get recent deals ─────────────────────────────────────────
        logger.info("\n📊 1. Recent deals (last 30 days)")
        deals = await client.history.get_deals(days=30)
        logger.info(f"   Total deals: {len(deals)}")
        for deal in deals[:5]:
            logger.info(
                f"   Deal {deal.deal_id}: {deal.symbol_name} {deal.side} "
                f"vol={deal.volume} @ {deal.execution_price} "
                f"pnl={deal.pnl:.2f} comm={deal.commission:.2f} swap={deal.swap:.2f} "
                f"ts={deal.timestamp}"
            )

        # ── 2. Deals by position (use first deal's position_id) ─────────
        if deals and deals[0].position_id:
            pos_id = deals[0].position_id
            logger.info(f"\n🔍 2. Deals by position {pos_id}")
            pos_deals = await client.history.get_deals_by_position(pos_id)
            logger.info(f"   Deals for position {pos_id}: {len(pos_deals)}")
            for d in pos_deals:
                logger.info(f"   Deal {d.deal_id}: side={d.side} vol={d.volume} @ {d.execution_price}")
        else:
            logger.info("\n🔍 2. Deals by position — skipped (no deals found)")

        # ── 3. Order details (use first deal's order_id) ────────────────
        if deals and deals[0].order_id:
            ord_id = deals[0].order_id
            logger.info(f"\n📋 3. Order details for order {ord_id}")
            order = await client.history.get_order_details(ord_id)
            if order:
                logger.info(f"   id={order.id} type={order.order_type} status={order.status} "
                            f"side={order.side} vol={order.volume} "
                            f"lp={order.limit_price} sp={order.stop_price} "
                            f"sl={order.stop_loss} tp={order.take_profit}")
            else:
                logger.info("   Order not found")
        else:
            logger.info("\n📋 3. Order details — skipped (no orders found)")

        # ── 4. Orders by position ────────────────────────────────────────
        if deals and deals[0].position_id:
            pos_id = deals[0].position_id
            logger.info(f"\n📋 4. Orders by position {pos_id}")
            pos_orders = await client.history.get_orders_by_position(pos_id)
            logger.info(f"   Orders for position {pos_id}: {len(pos_orders)}")
            for o in pos_orders[:3]:
                logger.info(f"   Order {o.id}: {o.order_type} {o.status} {o.side} {o.volume}")
        else:
            logger.info("\n📋 4. Orders by position — skipped")

        # ── 5. Deal offsets (use first deal id) ─────────────────────────
        if deals:
            deal_id = deals[0].deal_id
            logger.info(f"\n🔗 5. Deal offsets for deal {deal_id}")
            try:
                offsets = await client.history.get_deal_offsets(deal_id)
                logger.info(f"   Offsets: {len(offsets)}")
                for off in offsets:
                    logger.info(f"   Offset: open={off.open_deal_id} close={off.close_deal_id} "
                                f"vol={off.volume:.4f} ts={off.timestamp}")
            except Exception as e:
                logger.warning(f"   ⚠️ get_deal_offsets error: {e}")
        else:
            logger.info("\n🔗 5. Deal offsets — skipped (no deals)")

        # ── 6. Performance summary ───────────────────────────────────────
        logger.info("\n📈 6. Performance summary (last 30 days)")
        summary = await client.history.get_performance_summary(days=30)
        logger.info(f"   Total deals    : {summary['total_deals']}")
        logger.info(f"   Winning deals  : {summary['winning_deals']}")
        logger.info(f"   Losing deals   : {summary['losing_deals']}")
        logger.info(f"   Win rate       : {summary['win_rate']:.1f}%")
        logger.info(f"   Total PnL      : {summary['total_pnl']:.2f}")
        logger.info(f"   Total commission: {summary['total_commission']:.2f}")
        logger.info(f"   Total swap     : {summary['total_swap']:.2f}")
        logger.info(f"   Net PnL        : {summary['net_pnl']:.2f}")
        logger.info(f"   Avg win        : {summary['avg_win']:.2f}")
        logger.info(f"   Avg loss       : {summary['avg_loss']:.2f}")
        logger.info(f"   Profit factor  : {summary['profit_factor']:.2f}")

        logger.info("\n" + "=" * 60)
        logger.info("✅ History API debug complete")

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
