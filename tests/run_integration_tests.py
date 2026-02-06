#!/usr/bin/env python3
"""
Quick runner for integration tests.

Usage:
    python run_integration_tests.py
"""

import sys
import subprocess
from pathlib import Path

# Ensure project root is on sys.path so tests can import `ctrader_async`
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

def main():
    """Run integration tests."""
    tests_dir = Path(__file__).parent / "tests"
    test_file = tests_dir / "test_integration.py"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return 1
    
    print("=" * 70)
    print("cTrader Async Client - Integration Tests")
    print("=" * 70)
    print()
    
    # Check for .env file
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        print("⚠️  Warning: .env file not found!")
        print("   Copy .env.example to .env and fill in your credentials")
        print()
    
    # Run pytest
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_file),
        "-v", "-s",
        "--tb=short"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd)
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
