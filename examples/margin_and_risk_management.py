"""
Example: Margin and Risk Management

This example demonstrates how to use the Risk Management API for:
- Pre-trade margin calculations
- Position PnL monitoring
- Risk validation before trading
- Margin event monitoring
- Margin call tracking

Use cases:
- Position sizing based on available margin
- Pre-trade risk checks
- Real-time PnL monitoring
- Margin call alerts
- Professional risk management
"""

import asyncio
import logging
from ctc import CTraderClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def calculate_margin_example():
    """Example: Calculate margin before placing orders."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"
    )
    
    async with client:
        print("=== Margin Calculation Example ===\n")
        
        # Get account info
        account = await client.account.get_account_info()
        print(f"Account Balance: {account.balance:.2f} {account.currency}")
        print(f"Equity: {account.equity:.2f}")
        print(f"Free Margin: {account.free_margin:.2f}")
        print(f"Margin Level: {account.margin_level:.2f}%\n")
        
        # Calculate margin for different trade sizes
        symbol = "EURUSD"
        volumes = [0.01, 0.1, 1.0, 5.0]
        
        print(f"Margin requirements for {symbol}:")
        print(f"{'Volume (lots)':<15} {'Margin Required':<20} {'% of Free Margin':<20}")
        print("-" * 60)
        
        for volume in volumes:
            try:
                margin_info = await client.risk.get_expected_margin(symbol, volume)
                margin_pct = (margin_info.margin / account.free_margin * 100) if account.free_margin > 0 else 0
                
                print(f"{volume:<15.2f} {margin_info.formatted_margin:<20} {margin_pct:<20.2f}%")
                
                # Show buy/sell specific margins if available
                if margin_info.buy_margin and margin_info.sell_margin:
                    print(f"  → Buy Margin:  {margin_info.buy_margin:.2f}")
                    print(f"  → Sell Margin: {margin_info.sell_margin:.2f}")
            
            except Exception as e:
                print(f"{volume:<15.2f} Error: {e}")
        
        print("\n✅ Margin calculation complete!")


async def risk_validation_example():
    """Example: Validate trade risk before placing orders."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"
    )
    
    async with client:
        print("=== Risk Validation Example ===\n")
        
        # Proposed trade
        symbol = "EURUSD"
        volume = 1.0
        side = "BUY"
        max_risk_percent = 2.0  # Maximum 2% risk per trade
        
        print(f"Validating trade: {side} {volume} lots {symbol}")
        print(f"Maximum risk: {max_risk_percent}%\n")
        
        # Validate the trade
        validation = await client.risk.validate_trade_risk(
            symbol=symbol,
            volume=volume,
            side=side,
            max_risk_percent=max_risk_percent
        )
        
        print(f"{'Validation Results':-^60}")
        print(f"Valid: {'✅ YES' if validation['valid'] else '❌ NO'}")
        print(f"Margin Required: {validation['margin_required']:.2f}")
        print(f"Margin Available: {validation['margin_available']:.2f}")
        print(f"Margin Sufficient: {'✅' if validation['margin_sufficient'] else '❌'}")
        print(f"Risk Percentage: {validation['risk_percent']:.2f}%")
        print(f"Risk Acceptable: {'✅' if validation['risk_acceptable'] else '❌'}")
        
        if validation['warnings']:
            print(f"\n⚠️  Warnings:")
            for warning in validation['warnings']:
                print(f"  - {warning}")
        
        # Place order only if validation passes
        if validation['valid']:
            print(f"\n✅ Trade validated - Safe to place order")
            # Uncomment to actually place the order:
            # position = await client.trading.place_market_order(symbol, side, volume)
            # print(f"Order placed: Position #{position.id}")
        else:
            print(f"\n❌ Trade rejected - Does not meet risk criteria")


