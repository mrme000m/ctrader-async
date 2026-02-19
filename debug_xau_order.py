#!/usr/bin/env python3
"""
Debug Script: XAUUSD Market Order with Margin Calculation

This script:
1. Authenticates using .env file credentials
2. Fetches XAUUSD symbol information
3. Gets account leverage information
4. Calculates margin required for minimum XAUUSD order
5. Places the actual market order

Usage:
    python debug_xau_order.py
"""

import asyncio
import logging
import os
from decimal import Decimal
from typing import Optional

from dotenv import load_dotenv

from ctc import CTraderClient, TradeSide
from ctc.models import Symbol, MarginInfo

# Load environment variables from .env file
load_dotenv()


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class XAUOrderDebugger:
    """Debug class for XAUUSD order placement with margin calculation."""
    
    def __init__(self):
        self.client: Optional[CTraderClient] = None
        self.symbol: Optional[Symbol] = None
        self.account_info = None
        
    async def authenticate(self):
        """Authenticate using .env file credentials."""
        logger.info("🔐 Authenticating with cTrader API...")
        
        try:
            # Check environment variables first
            logger.info(f"Environment variables:")
            logger.info(f"  CTRADER_CLIENT_ID: {os.getenv('CTRADER_CLIENT_ID', 'NOT SET')}")
            logger.info(f"  CTRADER_CLIENT_SECRET: {'SET' if os.getenv('CTRADER_CLIENT_SECRET') else 'NOT SET'}")
            logger.info(f"  CTRADER_ACCESS_TOKEN: {'SET' if os.getenv('CTRADER_ACCESS_TOKEN') else 'NOT SET'}")
            logger.info(f"  CTRADER_ACCOUNT_ID: {os.getenv('CTRADER_ACCOUNT_ID', 'NOT SET')}")
            logger.info(f"  CTRADER_HOST_TYPE: {os.getenv('CTRADER_HOST_TYPE', 'NOT SET')}")
            
            # Use from_env() to load credentials from .env file
            self.client = CTraderClient.from_env()
            
            # Test the connection by entering the context
            await self.client.__aenter__()
            
            logger.info("✅ Successfully authenticated")
            return True
            
        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            return False
    
    async def get_account_info(self):
        """Get account information including leverage."""
        logger.info("📊 Fetching account information...")
        
        try:
            self.account_info = await self.client.account.get_info()
            
            logger.info(f"✅ Account Info:")
            logger.info(f"   Account ID: {self.account_info.account_id}")
            logger.info(f"   Balance: {self.account_info.balance:.2f}")
            logger.info(f"   Equity: {self.account_info.equity:.2f}")
            logger.info(f"   Free Margin: {self.account_info.free_margin:.2f}")
            logger.info(f"   Account Type: {self.account_info.account_type}")
            
            return self.account_info
            
        except Exception as e:
            logger.error(f"❌ Failed to get account info: {e}")
            return None
    
    async def get_xauusd_symbol_info(self):
        """Fetch XAUUSD symbol information."""
        logger.info("🔍 Fetching XAUUSD symbol information...")
        
        try:
            # Get symbol from catalog
            self.symbol = await self.client.symbols.get_symbol("XAUUSD")
            
            logger.info(f"✅ XAUUSD Symbol Info:")
            logger.info(f"   Symbol ID: {self.symbol.id}")
            logger.info(f"   Symbol Name: {self.symbol.name}")
            logger.info(f"   Description: {self.symbol.description}")
            logger.info(f"   Digits: {self.symbol.digits}")
            logger.info(f"   Pip Size: {self.symbol.pip_size}")
            logger.info(f"   Price Tick Size: {self.symbol.price_tick_size}")
            logger.info(f"   Lot Size: {self.symbol.lot_size_units}")
            
            # Get volume constraints in lots
            min_lot, max_lot, step_lot = self.symbol.volume_constraints_lots()
            logger.info(f"   Min Volume: {min_lot} lots")
            logger.info(f"   Max Volume: {max_lot} lots")
            logger.info(f"   Volume Step: {step_lot} lots")
            logger.info(f"   Leverage: {self.symbol.leverage}")
            logger.info(f"   Margin Rate: {self.symbol.margin_rate}")
            
            return self.symbol
            
        except Exception as e:
            logger.error(f"❌ Failed to get XAUUSD symbol info: {e}")
            return None
    
    async def get_leverage_info(self):
        """Get leverage information for XAUUSD including dynamic leverage tiers."""
        logger.info("⚖️ Fetching leverage information for XAUUSD...")
        
        try:
            # Get symbol leverage info
            if self.symbol:
                logger.info(f"✅ XAUUSD Basic Leverage Info:")
                logger.info(f"   Symbol Leverage: {self.symbol.leverage}")
                logger.info(f"   Margin Rate: {self.symbol.margin_rate}")
                
                # Get dynamic leverage tiers
                try:
                    dynamic_leverage = await self.client.risk.get_dynamic_leverage("XAUUSD")
                    if dynamic_leverage:
                        logger.info(f"✅ Dynamic Leverage Tiers for XAUUSD:")
                        logger.info(f"   Symbol ID: {dynamic_leverage.symbol_id}")
                        logger.info(f"   Symbol Name: {dynamic_leverage.symbol_name}")
                        logger.info(f"   Total Volume: {dynamic_leverage.total_volume}")
                        
                        max_leverage = 0
                        logger.info(f"   Leverage Tiers:")
                        for i, tier in enumerate(dynamic_leverage.tiers):
                            volume_to = tier.volume_to if tier.volume_to else "∞"
                            logger.info(f"     Tier {i+1}: {tier.volume_from} - {volume_to} lots | "
                                       f"Leverage: 1:{tier.leverage} | Margin: {tier.margin_percent:.2f}%")
                            if tier.leverage > max_leverage:
                                max_leverage = tier.leverage
                        
                        logger.info(f"   🎯 MAXIMUM LEVERAGE: 1:{max_leverage}")
                        
                        # Test leverage for different volumes
                        test_volumes = [0.001, 0.01, 0.1, 1.0, 5.0]
                        logger.info(f"   Applied Leverage by Volume:")
                        for volume in test_volumes:
                            leverage = dynamic_leverage.get_leverage_for_volume(volume)
                            logger.info(f"     {volume} lots: 1:{leverage}")
                        
                        return dynamic_leverage, max_leverage
                    else:
                        logger.warning(f"⚠️  No dynamic leverage data available for XAUUSD")
                        return None, self.symbol.leverage or 100.0
                        
                except Exception as e:
                    logger.warning(f"⚠️  Failed to get dynamic leverage: {e}")
                    return None, self.symbol.leverage or 100.0
            
        except Exception as e:
            logger.error(f"❌ Failed to get leverage info: {e}")
            return None, 100.0
    
    async def calculate_margin_for_min_order(self, dynamic_leverage=None, max_leverage=100.0):
        """Calculate margin required for minimum XAUUSD order using highest leverage."""
        logger.info("💰 Calculating margin for minimum XAUUSD order...")
        
        if not self.symbol:
            logger.error("❌ Symbol information not available")
            return None
            
        try:
            # Use minimum volume for the symbol
            min_lot, max_lot, step_lot = self.symbol.volume_constraints_lots()
            min_volume = min_lot if min_lot else 0.01
            logger.info(f"   Minimum volume: {min_volume} lots")
            
            # Calculate smallest possible order using maximum leverage
            if self.account_info and self.account_info.free_margin > 0:
                logger.info(f"   🎯 Using maximum leverage: 1:{max_leverage}")
                
                # Calculate theoretical minimum volume based on available margin and max leverage
                # This is a rough calculation - actual margin may vary due to other factors
                current_price = await self._get_current_price("XAUUSD")
                if current_price:
                    # For XAUUSD, 1 lot = 100 oz of gold
                    # Notional value = volume * lot_size * price
                    # Margin = notional_value / leverage
                    
                    lot_size = self.symbol.lot_size_units  # Usually 100000 for XAUUSD (100 oz in cents)
                    notional_per_lot = lot_size * current_price / 100  # Convert cents to dollars
                    
                    # Calculate minimum volume we can afford with max leverage
                    min_volume_possible = (self.account_info.free_margin * max_leverage) / notional_per_lot
                    logger.info(f"   Current XAUUSD Price: ${current_price:.2f}")
                    logger.info(f"   Notional Value per Lot: ${notional_per_lot:.2f}")
                    logger.info(f"   Theoretical Minimum Volume (max leverage): {min_volume_possible:.6f} lots")
                    
                    # Test progressively smaller volumes to find the minimum affordable
                    test_volumes = [0.001, 0.0005, 0.0001, 0.00005, 0.00001]
                    affordable_volume = None
                    
                    logger.info(f"   Testing affordable volumes with max leverage:")
                    for test_vol in test_volumes:
                        try:
                            test_margin = await self.client.risk.get_expected_margin("XAUUSD", test_vol)
                            if test_margin.margin <= self.account_info.free_margin:
                                affordable_volume = test_vol
                                logger.info(f"     ✅ {test_vol} lots: {test_margin.formatted_margin} (AFFORDABLE)")
                                break
                            else:
                                logger.info(f"     ❌ {test_vol} lots: {test_margin.formatted_margin} (too expensive)")
                        except:
                            logger.info(f"     ❌ {test_vol} lots: Error calculating margin")
                    
                    if affordable_volume:
                        logger.info(f"   💡 SMALLEST AFFORDABLE VOLUME: {affordable_volume} lots")
                        min_volume = affordable_volume
                    else:
                        logger.info(f"   💡 No volume tested is affordable even with maximum leverage")
                else:
                    logger.warning(f"⚠️  Could not get current price for XAUUSD")
            
            # Calculate expected margin for the determined volume
            margin_info = await self.client.risk.get_expected_margin("XAUUSD", min_volume)
            
            logger.info(f"✅ Final Margin Calculation:")
            logger.info(f"   Volume: {min_volume} lots")
            logger.info(f"   Required Margin: {margin_info.formatted_margin}")
            logger.info(f"   Buy Margin: {margin_info.buy_margin:.2f}" if margin_info.buy_margin else "   Buy Margin: N/A")
            logger.info(f"   Sell Margin: {margin_info.sell_margin:.2f}" if margin_info.sell_margin else "   Sell Margin: N/A")
            
            # Check if we have enough margin
            if self.account_info:
                margin_pct = (margin_info.margin / self.account_info.free_margin * 100) if self.account_info.free_margin > 0 else 0
                logger.info(f"   % of Free Margin: {margin_pct:.2f}%")
                
                if margin_info.margin > self.account_info.free_margin:
                    logger.warning(f"⚠️  Insufficient margin! Required: {margin_info.formatted_margin}, Available: {self.account_info.free_margin:.2f}")
                else:
                    logger.info(f"✅ Sufficient margin available")
            
            return margin_info, min_volume
            
        except Exception as e:
            logger.error(f"❌ Failed to calculate margin: {e}")
            return None, min_volume if 'min_volume' in locals() else 0.01
    
    async def _get_current_price(self, symbol):
        """Get current price for a symbol."""
        try:
            # Try to get current price from market data
            ticker = await self.client.market_data.get_symbol_tick(symbol)
            if ticker and hasattr(ticker, 'bid'):
                return (ticker.bid + ticker.ask) / 2  # Return mid price
        except:
            pass
        
        # Fallback: try to get from symbol info or use default
        if symbol == "XAUUSD":
            return 2000.0  # Rough fallback price for gold
        return None
    
    async def place_market_order(self, volume=None):
        """Place the actual market order for XAUUSD with specified volume."""
        logger.info("📈 Placing XAUUSD market order...")
        
        if not self.symbol:
            logger.error("❌ Symbol information not available")
            return None
            
        try:
            # Use provided volume or determine minimum
            if volume is None:
                min_lot, max_lot, step_lot = self.symbol.volume_constraints_lots()
                volume = min_lot if min_lot else 0.01
            
            # Final margin check before placing order
            if self.account_info:
                try:
                    margin_check = await self.client.risk.get_expected_margin("XAUUSD", volume)
                    if margin_check.margin > self.account_info.free_margin:
                        logger.error(f"❌ Cannot afford {volume} lots (requires {margin_check.formatted_margin}, have {self.account_info.free_margin:.2f})")
                        return None
                    else:
                        logger.info(f"✅ Margin check passed: {margin_check.formatted_margin} required, {self.account_info.free_margin:.2f} available")
                except Exception as e:
                    logger.warning(f"⚠️  Could not verify margin for order: {e}")
            
            side = TradeSide.BUY  # You can change this to SELL if needed
            
            logger.info(f"   Placing {side} order for {volume} lots of XAUUSD...")
            
            # Place the market order
            position = await self.client.trading.place_market_order(
                symbol="XAUUSD",
                side=side,
                volume=volume,
                comment="Debug script - XAUUSD market order"
            )
            
            logger.info(f"✅ Order placed successfully!")
            logger.info(f"   Position ID: {position.position_id}")
            logger.info(f"   Symbol: {position.symbol_name if hasattr(position, 'symbol_name') else 'XAUUSD'}")
            logger.info(f"   Side: {position.trade_side if hasattr(position, 'trade_side') else 'BUY'}")
            logger.info(f"   Volume: {position.volume_in_lots if hasattr(position, 'volume_in_lots') else volume}")
            logger.info(f"   Entry Price: {position.execution_price if hasattr(position, 'execution_price') else 'N/A'}")
            logger.info(f"   Stop Loss: {position.stop_loss if hasattr(position, 'stop_loss') else 'N/A'}")
            logger.info(f"   Take Profit: {position.take_profit if hasattr(position, 'take_profit') else 'N/A'}")
            logger.info(f"   Commission: {position.commission if hasattr(position, 'commission') else 'N/A'}")
            logger.info(f"   Swap: {position.swap if hasattr(position, 'swap') else 'N/A'}")
            logger.info(f"   Profit: {position.gross_pnl if hasattr(position, 'gross_pnl') else 'N/A'}")
            logger.info(f"   Comment: {position.comment if hasattr(position, 'comment') else 'Debug script - XAUUSD market order'}")
            
            return position
            
        except Exception as e:
            logger.error(f"❌ Failed to place market order: {e}")
            return None
    
    async def cleanup(self):
        """Clean up resources."""
        if self.client:
            try:
                await self.client.__aexit__(None, None, None)
                logger.info("✅ Client connection closed")
            except Exception as e:
                logger.error(f"❌ Error closing client: {e}")
    
    async def run_debug_sequence(self):
        """Run the complete debug sequence."""
        logger.info("🚀 Starting XAUUSD Order Debug Sequence")
        logger.info("=" * 50)
        
        try:
            # Step 1: Authenticate
            if not await self.authenticate():
                return False
            
            # Step 2: Get account info
            if not await self.get_account_info():
                return False
            
            # Step 3: Get XAUUSD symbol info
            if not await self.get_xauusd_symbol_info():
                return False
            
            # Step 4: Get leverage info
            dynamic_leverage, max_leverage = await self.get_leverage_info()
            
            # Step 5: Calculate margin for minimum order using max leverage
            margin_result = await self.calculate_margin_for_min_order(dynamic_leverage, max_leverage)
            if not margin_result:
                return False
            margin_info, min_volume = margin_result
            
            # Step 6: Place market order with calculated minimum volume
            position = await self.place_market_order(min_volume)
            # Note: position can be None due to insufficient margin, which is still a successful debug
            
            logger.info("=" * 50)
            logger.info("🎉 Debug sequence completed successfully!")
            logger.info("📋 SUMMARY:")
            logger.info("   ✅ Authentication: SUCCESS")
            logger.info("   ✅ Account Info: RETRIEVED")
            logger.info("   ✅ XAUUSD Symbol Info: RETRIEVED")
            logger.info("   ✅ Dynamic Leverage Analysis: COMPLETED")
            logger.info("   ✅ Margin Calculation: COMPLETED")
            if position:
                logger.info("   ✅ Order Placement: SUCCESS")
            else:
                logger.info("   ❌ Order Placement: INSUFFICIENT MARGIN")
            logger.info("")
            logger.info("💡 CONCLUSION:")
            if position:
                logger.info("   XAUUSD order placed successfully!")
                logger.info(f"   Position ID: {position.position_id}")
                logger.info(f"   Volume: {position.volume_in_lots if hasattr(position, 'volume_in_lots') else min_volume} lots")
                logger.info(f"   Entry Price: ${position.execution_price if hasattr(position, 'execution_price') else 'N/A'}")
            else:
                logger.info("   The account balance is insufficient to trade XAUUSD even with maximum leverage.")
                if max_leverage:
                    logger.info(f"   Maximum leverage available: 1:{max_leverage}")
                logger.info(f"   Smallest affordable volume tested: {min_volume if 'min_volume' in locals() else 'N/A'} lots")
                logger.info(f"   Available balance: ${self.account_info.free_margin:.2f}" if self.account_info else "N/A")
            logger.info("")
            logger.info("🔧 RECOMMENDATIONS:")
            if position:
                logger.info("   Monitor the position and manage risk appropriately")
            else:
                logger.info("   1. Add more funds to the account")
                logger.info("   2. Try trading symbols with lower margin requirements")
                logger.info("   3. Use a higher leverage account if available")
            return True
            
        except Exception as e:
            logger.error(f"❌ Debug sequence failed: {e}")
            return False
        
        finally:
            await self.cleanup()


async def main():
    """Main function to run the debug script."""
    debugger = XAUOrderDebugger()
    success = await debugger.run_debug_sequence()
    
    if success:
        logger.info("✅ Script completed successfully")
    else:
        logger.error("❌ Script failed")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)