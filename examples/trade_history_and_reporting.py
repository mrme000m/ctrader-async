"""
Example: Trade History and Reporting

This example demonstrates how to use the History API for:
- Retrieving deal/trade history
- Position-specific deal tracking
- Performance analysis and reporting
- Order details retrieval
- Trade reconciliation

Use cases:
- Performance tracking and analysis
- Tax reporting
- Trade reconciliation
- Position lifecycle tracking
- Strategy evaluation
"""

import asyncio
import logging
from datetime import datetime, timedelta
from ctc import CTraderClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def get_recent_deals():
    """Example: Get recent deal history."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"
    )
    
    async with client:
        print("=== Recent Deal History ===\n")
        
        # Get deals from last 7 days
        deals = await client.history.get_deals(days=7)
        
        print(f"Found {len(deals)} deals in the last 7 days\n")
        
        if deals:
            print(f"{'Date/Time':<20} {'Symbol':<10} {'Side':<6} {'Volume':<10} {'Price':<12} {'PnL':<12}")
            print("-" * 80)
            
            for deal in deals[-10:]:  # Show last 10
                dt = deal.datetime.strftime("%Y-%m-%d %H:%M") if deal.datetime else "N/A"
                symbol = deal.symbol_name or "N/A"
                side = deal.side or "N/A"
                volume = f"{deal.volume:.2f}" if deal.volume else "N/A"
                price = f"{deal.execution_price:.5f}" if deal.execution_price else "N/A"
                pnl = f"{deal.pnl:+.2f}" if deal.pnl != 0 else "0.00"
                
                print(f"{dt:<20} {symbol:<10} {side:<6} {volume:<10} {price:<12} {pnl:<12}")
            
            # Calculate totals
            total_pnl = sum(d.pnl for d in deals)
            total_commission = sum(d.commission for d in deals)
            total_swap = sum(d.swap for d in deals)
            net_result = total_pnl + total_commission + total_swap
            
            print("\n" + "=" * 80)
            print(f"Total PnL: {total_pnl:+.2f}")
            print(f"Total Commission: {total_commission:+.2f}")
            print(f"Total Swap: {total_swap:+.2f}")
            print(f"Net Result: {net_result:+.2f}")


async def analyze_position_lifecycle():
    """Example: Track all deals for a specific position."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"
    )
    
    async with client:
        print("=== Position Lifecycle Analysis ===\n")
        
        # Get open positions
        positions = await client.trading.get_positions()
        
        if not positions:
            print("No open positions found.")
            return
        
        # Analyze first position
        position = positions[0]
        print(f"Analyzing Position #{position.id}")
        print(f"Symbol: {position.symbol_name}")
        print(f"Current Volume: {position.volume:.2f} lots")
        print(f"Entry Price: {position.entry_price:.5f}\n")
        
        # Get all deals for this position
        deals = await client.history.get_deals_by_position(position.id)
        
        print(f"Found {len(deals)} deal(s) for this position:\n")
        
        if deals:
            print(f"{'#':<4} {'Date/Time':<20} {'Side':<6} {'Volume':<10} {'Price':<12} {'Commission':<12}")
            print("-" * 80)
            
            for i, deal in enumerate(deals, 1):
                dt = deal.datetime.strftime("%Y-%m-%d %H:%M") if deal.datetime else "N/A"
                side = deal.side or "N/A"
                volume = f"{deal.volume:.2f}" if deal.volume else "N/A"
                price = f"{deal.execution_price:.5f}" if deal.execution_price else "N/A"
                commission = f"{deal.commission:.2f}" if deal.commission else "0.00"
                
                print(f"{i:<4} {dt:<20} {side:<6} {volume:<10} {price:<12} {commission:<12}")
            
            # Calculate average entry price
            entry_deals = [d for d in deals if d.volume and d.execution_price]
            if entry_deals:
                total_volume = sum(d.volume for d in entry_deals)
                weighted_price = sum(d.execution_price * d.volume for d in entry_deals)
                avg_entry = weighted_price / total_volume if total_volume > 0 else 0
                
                print(f"\nAverage Entry Price: {avg_entry:.5f}")
                print(f"Current Entry Price: {position.entry_price:.5f}")