async def position_pnl_monitoring():
    """Example: Monitor position PnL in real-time."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"
    )
    
    async with client:
        print("=== Position PnL Monitoring ===\n")
        
        # Get all open positions
        positions = await client.trading.get_positions()
        
        if not positions:
            print("No open positions found.")
            return
        
        print(f"Found {len(positions)} open position(s)\n")
        
        # Monitor each position
        for position in positions:
            print(f"{'='*60}")
            print(f"Position #{position.id} - {position.symbol_name}")
            print(f"{'='*60}")
            
            # Get detailed PnL breakdown
            pnl = await client.risk.get_position_pnl(position.id)
            
            if pnl:
                print(f"Side: {position.side}")
                print(f"Volume: {position.volume:.2f} lots")
                print(f"Entry Price: {position.entry_price:.5f}")
                print(f"Current Price: {position.current_price:.5f}" if position.current_price else "N/A")
                print(f"\nPnL Breakdown:")
                print(f"  Gross Unrealized PnL: {pnl.formatted_gross_pnl}")
                print(f"  Swap Charges: {pnl.swap:+.2f}")
                print(f"  Commission: {pnl.commission:+.2f}")
                print(f"  Total Costs: {pnl.total_costs:.2f}")
                print(f"  Net Unrealized PnL: {pnl.formatted_net_pnl}")
                
                if pnl.used_margin:
                    print(f"  Used Margin: {pnl.used_margin:.2f}")
                
                # PnL status
                if pnl.net_unrealized_pnl > 0:
                    print(f"\n🟢 Position is PROFITABLE")
                elif pnl.net_unrealized_pnl < 0:
                    print(f"\n🔴 Position is LOSING")
                else:
                    print(f"\n⚪ Position is BREAKEVEN")
            
            print()


async def margin_event_monitoring():
    """Example: Monitor margin changes in real-time."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"
    )
    
    async with client:
        print("=== Margin Event Monitoring ===\n")
        print("Monitoring margin changes... Press Ctrl+C to stop\n")
        
        # Subscribe to margin change events
        def on_margin_change(position_id, used_margin, money_digits):
            print(f"[{asyncio.get_event_loop().time():.2f}] "
                  f"Position #{position_id}: Margin changed to {used_margin:.{money_digits}f}")
        
        client.risk.subscribe_margin_events(on_margin_change)
        
        # Keep monitoring
        try:
            # Also show periodic account margin level
            while True:
                await asyncio.sleep(10)
                account = await client.account.get_account_info()
                print(f"\n📊 Account Margin Level: {account.margin_level:.2f}%")
                print(f"   Used Margin: {account.margin:.2f}")
                print(f"   Free Margin: {account.free_margin:.2f}\n")
        
        except KeyboardInterrupt:
            print("\nStopped margin monitoring")


