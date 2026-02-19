#!/usr/bin/env python3
"""
Risk API Debug Script

Tests: get_expected_margin, get_dynamic_leverage, get_margin_calls,
       get_position_pnl, validate_trade_risk, subscribe_margin_events.

Key protobuf facts verified here:
- ProtoOAGetDynamicLeverageByIDReq uses leverageId (not symbolId)
- ProtoOADynamicLeverageTier: volume (cumulative upper bound), leverage (centi-units /100)
- ProtoOAGetPositionUnrealizedPnLRes: positionUnrealizedPnL (repeated), moneyDigits
- ProtoOAMarginCall: marginCallType, marginLevelThreshold, utcLastUpdateTimestamp
"""

import asyncio
import logging
from dotenv import load_dotenv
from ctc import CTraderClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SYMBOLS_TO_TEST = ["XAUUSD", "EURUSD", "BTCUSD", "USDJPY"]


async def main():
    load_dotenv()
    client = CTraderClient.from_env()
    await client.connect()

    logger.info("=" * 60)
    logger.info("⚠️  RISK API DEBUG")
    logger.info("=" * 60)

    try:
        # ── 1. Account leverage ──────────────────────────────────────────
        logger.info("\n🏦 1. Account leverage (from ProtoOATrader.leverageInCents)")
        full_info = await client.account.get_full_account_info()
        logger.info(f"   Account leverage  : 1:{full_info.leverage}")
        logger.info(f"   Balance           : {full_info.balance:.2f} {full_info.currency}")
        logger.info(f"   Equity            : {full_info.equity:.2f}")
        logger.info(f"   Used margin       : {full_info.margin:.2f}")
        logger.info(f"   Free margin       : {full_info.free_margin:.2f}")
        logger.info(f"   Margin level      : {full_info.formatted_margin_level}")

        # ── 2. Expected margin per symbol ────────────────────────────────
        logger.info("\n💰 2. Expected margin (0.01 lots, BUY)")
        for sym_name in SYMBOLS_TO_TEST:
            try:
                m = await client.risk.get_expected_margin(sym_name, 0.01, "BUY")
                logger.info(
                    f"   {sym_name:10s}: buy={m.buy_margin:.4f}  sell={m.sell_margin:.4f}  "
                    f"selected={m.margin:.4f}  money_digits={m.money_digits}"
                )
            except Exception as e:
                logger.warning(f"   {sym_name}: ⚠️ {e}")

        # ── 3. Dynamic leverage tiers ────────────────────────────────────
        logger.info("\n📐 3. Dynamic leverage tiers (leverageId-based lookup)")
        for sym_name in SYMBOLS_TO_TEST:
            try:
                dl = await client.risk.get_dynamic_leverage(sym_name)
                if dl:
                    logger.info(f"   {sym_name} ({len(dl.tiers)} tier(s)):")
                    for t in dl.tiers:
                        vol_to = f"{t.volume_to:.2f}" if t.volume_to else "∞"
                        logger.info(
                            f"     Tier {t.tier_id}: {t.volume_from:.2f}-{vol_to} lots | "
                            f"1:{t.leverage:.0f} | margin={t.margin_percent:.2f}%"
                        )
                    # Test leverage at specific volumes
                    for vol in [0.01, 1.0, 10.0]:
                        lev = dl.get_leverage_for_volume(vol)
                        logger.info(f"     @ {vol} lots → 1:{lev:.0f}")
                else:
                    logger.info(f"   {sym_name}: no dynamic leverage")
            except Exception as e:
                logger.warning(f"   {sym_name}: ⚠️ {e}")

        # ── 4. Margin call thresholds ────────────────────────────────────
        logger.info("\n🚨 4. Margin call thresholds (ProtoOAMarginCallListReq)")
        try:
            calls = await client.risk.get_margin_calls()
            if calls:
                for mc in calls:
                    logger.info(
                        f"   type={mc.margin_call_type}  "
                        f"threshold={mc.margin_level:.1f}%  "
                        f"ts={mc.timestamp}"
                    )
            else:
                logger.info("   No margin call thresholds configured")
        except Exception as e:
            logger.warning(f"   ⚠️ get_margin_calls error: {e}")

        # ── 5. Unrealised PnL (open positions) ───────────────────────────
        logger.info("\n📉 5. Unrealised PnL per position (ProtoOAGetPositionUnrealizedPnLReq)")
        positions = await client.trading.get_positions()
        if positions:
            for pos in positions:
                try:
                    pnl = await client.risk.get_position_pnl_realtime(pos.id)
                    if pnl:
                        logger.info(
                            f"   Position {pos.id} ({pos.symbol_name}): "
                            f"gross={pnl.gross_unrealized_pnl:.2f}  "
                            f"net={pnl.net_unrealized_pnl:.2f}  "
                            f"money_digits={pnl.money_digits}"
                        )
                    else:
                        logger.info(f"   Position {pos.id}: no PnL data returned")
                except Exception as e:
                    logger.warning(f"   Position {pos.id}: ⚠️ {e}")
        else:
            logger.info("   No open positions — skipping realtime PnL")

        # ── 6. Validate trade risk ────────────────────────────────────────
        logger.info("\n✅ 6. Trade risk validation (XAUUSD, 0.01 lots, BUY, max 2%)")
        try:
            val = await client.risk.validate_trade_risk("XAUUSD", 0.01, "BUY", max_risk_percent=2.0)
            logger.info(f"   valid             : {val['valid']}")
            logger.info(f"   margin_required   : {val['margin_required']:.4f}")
            logger.info(f"   margin_available  : {val['margin_available']:.2f}")
            logger.info(f"   margin_sufficient : {val['margin_sufficient']}")
            logger.info(f"   risk_percent      : {val['risk_percent']:.4f}%")
            logger.info(f"   risk_acceptable   : {val['risk_acceptable']}")
            if val['warnings']:
                for w in val['warnings']:
                    logger.warning(f"   ⚠️ {w}")
        except Exception as e:
            logger.warning(f"   ⚠️ validate_trade_risk error: {e}")

        # ── 7. Margin calculation using dynamic leverage ──────────────────
        logger.info("\n📊 7. Manual margin check: XAUUSD 0.01 lots")
        try:
            sym = await client.symbols.get_symbol("XAUUSD")
            dl = await client.risk.get_dynamic_leverage("XAUUSD")
            if sym and dl:
                # Get a live price
                price = None
                try:
                    async with asyncio.timeout(5):
                        async with client.market_data.stream_ticks("XAUUSD") as stream:
                            async for tick in stream:
                                price = tick.ask
                                break
                except asyncio.TimeoutError:
                    price = 3000.0  # fallback

                volume_lots = 0.01
                notional = price * volume_lots * sym.lot_size_units if price else 0
                lev = dl.get_leverage_for_volume(volume_lots)
                margin_calc = notional / lev if lev else 0
                logger.info(f"   Price (ask)       : {price}")
                logger.info(f"   Notional value    : {notional:.2f} USD")
                logger.info(f"   Dynamic leverage  : 1:{lev:.0f}")
                logger.info(f"   Calculated margin : {margin_calc:.4f} USD")
        except Exception as e:
            logger.warning(f"   ⚠️ manual margin calc error: {e}")

        logger.info("\n" + "=" * 60)
        logger.info("✅ Risk API debug complete")

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
