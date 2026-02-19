#!/usr/bin/env python3
"""
Session & Assets API Debug Script

Tests: get_available_accounts, get_server_version, get_ctid_profile,
       refresh_token, get_all assets, get_asset_classes,
       symbol catalog (search, categories, get_symbol_details_by_id).
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
    logger.info("🔑 SESSION & ASSETS API DEBUG")
    logger.info("=" * 60)

    try:
        # ── 1. Server version ────────────────────────────────────────────
        logger.info("\n🌐 1. Server version")
        version = await client.session.get_server_version()
        logger.info(f"   Server version: {version}")

        # ── 2. Available accounts ────────────────────────────────────────
        logger.info("\n👤 2. Available accounts (ProtoOAGetAccountListByAccessTokenReq)")
        accounts = await client.session.get_available_accounts()
        logger.info(f"   Found {len(accounts)} account(s)")
        for acc in accounts:
            logger.info(
                f"   Account {acc.account_id}: type={acc.account_type} "
                f"live={acc.is_live} trader_login={acc.broker_name}"
            )

        # ── 3. cTID profile ──────────────────────────────────────────────
        logger.info("\n👤 3. cTID profile (ProtoOAGetCtidProfileByTokenReq)")
        try:
            profile = await client.session.get_ctid_profile()
            logger.info(f"   user_id: {profile.get('user_id')}")
            logger.info(f"   (note: only userId is available in ProtoOACtidProfile)")
        except Exception as e:
            logger.warning(f"   ⚠️ ctid profile error: {e}")

        # ── 4. Assets ────────────────────────────────────────────────────
        logger.info("\n💱 4. Assets (ProtoOAAssetListReq)")
        assets = await client.assets.get_all()
        logger.info(f"   Total assets: {len(assets)}")
        # Show sample assets
        sample = [a for a in assets if a.name in ('USD', 'EUR', 'GBP', 'JPY', 'XAU', 'BTC')]
        for a in sample:
            logger.info(f"   Asset {a.id}: name={a.name} display={a.display_name} digits={a.digits}")

        # ── 5. Asset classes ─────────────────────────────────────────────
        logger.info("\n🏷️  5. Asset classes (ProtoOAAssetClassListReq)")
        try:
            classes = await client.assets.get_asset_classes()
            logger.info(f"   Total asset classes: {len(classes)}")
            for cls in classes[:5]:
                logger.info(f"   Class {cls.id}: {cls.name}")
        except Exception as e:
            logger.warning(f"   ⚠️ get_asset_classes error: {e}")

        # ── 6. Symbol catalog ────────────────────────────────────────────
        logger.info("\n📋 6. Symbol catalog")
        all_symbols = await client.symbols.get_all()
        logger.info(f"   Total symbols: {len(all_symbols)}")

        # Symbols with leverage_id
        with_lid = [s for s in all_symbols if s.leverage_id is not None]
        logger.info(f"   Symbols with leverage_id: {len(with_lid)}")

        # Search
        results = await client.symbols.search("XAU")
        logger.info(f"   Search 'XAU': {[s.name for s in results[:5]]}")

        # ── 7. Full symbol details (ProtoOASymbolByIdReq) ────────────────
        logger.info("\n🔍 7. Full symbol details (XAUUSD, ProtoOASymbolByIdReq)")
        sym = await client.symbols.get_symbol("XAUUSD")
        if sym:
            full = await client.symbols.get_symbol_details_by_id(sym.id)
            if full:
                logger.info(f"   id            : {full.id}")
                logger.info(f"   name          : {full.name}")
                logger.info(f"   digits        : {full.digits}")
                logger.info(f"   pip_position  : {full.pip_position}")
                logger.info(f"   pip_size      : {full.pip_size}")
                logger.info(f"   lot_size_units: {full.lot_size_units}")
                logger.info(f"   leverage_id   : {full.leverage_id}")
                min_v, max_v, step = full.volume_constraints_lots()
                logger.info(f"   min/max/step  : {min_v} / {max_v} / {step} lots")
                logger.info(f"   swap_long     : {full.swap_long}")
                logger.info(f"   swap_short    : {full.swap_short}")

        # ── 8. Symbol categories ─────────────────────────────────────────
        logger.info("\n📂 8. Symbol categories (ProtoOASymbolCategoryListReq)")
        try:
            cats = await client.symbols.get_categories()
            logger.info(f"   Categories: {cats[:10]}")
        except Exception as e:
            logger.warning(f"   ⚠️ get_categories error: {e}")

        logger.info("\n" + "=" * 60)
        logger.info("✅ Session & Assets API debug complete")

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
