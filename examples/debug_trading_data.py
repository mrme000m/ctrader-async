#!/usr/bin/env python3
"""
Comprehensive debug script for all deals, positions, and orders related code.

This script provides detailed debugging information for:
- Open positions with P&L and risk metrics
- Pending orders with status and execution details
- Historical deals with performance analysis
- Position-specific deals and orders
- Cash flow history and account transactions
- Performance summary and trading statistics
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
import sys

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")

from ctc import CTraderClient
from ctc.models import Position, Order, Deal
from ctc.api.account import FullAccountInfo, CashFlowEntry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TradingDataDebugger:
    """Comprehensive debugger for trading data (positions, orders, deals)."""
    
    def __init__(self):
        """Initialize the debugger."""
        self.client: Optional[CTraderClient] = None
        self.account_info: Optional[FullAccountInfo] = None
    
    async def authenticate(self) -> bool:
        """Authenticate using .env file credentials."""
        try:
            print("🔐 Authenticating with cTrader...")
            self.client = CTraderClient.from_env()
            await self.client.connect()
            
            # Get account info
            self.account_info = await self.client.account.get_full_account_info()
            print(f"✅ Connected to account {self.account_info.account_id}")
            print(f"   Balance: {self.account_info.balance:.2f} {self.account_info.currency}")
            print(f"   Equity: {self.account_info.equity:.2f} {self.account_info.currency}")
            print(f"   Margin: {self.account_info.margin:.2f} {self.account_info.currency}")
            print(f"   Free Margin: {self.account_info.free_margin:.2f} {self.account_info.currency}")
            if self.account_info.margin_level:
                print(f"   Margin Level: {self.account_info.margin_level:.2f}%")
            
            return True
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            logger.error("Authentication failed", exc_info=True)
            return False
    
    async def debug_open_positions(self) -> None:
        """Debug all open positions with detailed information."""
        print("\n" + "="*80)
        print("📊 DEBUG: OPEN POSITIONS")
        print("="*80)
        
        try:
            positions = await self.client.trading.get_positions()
            
            if not positions:
                print("📭 No open positions found")
                return
            
            print(f"📈 Found {len(positions)} open position(s):")
            
            for i, pos in enumerate(positions, 1):
                print(f"\n--- Position {i} ---")
                print(f"ID: {pos.id}")
                print(f"Symbol: {pos.symbol_name or 'Unknown'} (ID: {pos.symbol_id})")
                print(f"Side: {pos.side}")
                print(f"Volume: {pos.volume} lots")
                print(f"Entry Price: {pos.entry_price}")
                
                if pos.current_price:
                    print(f"Current Price: {pos.current_price}")
                    price_diff = pos.current_price - pos.entry_price
                    if pos.side == "BUY":
                        price_change_pct = (price_diff / pos.entry_price) * 100
                    else:
                        price_change_pct = -(price_diff / pos.entry_price) * 100
                    print(f"Price Change: {price_diff:.5f} ({price_change_pct:.2f}%)")
                
                print(f"Gross P&L: {pos.pnl_gross_unrealized:.2f}")
                print(f"Net P&L: {pos.pnl_net_unrealized:.2f}")
                print(f"Commission: {pos.commission:.2f}")
                print(f"Swap: {pos.swap:.2f}")
                
                if pos.used_margin:
                    print(f"Used Margin: {pos.used_margin:.2f}")
                
                if pos.stop_loss:
                    print(f"Stop Loss: {pos.stop_loss}")
                if pos.take_profit:
                    print(f"Take Profit: {pos.take_profit}")
                
                print(f"Status: {pos.status or 'Unknown'}")
                
                if pos.open_timestamp:
                    open_time = datetime.fromtimestamp(pos.open_timestamp / 1000.0, tz=timezone.utc)
                    duration = datetime.now(timezone.utc) - open_time
                    print(f"Open Time: {open_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                    print(f"Duration: {duration}")
                
                if pos.last_update_timestamp:
                    update_time = datetime.fromtimestamp(pos.last_update_timestamp / 1000.0, tz=timezone.utc)
                    print(f"Last Update: {update_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                
                # Calculate risk metrics
                if self.account_info and self.account_info.equity > 0:
                    risk_pct = (abs(pos.pnl_net_unrealized) / self.account_info.equity) * 100
                    print(f"Risk as % of Equity: {risk_pct:.2f}%")
            
        except Exception as e:
            print(f"❌ Error debugging positions: {e}")
            logger.error("Error debugging positions", exc_info=True)
    
    async def debug_pending_orders(self) -> None:
        """Debug all pending orders with detailed information."""
        print("\n" + "="*80)
        print("📋 DEBUG: PENDING ORDERS")
        print("="*80)
        
        try:
            orders = await self.client.trading.get_orders()
            
            if not orders:
                print("📭 No pending orders found")
                return
            
            print(f"📋 Found {len(orders)} pending order(s):")
            
            for i, order in enumerate(orders, 1):
                print(f"\n--- Order {i} ---")
                print(f"ID: {order.id}")
                print(f"Symbol: {order.symbol_name or 'Unknown'} (ID: {order.symbol_id})")
                print(f"Side: {order.side}")
                print(f"Volume: {order.volume} lots")
                print(f"Type: {order.order_type or 'Unknown'}")
                print(f"Status: {order.status or 'Unknown'}")
                print(f"Time in Force: {order.time_in_force or 'Unknown'}")
                
                if order.limit_price:
                    print(f"Limit Price: {order.limit_price}")
                if order.stop_price:
                    print(f"Stop Price: {order.stop_price}")
                if order.stop_loss:
                    print(f"Stop Loss: {order.stop_loss}")
                if order.take_profit:
                    print(f"Take Profit: {order.take_profit}")
                
                if order.trailing_stop is not None:
                    print(f"Trailing Stop: {order.trailing_stop}")
                if order.guaranteed_stop_loss is not None:
                    print(f"Guaranteed Stop Loss: {order.guaranteed_stop_loss}")
                
                if order.expiration_timestamp:
                    exp_time = datetime.fromtimestamp(order.expiration_timestamp / 1000.0, tz=timezone.utc)
                    print(f"Expiration: {exp_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                    
                    time_to_exp = exp_time - datetime.now(timezone.utc)
                    if time_to_exp.total_seconds() > 0:
                        print(f"Time to Expiration: {time_to_exp}")
                    else:
                        print("⚠️ Order has expired")
                
                if order.create_timestamp:
                    create_time = datetime.fromtimestamp(order.create_timestamp / 1000.0, tz=timezone.utc)
                    duration = datetime.now(timezone.utc) - create_time
                    print(f"Create Time: {create_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                    print(f"Duration: {duration}")
                
                if order.last_update_timestamp:
                    update_time = datetime.fromtimestamp(order.last_update_timestamp / 1000.0, tz=timezone.utc)
                    print(f"Last Update: {update_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                
                if order.client_order_id:
                    print(f"Client Order ID: {order.client_order_id}")
                if order.label:
                    print(f"Label: {order.label}")
                if order.comment:
                    print(f"Comment: {order.comment}")
            
        except Exception as e:
            print(f"❌ Error debugging orders: {e}")
            logger.error("Error debugging orders", exc_info=True)
    
    async def debug_deals_history(self, days: int = 7) -> None:
        """Debug recent deals history with performance analysis."""
        print(f"\n" + "="*80)
        print(f"💼 DEBUG: DEALS HISTORY (Last {days} days)")
        print("="*80)
        
        try:
            deals = await self.client.history.get_deals(days=days)
            
            if not deals:
                print("📭 No deals found in the specified period")
                return
            
            print(f"💼 Found {len(deals)} deal(s) in the last {days} days:")
            
            # Calculate summary statistics
            total_volume = 0
            total_commission = 0
            total_swap = 0
            total_pnl = 0
            profitable_deals = 0
            losing_deals = 0
            
            symbol_stats = {}
            
            for i, deal in enumerate(deals, 1):
                print(f"\n--- Deal {i} ---")
                print(f"Deal ID: {deal.deal_id}")
                print(f"Position ID: {deal.position_id or 'Unknown'}")
                print(f"Order ID: {deal.order_id or 'Unknown'}")
                print(f"Symbol: {deal.symbol_name or 'Unknown'} (ID: {deal.symbol_id})")
                print(f"Side: {deal.side}")
                print(f"Volume: {deal.volume} lots")
                print(f"Execution Price: {deal.execution_price}")
                print(f"Commission: {deal.commission:.2f}")
                print(f"Swap: {deal.swap:.2f}")
                print(f"P&L: {deal.pnl:.2f}")
                
                if deal.timestamp:
                    exec_time = datetime.fromtimestamp(deal.timestamp / 1000.0, tz=timezone.utc)
                    print(f"Execution Time: {exec_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                
                # Update statistics
                if deal.volume:
                    total_volume += deal.volume
                total_commission += deal.commission
                total_swap += deal.swap
                total_pnl += deal.pnl
                
                if deal.pnl > 0:
                    profitable_deals += 1
                elif deal.pnl < 0:
                    losing_deals += 1
                
                # Symbol-specific statistics
                symbol = deal.symbol_name or 'Unknown'
                if symbol not in symbol_stats:
                    symbol_stats[symbol] = {
                        'volume': 0,
                        'pnl': 0,
                        'deals': 0,
                        'profitable': 0,
                        'losing': 0
                    }
                
                if deal.volume:
                    symbol_stats[symbol]['volume'] += deal.volume
                symbol_stats[symbol]['pnl'] += deal.pnl
                symbol_stats[symbol]['deals'] += 1
                
                if deal.pnl > 0:
                    symbol_stats[symbol]['profitable'] += 1
                elif deal.pnl < 0:
                    symbol_stats[symbol]['losing'] += 1
            
            # Print summary statistics
            print(f"\n📊 SUMMARY STATISTICS:")
            print(f"Total Volume: {total_volume:.2f} lots")
            print(f"Total Commission: {total_commission:.2f}")
            print(f"Total Swap: {total_swap:.2f}")
            print(f"Total P&L: {total_pnl:.2f}")
            print(f"Profitable Deals: {profitable_deals}")
            print(f"Losing Deals: {losing_deals}")
            
            if len(deals) > 0:
                win_rate = (profitable_deals / len(deals)) * 100
                avg_pnl = total_pnl / len(deals)
                print(f"Win Rate: {win_rate:.2f}%")
                print(f"Average P&L per Deal: {avg_pnl:.2f}")
            
            # Symbol-specific summary
            if symbol_stats:
                print(f"\n📈 PERFORMANCE BY SYMBOL:")
                for symbol, stats in symbol_stats.items():
                    print(f"\n{symbol}:")
                    print(f"  Volume: {stats['volume']:.2f} lots")
                    print(f"  P&L: {stats['pnl']:.2f}")
                    print(f"  Deals: {stats['deals']}")
                    print(f"  Profitable: {stats['profitable']}")
                    print(f"  Losing: {stats['losing']}")
                    if stats['deals'] > 0:
                        symbol_win_rate = (stats['profitable'] / stats['deals']) * 100
                        avg_symbol_pnl = stats['pnl'] / stats['deals']
                        print(f"  Win Rate: {symbol_win_rate:.2f}%")
                        print(f"  Avg P&L: {avg_symbol_pnl:.2f}")
            
        except Exception as e:
            print(f"❌ Error debugging deals history: {e}")
            logger.error("Error debugging deals history", exc_info=True)
    
    async def debug_position_specific_data(self) -> None:
        """Debug position-specific deals and orders."""
        print("\n" + "="*80)
        print("🎯 DEBUG: POSITION-SPECIFIC DATA")
        print("="*80)
        
        try:
            positions = await self.client.trading.get_positions()
            
            if not positions:
                print("📭 No open positions to analyze")
                return
            
            for pos in positions:
                print(f"\n--- Analysis for Position {pos.id} ({pos.symbol_name}) ---")
                
                # Get deals for this position
                try:
                    position_deals = await self.client.history.get_deals_by_position(pos.id)
                    print(f"📦 Deals for Position {pos.id}: {len(position_deals)}")
                    
                    for i, deal in enumerate(position_deals, 1):
                        print(f"  Deal {i}: ID={deal.deal_id}, Volume={deal.volume}, Price={deal.execution_price}, P&L={deal.pnl:.2f}")
                        if deal.timestamp:
                            deal_time = datetime.fromtimestamp(deal.timestamp / 1000.0, tz=timezone.utc)
                            print(f"    Time: {deal_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                
                except Exception as e:
                    print(f"  ❌ Error getting deals for position {pos.id}: {e}")
                
                # Get orders for this position
                try:
                    position_orders = await self.client.trading.get_orders_by_position(pos.id)
                    print(f"📋 Orders for Position {pos.id}: {len(position_orders)}")
                    
                    for i, order in enumerate(position_orders, 1):
                        print(f"  Order {i}: ID={order.id}, Type={order.order_type}, Status={order.status}, Volume={order.volume}")
                        if order.create_timestamp:
                            order_time = datetime.fromtimestamp(order.create_timestamp / 1000.0, tz=timezone.utc)
                            print(f"    Created: {order_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                
                except Exception as e:
                    print(f"  ❌ Error getting orders for position {pos.id}: {e}")
            
        except Exception as e:
            print(f"❌ Error debugging position-specific data: {e}")
            logger.error("Error debugging position-specific data", exc_info=True)
    
    async def debug_cash_flow_history(self, days: int = 30) -> None:
        """Debug cash flow history and account transactions."""
        print(f"\n" + "="*80)
        print(f"💰 DEBUG: CASH FLOW HISTORY (Last {days} days)")
        print("="*80)
        
        try:
            cash_flows = await self.client.account.get_cash_flow_history(days=days)
            
            if not cash_flows:
                print("📭 No cash flow entries found in the specified period")
                return
            
            print(f"💰 Found {len(cash_flows)} cash flow entry(ies) in the last {days} days:")
            
            # Calculate summary by type
            summary = {}
            total_deposits = 0
            total_withdrawals = 0
            total_commissions = 0
            total_swaps = 0
            
            for i, entry in enumerate(cash_flows, 1):
                print(f"\n--- Cash Flow {i} ---")
                print(f"Entry ID: {entry.entry_id}")
                print(f"Type: {entry.type.value}")
                print(f"Amount: {entry.formatted_amount}")
                print(f"Balance After: {entry.balance_after:.2f}")
                
                if entry.timestamp:
                    entry_time = datetime.fromtimestamp(entry.timestamp / 1000.0, tz=timezone.utc)
                    print(f"Time: {entry_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                
                if entry.description:
                    print(f"Description: {entry.description}")
                
                # Update summary
                if entry.type.value not in summary:
                    summary[entry.type.value] = {'count': 0, 'total': 0}
                summary[entry.type.value]['count'] += 1
                summary[entry.type.value]['total'] += entry.amount
                
                if entry.type.value == "DEPOSIT":
                    total_deposits += entry.amount
                elif entry.type.value == "WITHDRAWAL":
                    total_withdrawals += abs(entry.amount)
                elif entry.type.value == "COMMISSION":
                    total_commissions += abs(entry.amount)
                elif entry.type.value == "SWAP":
                    total_swaps += abs(entry.amount)
            
            # Print summary
            print(f"\n📊 CASH FLOW SUMMARY:")
            for flow_type, data in summary.items():
                print(f"{flow_type}: {data['count']} entries, Total: {data['total']:.2f}")
            
            print(f"\n💵 NET MOVEMENTS:")
            print(f"Total Deposits: {total_deposits:.2f}")
            print(f"Total Withdrawals: {total_withdrawals:.2f}")
            print(f"Total Commissions: {total_commissions:.2f}")
            print(f"Total Swaps: {total_swaps:.2f}")
            print(f"Net Cash Flow: {total_deposits - total_withdrawals:.2f}")
            
        except Exception as e:
            if "Unexpected response type" in str(e):
                print("⚠️ Cash flow history API is not available on this account/server")
                print("   This is a common limitation on demo accounts or certain brokers")
            else:
                print(f"❌ Error debugging cash flow history: {e}")
            logger.error("Error debugging cash flow history", exc_info=True)
    
    async def debug_performance_summary(self, days: int = 30) -> None:
        """Debug performance summary and trading statistics."""
        print(f"\n" + "="*80)
        print(f"📈 DEBUG: PERFORMANCE SUMMARY (Last {days} days)")
        print("="*80)
        
        try:
            # Get performance summary
            perf_summary = await self.client.history.get_performance_summary(days=days)
            
            if not perf_summary:
                print("📭 No performance data available for the specified period")
                return
            
            print("📈 PERFORMANCE SUMMARY:")
            for key, value in perf_summary.items():
                if isinstance(value, float):
                    print(f"{key}: {value:.2f}")
                else:
                    print(f"{key}: {value}")
            
            # Additional analysis with deals data
            deals = await self.client.history.get_deals(days=days)
            if deals:
                print(f"\n📊 DETAILED ANALYSIS (based on {len(deals)} deals):")
                
                # Calculate various metrics
                total_pnl = sum(deal.pnl for deal in deals)
                total_volume = sum(deal.volume or 0 for deal in deals)
                profitable_deals = [d for d in deals if d.pnl > 0]
                losing_deals = [d for d in deals if d.pnl < 0]
                
                print(f"Total P&L: {total_pnl:.2f}")
                print(f"Total Volume: {total_volume:.2f} lots")
                print(f"Number of Deals: {len(deals)}")
                print(f"Profitable Deals: {len(profitable_deals)}")
                print(f"Losing Deals: {len(losing_deals)}")
                
                if len(deals) > 0:
                    win_rate = (len(profitable_deals) / len(deals)) * 100
                    avg_pnl = total_pnl / len(deals)
                    print(f"Win Rate: {win_rate:.2f}%")
                    print(f"Average P&L per Deal: {avg_pnl:.2f}")
                
                if profitable_deals:
                    avg_win = sum(d.pnl for d in profitable_deals) / len(profitable_deals)
                    max_win = max(d.pnl for d in profitable_deals)
                    print(f"Average Win: {avg_win:.2f}")
                    print(f"Maximum Win: {max_win:.2f}")
                
                if losing_deals:
                    avg_loss = sum(d.pnl for d in losing_deals) / len(losing_deals)
                    max_loss = min(d.pnl for d in losing_deals)
                    print(f"Average Loss: {avg_loss:.2f}")
                    print(f"Maximum Loss: {max_loss:.2f}")
                
                if profitable_deals and losing_deals:
                    profit_factor = sum(d.pnl for d in profitable_deals) / abs(sum(d.pnl for d in losing_deals))
                    print(f"Profit Factor: {profit_factor:.2f}")
            
        except Exception as e:
            print(f"❌ Error debugging performance summary: {e}")
            logger.error("Error debugging performance summary", exc_info=True)
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            if self.client:
                await self.client.disconnect()
                print("🔌 Disconnected from cTrader")
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            logger.error("Error during cleanup", exc_info=True)
    
    async def run_complete_debug(self) -> None:
        """Run the complete debugging sequence."""
        print("🚀 Starting comprehensive trading data debugging...")
        
        try:
            # Authenticate
            if not await self.authenticate():
                return
            
            # Run all debugging functions
            await self.debug_open_positions()
            await self.debug_pending_orders()
            await self.debug_deals_history(days=7)
            await self.debug_position_specific_data()
            await self.debug_cash_flow_history(days=30)
            await self.debug_performance_summary(days=30)
            
            print("\n" + "="*80)
            print("✅ COMPLETE DEBUGGING FINISHED")
            print("="*80)
            
        except Exception as e:
            print(f"❌ Error during debugging: {e}")
            logger.error("Error during debugging", exc_info=True)
        
        finally:
            await self.cleanup()


async def main():
    """Main function to run the trading data debugger."""
    debugger = TradingDataDebugger()
    await debugger.run_complete_debug()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Debugging interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)