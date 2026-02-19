#!/usr/bin/env python3
"""
Trading API Debug Script

Tests: positions, orders, reconcile, place/close market orders,
       modify position SL/TP, cancel pending orders.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from ctc import CTraderClient
from ctc.enums import TradeSide, TimeFrame

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    load_dotenv()
    client = CTraderClient.from_env()
    await client.connect()

    logger.info("=" * 60)
    logger.info("🔧 TRADING API DEBUG")
    logger.info("=" * 60)

    try:
        # ── 1. Reconcile (open positions + pending orders) ──────────────
        logger.info("\n📋 1. Reconcile (positions + orders)")
        positions = await client.trading.get_positions()
        orders = await client.trading.get_orders()
        logger.info(f"   Open positions : {len(positions)}")
        logger.info(f"   Pending orders : {len(orders)}")

        for pos in positions:
            logger.info(
                f"   POS {pos.id}: {pos.symbol_name} {pos.side} {pos.volume:.4f} lots "
                f"@ {pos.entry_price}, swap={pos.swap:.2f}, comm={pos.commission:.2f}, "
                f"used_margin={pos.used_margin}"
            )

        for ord_ in orders:
            logger.info(
                f"   ORD {ord_.id}: {ord_.symbol_name} {ord_.side} {ord_.volume:.4f} lots "
                f"type={ord_.order_type} status={ord_.status}"
            )

        # ── 2. Volume constraints for XAUUSD ────────────────────────────
        logger.info("\n📐 2. Symbol volume constraints (XAUUSD)")
        sym = await client.symbols.get_symbol("XAUUSD")
        if sym:
            min_v, max_v, step = sym.volume_constraints_lots()
            logger.info(f"   lot_size_units : {sym.lot_size_units}")
            logger.info(f"   min_volume     : {min_v} lots")
            logger.info(f"   max_volume     : {max_v} lots")
            logger.info(f"   step_volume    : {step} lots")
            logger.info(f"   leverage_id    : {sym.leverage_id}")
            proto_vol = sym.lots_to_protocol_volume(0.01)
            logger.info(f"   0.01 lots → proto_volume={proto_vol}")
            back = sym.protocol_volume_to_lots(proto_vol)
            logger.info(f"   proto_volume={proto_vol} → {back:.4f} lots")

        # ── 3. Expected margin for XAUUSD 0.01 lots ─────────────────────
        logger.info("\n💰 3. Expected margin (XAUUSD, 0.01 lots, BUY)")
        try:
            margin_info = await client.risk.get_expected_margin("XAUUSD", 0.01, "BUY")
            logger.info(f"   buy_margin  : {margin_info.buy_margin}")
            logger.info(f"   sell_margin : {margin_info.sell_margin}")
            logger.info(f"   margin      : {margin_info.margin} (selected side)")
            logger.info(f"   money_digits: {margin_info.money_digits}")
        except Exception as e:
            logger.warning(f"   ⚠️ Expected margin error: {e}")

        # ── 4. Place a tiny XAUUSD market order (demo only) ─────────────
        logger.info("\n📤 4. Place market order XAUUSD BUY 0.01 lots (demo)")
        try:
            pos = await client.trading.place_market_order(
                symbol="XAUUSD",
                side=TradeSide.BUY,
                volume=0.01,
            )
            logger.info(f"   ✅ Position opened: id={pos.id}, entry={pos.entry_price}, "
                        f"side={pos.side}, volume={pos.volume}, used_margin={pos.used_margin}")

            # ── 5. Modify SL/TP ─────────────────────────────────────────
            logger.info("\n✏️  5. Modify position SL/TP")
            entry = pos.entry_price
            sl = round(entry * 0.98, 2)
            tp = round(entry * 1.02, 2)
            try:
                await client.trading.modify_position(pos.id, stop_loss=sl, take_profit=tp)
                logger.info(f"   ✅ SL={sl}, TP={tp} set for position {pos.id}")
            except Exception as e:
                logger.warning(f"   ⚠️ modify_position error: {e}")

            # ── 6. Close the position ────────────────────────────────────
            logger.info(f"\n🚪 6. Close position {pos.id}")
            try:
                await client.trading.close_position(pos.id, pos.volume)
                logger.info(f"   ✅ Position {pos.id} close request sent")
            except Exception as e:
                logger.warning(f"   ⚠️ close_position error: {e}")

        except Exception as e:
            logger.warning(f"   ⚠️ place_market_order error: {e}")

        # ── 7. Place + cancel a limit order ─────────────────────────────
        logger.info("\n📋 7. Place EURUSD LIMIT order then cancel")
        try:
            sym_eu = await client.symbols.get_symbol("EURUSD")
            if sym_eu:
                import time as _time
                tick = await asyncio.wait_for(
                    _get_last_tick(client, "EURUSD"), timeout=5
                )
                limit_price = round(tick - 0.0050, 5) if tick else 1.05
                limit_ord = await client.trading.place_limit_order(
                    symbol="EURUSD",
                    side=TradeSide.BUY,
                    volume=0.01,
                    price=limit_price,
                )
                logger.info(f"   ✅ Limit order: id={limit_ord.id}, price={limit_price}")
                await asyncio.sleep(0.5)
                await client.trading.cancel_order(limit_ord.id)
                logger.info(f"   ✅ Limit order {limit_ord.id} cancelled")
        except Exception as e:
            logger.warning(f"   ⚠️ limit order test error: {e}")

        logger.info("\n" + "=" * 60)
        logger.info("✅ Trading API debug complete")

    finally:
        await client.disconnect()


async def _get_last_tick(client, symbol: str) -> float:
    """Quick tick fetch via tick streaming."""
    sym = await client.symbols.get_symbol(symbol)
    if not sym:
        return 0.0
    async with client.market_data.stream_ticks(symbol) as stream:
        async for tick in stream:
            return tick.bid
    return 0.0


if __name__ == "__main__":
    asyncio.run(main())
