#!/usr/bin/env python3
"""
Account and Leverage Debug Script

This script fetches comprehensive account information and leverage details
for all available symbols, providing a complete overview of account capabilities.
"""

import asyncio
import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from ctc import CTraderClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class AccountLeverageDebugger:
    """Debug class for comprehensive account and leverage information."""
    
    def __init__(self):
        self.client = None
        self.account_info = None
        self.full_account_info = None
        self.symbols = []
        
    async def authenticate(self):
        """Authenticate using .env file credentials."""
        logger.info("🔐 Authenticating with cTrader API...")
        
        try:
            # Load environment variables
            load_dotenv()
            
            # Create client from environment variables
            self.client = CTraderClient.from_env()
            
            # Connect and authenticate
            await self.client.connect()
            
            logger.info("✅ Authentication successful!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            return False
    
    async def get_account_info(self):
        """Get comprehensive account information."""
        logger.info("📊 Fetching account information...")
        
        try:
            # Get basic account info
            self.account_info = await self.client.account.get_info()
            logger.info("✅ Basic Account Info:")
            currency = self.account_info.currency or "USD"
            logger.info(f"   Account ID: {self.account_info.account_id}")
            logger.info(f"   Currency: {currency}")
            logger.info(f"   Balance: {self.account_info.balance:.2f} {currency}")
            logger.info(f"   Equity: {self.account_info.equity:.2f} {currency}")
            logger.info(f"   Margin Used: {self.account_info.margin:.2f} {currency}")
            logger.info(f"   Margin Free: {self.account_info.free_margin:.2f} {currency}")
            margin_level = self.account_info.margin_level or 0
            leverage = self.account_info.leverage or "N/A"
            account_type = self.account_info.account_type or "N/A"
            logger.info(f"   Margin Level: {margin_level:.2f}%")
            logger.info(f"   Leverage: {leverage}")
            logger.info(f"   Account Type: {account_type}")
            
            # Get full account info with additional details
            self.full_account_info = await self.client.account.get_full_account_info()
            logger.info("\n✅ Full Account Info:")
            currency = self.full_account_info.currency
            account_type = self.full_account_info.account_type
            leverage = self.full_account_info.leverage or "N/A"
            unrealized_pnl = self.full_account_info.unrealized_pnl or 0
            realized_pnl = self.full_account_info.realized_pnl or 0
            swap = self.full_account_info.swap or 0
            commission = self.full_account_info.commission or 0
            last_update = self.full_account_info.last_update_datetime or "N/A"
            
            logger.info(f"   Account ID: {self.full_account_info.account_id}")
            logger.info(f"   Account Type: {account_type}")
            logger.info(f"   Leverage: {leverage}")
            logger.info(f"   Balance: {self.full_account_info.balance:.2f} {currency}")
            logger.info(f"   Equity: {self.full_account_info.equity:.2f} {currency}")
            logger.info(f"   Margin Used: {self.full_account_info.margin:.2f} {currency}")
            logger.info(f"   Margin Free: {self.full_account_info.free_margin:.2f} {currency}")
            margin_level = self.full_account_info.margin_level or 0
            logger.info(f"   Margin Level: {margin_level:.2f}%")
            logger.info(f"   Unrealized PnL: {unrealized_pnl:.2f} {currency}")
            logger.info(f"   Realized PnL: {realized_pnl:.2f} {currency}")
            logger.info(f"   Swap: {swap:.2f} {currency}")
            logger.info(f"   Commission: {commission:.2f} {currency}")
            logger.info(f"   Last Update: {last_update}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to get account info: {e}")
            return False
    
    async def get_all_symbols(self):
        """Get all available symbols."""
        logger.info("📈 Fetching all available symbols...")
        
        try:
            self.symbols = await self.client.symbols.get_all()
            logger.info(f"✅ Found {len(self.symbols)} symbols")
            
            # Group symbols by category
            categories = {}
            for symbol in self.symbols:
                category = symbol.category_name or "Unknown"
                if category not in categories:
                    categories[category] = []
                categories[category].append(symbol)
            
            logger.info(f"📂 Symbol Categories:")
            for category, symbols in sorted(categories.items()):
                logger.info(f"   {category}: {len(symbols)} symbols")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to get symbols: {e}")
            return False
    
    async def analyze_leverage_by_category(self):
        """Analyze leverage information by symbol category."""
        logger.info("⚖️ Analyzing leverage by symbol category...")
        
        try:
            # Group symbols by category and filter out those without leverage data
            categories = {}
            for symbol in self.symbols:
                category = symbol.category_name or "Unknown"
                if category not in categories:
                    categories[category] = {
                        'symbols': [],
                        'leverage_ids': [],
                    }

                # Only include symbols with a leverage schedule ID
                if symbol.leverage_id is not None:
                    categories[category]['symbols'].append(symbol)
                    categories[category]['leverage_ids'].append(symbol.leverage_id)

            # Analyze each category
            for category, data in sorted(categories.items()):
                symbols = data['symbols']
                leverage_ids = data['leverage_ids']

                if not symbols:  # Skip categories with no valid symbols
                    continue

                unique_schedules = len(set(leverage_ids))

                logger.info(f"\n📊 {category} Category Analysis:")
                logger.info(f"   Total Symbols with Leverage Schedule: {len(symbols)}")
                logger.info(f"   Unique Leverage Schedules: {unique_schedules}")

                # Show first 5 symbols with their leverage schedule IDs
                logger.info(f"   Sample Symbols:")
                for symbol in symbols[:5]:
                    logger.info(f"     {symbol.name}: leverage_id={symbol.leverage_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze leverage by category: {e}")
            return False
    
    async def get_dynamic_leverage_for_popular_symbols(self):
        """Get dynamic leverage information for popular symbols."""
        logger.info("🔄 Fetching dynamic leverage for popular symbols...")
        
        # Popular symbols to check
        popular_symbols = [
            'XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD',
            'US30', 'SPX500', 'NAS100', 'BTCUSD', 'ETHUSD'
        ]
        
        for symbol_name in popular_symbols:
            try:
                # Get symbol info
                symbol = await self.client.symbols.get_symbol(symbol_name)
                if not symbol:
                    logger.warning(f"⚠️ Symbol {symbol_name} not found")
                    continue
                
                logger.info(f"\n🔍 {symbol_name} Dynamic Leverage Analysis:")
                logger.info(f"   Leverage Schedule ID: {symbol.leverage_id}")
                
                # Get dynamic leverage tiers
                try:
                    dynamic_leverage = await self.client.risk.get_dynamic_leverage(symbol_name)
                    if dynamic_leverage:
                        logger.info(f"   Dynamic Leverage Tiers:")
                        max_leverage = 0
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
                    else:
                        logger.info(f"   No dynamic leverage tiers available")
                        
                except Exception as e:
                    logger.warning(f"   ⚠️ Could not fetch dynamic leverage: {e}")
                
            except Exception as e:
                logger.error(f"❌ Failed to analyze {symbol_name}: {e}")
    
    async def get_margin_status(self):
        """Get current margin status and risk metrics."""
        logger.info("💰 Fetching margin status and risk metrics...")
        
        try:
            margin_status = await self.client.account.get_margin_status()
            logger.info("✅ Margin Status:")
            logger.info(f"   Balance: {margin_status.get('balance', 'N/A')}")
            logger.info(f"   Equity: {margin_status.get('equity', 'N/A')}")
            logger.info(f"   Margin Used: {margin_status.get('margin_used', 'N/A')}")
            logger.info(f"   Margin Free: {margin_status.get('margin_free', 'N/A')}")
            logger.info(f"   Margin Level: {margin_status.get('margin_level', 'N/A')}%")
            logger.info(f"   Margin Call Level: {margin_status.get('margin_call_level', 'N/A')}%")
            logger.info(f"   Stop Out Level: {margin_status.get('stop_out_level', 'N/A')}%")
            
            # Calculate risk metrics
            if self.full_account_info:
                margin_level = self.full_account_info.margin_level or 0
                
                logger.info("\n🚨 Risk Assessment:")
                if margin_level == 0:
                    logger.info("   ℹ️ No open positions - margin level not applicable")
                elif margin_level < 50:  # Typical stop-out level
                    logger.warning("   ⚠️ CRITICAL: Account is below stop-out level!")
                elif margin_level < 100:  # Typical margin call level
                    logger.warning("   ⚠️ WARNING: Account is at margin call level!")
                elif margin_level < 200:  # Safe buffer
                    logger.info("   ⚠️ CAUTION: Account is approaching margin call level")
                else:
                    logger.info("   ✅ Account margin level is healthy")
                
                logger.info(f"   Current Margin Level: {margin_level:.2f}%")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to get margin status: {e}")
            return False
    
    async def cleanup(self):
        """Clean up resources."""
        if self.client:
            try:
                await self.client.disconnect()
                logger.info("✅ Disconnected from cTrader API")
            except Exception as e:
                logger.error(f"❌ Error during cleanup: {e}")
    
    async def run_debug_sequence(self):
        """Run the complete debug sequence."""
        logger.info("🚀 Starting Account and Leverage Debug Sequence")
        logger.info("=" * 60)
        
        try:
            # Step 1: Authenticate
            if not await self.authenticate():
                return False
            
            # Step 2: Get account information
            if not await self.get_account_info():
                return False
            
            # Step 3: Get all symbols
            if not await self.get_all_symbols():
                return False
            
            # Step 4: Analyze leverage by category
            if not await self.analyze_leverage_by_category():
                return False
            
            # Step 5: Get dynamic leverage for popular symbols
            await self.get_dynamic_leverage_for_popular_symbols()
            
            # Step 6: Get margin status
            if not await self.get_margin_status():
                return False
            
            logger.info("\n" + "=" * 60)
            logger.info("✅ Account and Leverage Debug Sequence Completed Successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Debug sequence failed: {e}")
            return False
        
        finally:
            await self.cleanup()

async def main():
    """Main function to run the account and leverage debugger."""
    debugger = AccountLeverageDebugger()
    success = await debugger.run_debug_sequence()
    
    if success:
        logger.info("🎉 All account and leverage information retrieved successfully!")
    else:
        logger.error("💥 Failed to retrieve complete account and leverage information")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())