async def performance_report():
    """Example: Generate comprehensive performance report."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"
    )
    
    async with client:
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║              TRADING PERFORMANCE REPORT                      ║")
        print("╚══════════════════════════════════════════════════════════════╝\n")
        
        # Get performance summary for last 30 days
        summary = await client.history.get_performance_summary(days=30)
        
        print("📊 PERFORMANCE METRICS (Last 30 Days)")
        print("-" * 60)
        print(f"Total Deals: {summary['total_deals']}")
        print(f"Winning Deals: {summary['winning_deals']} 🟢")
        print(f"Losing Deals: {summary['losing_deals']} 🔴")
        print(f"Win Rate: {summary['win_rate']:.1f}%")
        print()
        
        print("💰 PROFIT & LOSS")
        print("-" * 60)
        print(f"Total PnL: {summary['total_pnl']:+.2f}")
        print(f"Total Commission: {summary['total_commission']:+.2f}")
        print(f"Total Swap: {summary['total_swap']:+.2f}")
        print(f"Net PnL: {summary['net_pnl']:+.2f}")
        print()
        
        print("📈 TRADE STATISTICS")
        print("-" * 60)
        print(f"Average Win: {summary['avg_win']:+.2f}")
        print(f"Average Loss: {summary['avg_loss']:+.2f}")
        print(f"Largest Win: {summary['largest_win']:+.2f}")
        print(f"Largest Loss: {summary['largest_loss']:+.2f}")
        print(f"Profit Factor: {summary['profit_factor']:.2f}")
        print()
        
        # Determine overall performance
        if summary['net_pnl'] > 0:
            performance = "🟢 PROFITABLE"
        elif summary['net_pnl'] < 0:
            performance = "🔴 LOSING"
        else:
            performance = "⚪ BREAKEVEN"
        
        print(f"Overall Performance: {performance}")
        print()
        
        # Add recommendations
        print("💡 RECOMMENDATIONS")
        print("-" * 60)
        
        if summary['win_rate'] < 40:
            print("⚠️  Win rate is low. Consider reviewing entry criteria.")
        elif summary['win_rate'] > 60:
            print("✅ Win rate is good!")
        
        if summary['profit_factor'] < 1.0:
            print("⚠️  Profit factor < 1.0. Strategy is losing money.")
        elif summary['profit_factor'] > 2.0:
            print("✅ Excellent profit factor!")
        
        if abs(summary['avg_loss']) > summary['avg_win']:
            print("⚠️  Average loss is larger than average win. Improve risk/reward.")
        else:
            print("✅ Good risk/reward ratio!")


async def symbol_breakdown():
    """Example: Analyze performance by symbol."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"
    )
    
    async with client:
        print("=== Performance by Symbol ===\n")
        
        # Get deals from last 30 days
        deals = await client.history.get_deals(days=30)
        
        if not deals:
            print("No deals found.")
            return
        
        # Group by symbol
        symbol_stats = {}
        
        for deal in deals:
            symbol = deal.symbol_name or "UNKNOWN"
            
            if symbol not in symbol_stats:
                symbol_stats[symbol] = {
                    'deals': 0,
                    'pnl': 0.0,
                    'commission': 0.0,
                    'swap': 0.0,
                    'volume': 0.0,
                    'wins': 0,
                    'losses': 0
                }
            
            stats = symbol_stats[symbol]
            stats['deals'] += 1
            stats['pnl'] += deal.pnl
            stats['commission'] += deal.commission
            stats['swap'] += deal.swap
            stats['volume'] += deal.volume or 0
            
            if deal.pnl > 0:
                stats['wins'] += 1
            elif deal.pnl < 0:
                stats['losses'] += 1
        
        # Display results
        print(f"{'Symbol':<12} {'Deals':<8} {'Win Rate':<12} {'Net PnL':<15} {'Volume':<10}")
        print("-" * 70)
        
        for symbol, stats in sorted(symbol_stats.items(), key=lambda x: x[1]['pnl'], reverse=True):
            win_rate = (stats['wins'] / stats['deals'] * 100) if stats['deals'] > 0 else 0
            net_pnl = stats['pnl'] + stats['commission'] + stats['swap']
            
            print(f"{symbol:<12} {stats['deals']:<8} {win_rate:<12.1f}% {net_pnl:<15.2f} {stats['volume']:<10.2f}")
        
        print()


