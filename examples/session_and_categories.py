"""
Example: Session Management and Symbol Categories

This example demonstrates:
- Multi-account discovery
- Symbol category filtering
- Session management
"""

import asyncio
import logging
from ctc import CTraderClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def multi_account_example():
    """Example: Discover and list available accounts."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"
    )
    
    async with client:
        print("=== Multi-Account Discovery ===\n")
        
        # Get all accounts accessible with current token
        accounts = await client.session.get_available_accounts()
        
        print(f"Found {len(accounts)} accessible account(s):\n")
        
        for i, account in enumerate(accounts, 1):
            print(f"Account #{i}")
            print(f"  ID: {account.account_id}")
            print(f"  Type: {account.account_type}")
            print(f"  Broker: {account.broker_name}")
            print(f"  Is Live: {account.is_live}")
            print()
        
        print("Note: To switch accounts, create a new client with the desired account_id")


async def symbol_categories_example():
    """Example: Filter symbols by category."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"
    )
    
    async with client:
        print("=== Symbol Categories ===\n")
        
        # Get all available categories
        categories = await client.symbols.get_categories()
        
        print(f"Available Categories ({len(categories)}):")
        for category in categories:
            print(f"  - {category}")
        print()
        
        # Get symbols for each category
        for category in categories[:3]:  # Show first 3 categories
            symbols = await client.symbols.get_symbols_by_category(category)
            print(f"\n{category} Symbols ({len(symbols)}):")
            
            for symbol in symbols[:5]:  # Show first 5 symbols
                print(f"  • {symbol.name}")
                if symbol.description:
                    print(f"    {symbol.description}")


async def filter_tradeable_symbols():
    """Example: Find all tradeable Forex symbols."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"
    )
    
    async with client:
        print("=== Tradeable Forex Symbols ===\n")
        
        # Get all Forex symbols
        try:
            forex_symbols = await client.symbols.get_symbols_by_category("Forex")
        except:
            # Fallback: search for common forex pairs
            all_symbols = await client.symbols.get_all()
            forex_symbols = [s for s in all_symbols if s.category_name and "forex" in s.category_name.lower()]
        
        # Filter to enabled symbols only
        enabled_symbols = [s for s in forex_symbols if s.enabled]
        
        print(f"Found {len(enabled_symbols)} tradeable Forex symbols\n")
        
        # Group by major/minor/exotic
        majors = []
        minors = []
        exotics = []
        
        for symbol in enabled_symbols:
            name = symbol.name.upper()
            # Major pairs include USD
            if "USD" in name and any(x in name for x in ["EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"]):
                majors.append(symbol)
            # Minor pairs (cross pairs)
            elif "USD" not in name and any(x in name for x in ["EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"]):
                minors.append(symbol)
            else:
                exotics.append(symbol)
        
        print(f"Major Pairs ({len(majors)}):")
        for s in majors[:10]:
            print(f"  {s.name}: leverage={s.leverage}, spread~{s.pip_position}")
        
        print(f"\nMinor Pairs ({len(minors)}):")
        for s in minors[:5]:
            print(f"  {s.name}")
        
        print(f"\nExotic Pairs ({len(exotics)}):")
        for s in exotics[:5]:
            print(f"  {s.name}")


async def category_watchlist():
    """Example: Create watchlists by category."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"
    )
    
    async with client:
        print("=== Category Watchlists ===\n")
        
        # Define watchlist categories
        watchlist_categories = {
            "Forex": ["EURUSD", "GBPUSD", "USDJPY"],
            "Commodities": ["XAUUSD", "XAGUSD", "USOIL"],  # Gold, Silver, Oil
            "Indices": ["US30", "NAS100", "SPX500"],
        }
        
        for category, preferred_symbols in watchlist_categories.items():
            try:
                # Get all symbols in category
                category_symbols = await client.symbols.get_symbols_by_category(category)
                
                # Find matching symbols
                watchlist = []
                for pref in preferred_symbols:
                    for symbol in category_symbols:
                        if pref.upper() in symbol.name.upper():
                            watchlist.append(symbol)
                            break
                
                print(f"\n{category} Watchlist:")
                for symbol in watchlist:
                    print(f"  {symbol.name}")
                    print(f"    Enabled: {symbol.enabled}")
                    print(f"    Digits: {symbol.digits}")
                    if symbol.leverage:
                        print(f"    Leverage: {symbol.leverage}")
            
            except Exception as e:
                print(f"  Error loading {category}: {e}")


async def session_logout_example():
    """Example: Properly logout from account."""
    
    client = CTraderClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        account_id=12345,
        host_type="demo"
    )
    
    async with client:
        print("=== Session Logout ===\n")
        
        # Get account info
        account = await client.account.get_account_info()
        print(f"Connected to account {account.account_id}")
        print(f"Balance: {account.balance}")
        print()
        
        # Do some operations
        positions = await client.trading.get_positions()
        print(f"Open positions: {len(positions)}")
        print()
        
        # Logout when done
        print("Logging out...")
        await client.session.logout()
        print("Logged out successfully")
        
        # Connection remains but account operations won't work
        print("\nNote: Connection remains open but account operations are disabled")


if __name__ == "__main__":
    # Run different examples
    import sys
    
    if len(sys.argv) > 1:
        example = sys.argv[1]
        examples = {
            "accounts": multi_account_example,
            "categories": symbol_categories_example,
            "filter": filter_tradeable_symbols,
            "watchlist": category_watchlist,
            "logout": session_logout_example,
        }
        
        if example in examples:
            asyncio.run(examples[example]())
        else:
            print(f"Unknown example: {example}")
            print(f"Available examples: {', '.join(examples.keys())}")
    else:
        # Run categories example by default
        asyncio.run(symbol_categories_example())