async def margin_call_tracking():
    """Example: Track margin calls on the account."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"
    )
    
    async with client:
        print("=== Margin Call Tracking ===\n")
        
        # Get margin call history
        try:
            margin_calls = await client.risk.get_margin_calls()
            
            if not margin_calls:
                print("✅ No margin calls found - Account is healthy!")
            else:
                print(f"⚠️  Found {len(margin_calls)} margin call(s):\n")
                
                for i, call in enumerate(margin_calls, 1):
                    print(f"Margin Call #{i}")
                    print(f"  Type: {call.margin_call_type}")
                    print(f"  Time: {call.datetime}")
                    print(f"  Equity: {call.formatted_equity}")
                    print(f"  Margin: {call.margin:.2f}")
                    print(f"  Margin Level: {call.formatted_margin_level}")
                    print()
        
        except Exception as e:
            print(f"Error retrieving margin calls: {e}")


async def smart_position_sizing():
    """Example: Calculate optimal position size based on risk."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"
    )
    
    async with client:
        print("=== Smart Position Sizing ===\n")
        
        # Get account info
        account = await client.account.get_account_info()
        print(f"Account Equity: {account.equity:.2f}")
        print(f"Free Margin: {account.free_margin:.2f}\n")
        
        # Risk parameters
        symbol = "EURUSD"
        max_risk_percent = 2.0  # Risk 2% of equity
        max_margin_usage = 50.0  # Use max 50% of free margin
        
        print(f"Finding optimal position size for {symbol}")
        print(f"Maximum risk: {max_risk_percent}% of equity")
        print(f"Maximum margin usage: {max_margin_usage}% of free margin\n")
        
        # Test different volumes to find maximum acceptable
        test_volumes = [0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        optimal_volume = 0.01
        
        print(f"{'Volume':<10} {'Margin':<15} {'% Free Margin':<20} {'Status':<10}")
        print("-" * 60)
        
        for volume in test_volumes:
            try:
                margin_info = await client.risk.get_expected_margin(symbol, volume)
                margin_pct = (margin_info.margin / account.free_margin * 100) if account.free_margin > 0 else 0
                
                # Check if within limits
                if margin_pct <= max_margin_usage:
                    optimal_volume = volume
                    status = "✅ OK"
                else:
                    status = "❌ Too high"
                
                print(f"{volume:<10.2f} {margin_info.margin:<15.2f} {margin_pct:<20.2f}% {status}")
            
            except Exception as e:
                print(f"{volume:<10.2f} Error: {e}")
                break
        
        print(f"\n✅ Optimal position size: {optimal_volume:.2f} lots")
        print(f"   This uses approximately {(optimal_volume / test_volumes[-1] * 100):.1f}% of max tested volume")


async def risk_dashboard():
    """Example: Complete risk dashboard."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"
    )
    
    async with client:
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║              RISK MANAGEMENT DASHBOARD                       ║")
        print("╚══════════════════════════════════════════════════════════════╝\n")
        
        # Account Overview
        account = await client.account.get_account_info()
        print("📊 ACCOUNT OVERVIEW")
        print("-" * 60)
        print(f"Balance: {account.balance:.2f} {account.currency}")
        print(f"Equity: {account.equity:.2f}")
        print(f"Used Margin: {account.margin:.2f}")
        print(f"Free Margin: {account.free_margin:.2f}")
        print(f"Margin Level: {account.margin_level:.2f}%")
        
        # Health indicator
        if account.margin_level and account.margin_level > 200:
            print("Health: 🟢 HEALTHY")
        elif account.margin_level and account.margin_level > 100:
            print("Health: 🟡 MODERATE")
        else:
            print("Health: 🔴 WARNING")
        print()
        
        # Open Positions Risk
        positions = await client.trading.get_positions()
        print(f"📈 OPEN POSITIONS ({len(positions)})")
        print("-" * 60)
        
        total_unrealized_pnl = 0
        total_costs = 0
        
        for position in positions:
            pnl = await client.risk.get_position_pnl(position.id)
            if pnl:
                total_unrealized_pnl += pnl.net_unrealized_pnl
                total_costs += pnl.total_costs
                
                indicator = "🟢" if pnl.net_unrealized_pnl > 0 else "🔴" if pnl.net_unrealized_pnl < 0 else "⚪"
                print(f"{indicator} {position.symbol_name} {position.side} {position.volume:.2f} lots")
                print(f"   PnL: {pnl.formatted_net_pnl} (Costs: {pnl.total_costs:.2f})")
        
        if positions:
            print(f"\nTotal Unrealized PnL: {total_unrealized_pnl:+.2f}")
            print(f"Total Costs: {total_costs:.2f}")
        else:
            print("No open positions")
        print()
        
        # Margin Calls
        try:
            margin_calls = await client.risk.get_margin_calls()
            if margin_calls:
                print(f"⚠️  MARGIN CALLS ({len(margin_calls)})")
                print("-" * 60)
                for call in margin_calls[:3]:  # Show last 3
                    print(f"{call.margin_call_type} at {call.datetime}")
                print()
        except Exception:
            pass
        
        print("✅ Dashboard updated!")


if __name__ == "__main__":
    # Run different examples
    import sys
    
    if len(sys.argv) > 1:
        example = sys.argv[1]
        examples = {
            "margin": calculate_margin_example,
            "validate": risk_validation_example,
            "pnl": position_pnl_monitoring,
            "events": margin_event_monitoring,
            "calls": margin_call_tracking,
            "sizing": smart_position_sizing,
            "dashboard": risk_dashboard,
        }
        
        if example in examples:
            asyncio.run(examples[example]())
        else:
            print(f"Unknown example: {example}")
            print(f"Available examples: {', '.join(examples.keys())}")
    else:
        # Run dashboard by default
        asyncio.run(risk_dashboard())