async def daily_trading_journal():
    """Example: Create a daily trading journal."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"
    )
    
    async with client:
        print("=== Daily Trading Journal ===\n")
        
        # Get today's deals
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        from_ts = int(today_start.timestamp() * 1000)
        to_ts = int(datetime.now().timestamp() * 1000)
        
        deals = await client.history.get_deals(from_timestamp=from_ts, to_timestamp=to_ts)
        
        print(f"Date: {today_start.strftime('%Y-%m-%d')}")
        print(f"Total Deals: {len(deals)}\n")
        
        if not deals:
            print("No deals executed today.")
            return
        
        # Group by hour
        hourly_stats = {}
        
        for deal in deals:
            if deal.datetime:
                hour = deal.datetime.hour
                if hour not in hourly_stats:
                    hourly_stats[hour] = {
                        'deals': 0,
                        'pnl': 0.0,
                        'wins': 0,
                        'losses': 0
                    }
                
                hourly_stats[hour]['deals'] += 1
                hourly_stats[hour]['pnl'] += deal.pnl
                
                if deal.pnl > 0:
                    hourly_stats[hour]['wins'] += 1
                elif deal.pnl < 0:
                    hourly_stats[hour]['losses'] += 1
        
        # Display hourly breakdown
        print(f"{'Hour':<10} {'Deals':<8} {'Wins':<8} {'Losses':<8} {'PnL':<12}")
        print("-" * 50)
        
        for hour in sorted(hourly_stats.keys()):
            stats = hourly_stats[hour]
            print(f"{hour:02d}:00-{hour:02d}:59  {stats['deals']:<8} {stats['wins']:<8} {stats['losses']:<8} {stats['pnl']:<12.2f}")
        
        # Summary
        total_pnl = sum(d.pnl for d in deals)
        wins = sum(1 for d in deals if d.pnl > 0)
        losses = sum(1 for d in deals if d.pnl < 0)
        
        print("\n" + "=" * 50)
        print(f"Day Summary:")
        print(f"  Wins: {wins}, Losses: {losses}")
        print(f"  Win Rate: {(wins / len(deals) * 100):.1f}%")
        print(f"  Total PnL: {total_pnl:+.2f}")


async def tax_report():
    """Example: Generate tax reporting data."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"
    )
    
    async with client:
        print("=== Tax Reporting Data ===\n")
        
        # Get deals for the entire year
        year_start = datetime(datetime.now().year, 1, 1)
        from_ts = int(year_start.timestamp() * 1000)
        to_ts = int(datetime.now().timestamp() * 1000)
        
        deals = await client.history.get_deals(from_timestamp=from_ts, to_timestamp=to_ts)
        
        print(f"Tax Year: {datetime.now().year}")
        print(f"Total Transactions: {len(deals)}\n")
        
        # Calculate tax-relevant metrics
        total_gross_profit = sum(d.pnl for d in deals if d.pnl > 0)
        total_gross_loss = abs(sum(d.pnl for d in deals if d.pnl < 0))
        net_profit_loss = sum(d.pnl for d in deals)
        total_commission = sum(abs(d.commission) for d in deals)
        total_swap = sum(d.swap for d in deals)
        
        print("PROFIT & LOSS STATEMENT")
        print("-" * 60)
        print(f"Gross Profit: {total_gross_profit:.2f}")
        print(f"Gross Loss: {total_gross_loss:.2f}")
        print(f"Net Profit/Loss: {net_profit_loss:+.2f}")
        print()
        
        print("TRADING COSTS")
        print("-" * 60)
        print(f"Total Commission: {total_commission:.2f}")
        print(f"Total Swap: {total_swap:+.2f}")
        print()
        
        print("ADJUSTED NET")
        print("-" * 60)
        adjusted_net = net_profit_loss - total_commission + total_swap
        print(f"Net P/L After Costs: {adjusted_net:+.2f}")
        print()
        
        print("📌 Note: Please consult with a tax professional for proper reporting.")


async def get_order_details_example():
    """Example: Get detailed information about a specific order."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"
    )
    
    async with client:
        print("=== Order Details Example ===\n")
        
        # Get pending orders
        orders = await client.trading.get_orders()
        
        if not orders:
            print("No pending orders found.")
            return
        
        # Get details for first order
        order_id = orders[0].id
        print(f"Retrieving details for Order #{order_id}...\n")
        
        order_details = await client.history.get_order_details(order_id)
        
        if order_details:
            print(f"Order #{order_details.id}")
            print(f"Symbol: {order_details.symbol_name}")
            print(f"Type: {order_details.order_type}")
            print(f"Status: {order_details.status}")
            print(f"Side: {order_details.side}")
            print(f"Volume: {order_details.volume:.2f} lots")
            
            if order_details.limit_price:
                print(f"Limit Price: {order_details.limit_price:.5f}")
            if order_details.stop_price:
                print(f"Stop Price: {order_details.stop_price:.5f}")
            
            if order_details.create_datetime:
                print(f"Created: {order_details.create_datetime}")
        else:
            print("Order details not found.")


if __name__ == "__main__":
    # Run different examples
    import sys
    
    if len(sys.argv) > 1:
        example = sys.argv[1]
        examples = {
            "deals": get_recent_deals,
            "position": analyze_position_lifecycle,
            "performance": performance_report,
            "symbols": symbol_breakdown,
            "journal": daily_trading_journal,
            "tax": tax_report,
            "order": get_order_details_example,
        }
        
        if example in examples:
            asyncio.run(examples[example]())
        else:
            print(f"Unknown example: {example}")
            print(f"Available examples: {', '.join(examples.keys())}")
    else:
        # Run performance report by default
        asyncio.run(performance_report())
