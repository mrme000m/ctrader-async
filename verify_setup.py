#!/usr/bin/env python3
"""
Verify that the cTrader async client setup is complete and ready for testing.

This script checks:
- Python version
- Required dependencies
- .env configuration
- Import paths
- Basic connectivity test

Usage:
    python verify_setup.py
"""

import sys
import os
from pathlib import Path

# Ensure project root is on sys.path so `import ctrader_async` works
# whether this script is run from the repo root or from inside `ctrader_async/`.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

def check_python_version():
    """Check if Python version is 3.10+"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (requires 3.10+)")
        return False

def check_dependencies():
    """Check if required dependencies are installed."""
    print("\n📦 Checking dependencies...")
    
    required = {
        'ctrader_async': 'ctrader-async (local)',
        'google.protobuf': 'protobuf',
        'pytest': 'pytest',
        'pytest_asyncio': 'pytest-asyncio',
    }
    
    all_ok = True
    for module, package in required.items():
        try:
            __import__(module)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} (install with: pip install {package})")
            all_ok = False
    
    return all_ok

def check_env_file():
    """Check if .env file exists and has required variables."""
    print("\n⚙️  Checking .env configuration...")
    
    env_file = Path(__file__).parent / ".env"
    
    if not env_file.exists():
        print(f"   ❌ .env file not found")
        print(f"      Copy .env.example to .env and configure it")
        return False
    
    print(f"   ✅ .env file exists")
    
    # Check for required variables
    required_vars = [
        'CTRADER_CLIENT_ID',
        'CTRADER_CLIENT_SECRET',
        'CTRADER_ACCESS_TOKEN',
        'CTRADER_ACCOUNT_ID',
    ]
    
    # Try to load dotenv if available
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith('your_') or value.startswith('12345'):
            missing.append(var)
    
    if missing:
        print(f"   ⚠️  Missing or placeholder values in .env:")
        for var in missing:
            print(f"      - {var}")
        return False
    else:
        print(f"   ✅ All required variables configured")
        return True

def check_imports():
    """Check if package can be imported."""
    print("\n📥 Checking package imports...")
    
    try:
        from ctrader_async import CTraderClient, TradeSide
        print(f"   ✅ ctrader_async package imports correctly")
        return True
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False

def check_structure():
    """Check if all required files exist."""
    print("\n📁 Checking package structure...")
    
    base_dir = Path(__file__).parent
    required_files = [
        "client.py",
        "config.py",
        "models.py",
        "enums.py",
        "api/trading.py",
        "api/market_data.py",
        "api/account.py",
        "api/symbols.py",
        "transport/tcp.py",
        "protocol/handler.py",
        "auth/authenticator.py",
        "tests/test_integration.py",
    ]
    
    all_ok = True
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path}")
            all_ok = False
    
    return all_ok

async def test_connection():
    """Test basic connection to cTrader server."""
    print("\n🔌 Testing connection to cTrader demo server...")
    
    try:
        from ctrader_async import CTraderClient
        
        client = CTraderClient.from_env()
        
        print(f"   Connecting to {client.config.host_type} server...")
        await client.connect()
        
        print(f"   ✅ Connected successfully!")
        print(f"   ✅ Authenticated successfully!")
        
        # Get basic info
        account = await client.account.get_info()
        print(f"   💰 Account Balance: ${account.balance:,.2f}")
        
        symbols = await client.symbols.get_all()
        print(f"   📊 Available Symbols: {len(symbols)}")
        
        await client.disconnect()
        print(f"   ✅ Disconnected successfully!")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False

def main():
    """Run all verification checks."""
    print("=" * 70)
    print("cTrader Async Client - Setup Verification")
    print("=" * 70)
    
    checks = []
    
    # Run checks
    checks.append(("Python Version", check_python_version()))
    checks.append(("Dependencies", check_dependencies()))
    checks.append(("Environment Config", check_env_file()))
    checks.append(("Package Imports", check_imports()))
    checks.append(("Package Structure", check_structure()))
    
    # Connection test (optional, requires valid credentials)
    if all(result for _, result in checks):
        print("\n" + "=" * 70)
        print("All basic checks passed! Attempting live connection test...")
        print("=" * 70)
        
        try:
            import asyncio
            connection_ok = asyncio.run(test_connection())
            checks.append(("Connection Test", connection_ok))
        except Exception as e:
            print(f"\n⚠️  Connection test skipped: {e}")
            checks.append(("Connection Test", False))
    
    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    for check_name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:12} {check_name}")
    
    all_passed = all(result for _, result in checks)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL CHECKS PASSED!")
        print("=" * 70)
        print("\n🚀 You're ready to run tests:")
        print("   python run_integration_tests.py")
        print("\n   OR")
        print("   pytest tests/test_integration.py -v -s")
        return 0
    else:
        print("❌ SOME CHECKS FAILED")
        print("=" * 70)
        print("\n📝 Please fix the issues above before running tests.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
