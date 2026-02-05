# Testing Guide

Complete guide for running integration tests on the cTrader async client.

## Quick Start

```bash
# 1. Verify setup
python verify_setup.py

# 2. Run all tests
python run_integration_tests.py
```

## Prerequisites

### 1. Python Environment
- Python 3.10 or higher
- Virtual environment recommended

### 2. Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. cTrader Demo Account
You need:
- Client ID
- Client Secret  
- Access Token
- Demo Account ID

Get these from: https://openapi.ctrader.com/

### 4. Environment Configuration
```bash
cp .env.example .env
# Edit .env with your credentials
```

## Running Tests

### Verify Setup First
```bash
python verify_setup.py
```

This checks:
- ✅ Python version
- ✅ Dependencies installed
- ✅ .env file configured
- ✅ Package imports
- ✅ Live connection test

### Run All Tests
```bash
python run_integration_tests.py
```

### Run with pytest
```bash
# All tests with verbose output
pytest tests/test_integration.py -v -s

# Specific test class
pytest tests/test_integration.py::TestMarketOrderTrading -v -s

# Specific test function
pytest tests/test_integration.py::TestAllOrderTypes::test_all_order_types_sequence -v -s

# With coverage
pytest tests/test_integration.py --cov=ctrader_async
```

## Test Organization

### Test Classes

1. **TestConnection** - Connection lifecycle
2. **TestAccountAPI** - Account operations
3. **TestSymbolsAPI** - Symbol catalog
4. **TestMarketOrderTrading** - Market orders
5. **TestLimitOrderTrading** - Limit orders
6. **TestStopOrderTrading** - Stop orders
7. **TestStopLimitOrderTrading** - Stop-limit orders
8. **TestPositionManagement** - Position operations
9. **TestOrderManagement** - Order operations
10. **TestMarketData** - Historical & streaming data
11. **TestBulkOperations** - Bulk operations
12. **TestAllOrderTypes** - Comprehensive test

## What Gets Tested

### Order Types (All 4)
- ✅ Market orders (immediate execution)
- ✅ Limit orders (at specified price)
- ✅ Stop orders (trigger at price)
- ✅ Stop-limit orders (trigger + limit)

### Trading Operations
- ✅ Place orders with SL/TP
- ✅ Modify position SL/TP
- ✅ Close positions (full/partial)
- ✅ Cancel orders
- ✅ Bulk operations

### Market Data
- ✅ Historical candles
- ✅ Real-time tick streaming
- ✅ Symbol information

### Account
- ✅ Balance and equity
- ✅ Margin calculations
- ✅ Account info caching

## Test Safety

### Automated Cleanup
- All positions closed after tests
- All orders cancelled after tests
- Isolated test fixtures

### Minimal Impact
- Uses micro lots (0.01)
- Orders placed far from market
- Won't execute unless market moves dramatically

## Troubleshooting

### Import Errors
```
ModuleNotFoundError: No module named 'ctrader_open_api'
```
**Fix**: `pip install ctrader-open-api`

### Connection Errors
```
ConnectionError: Failed to connect
```
**Fix**: Check credentials in .env and internet connection

### Authentication Errors
```
AuthenticationError: Authentication failed
```
**Fix**: Verify credentials are correct and account is active

### Market Closed
```
MarketClosedError: Market is closed
```
**Fix**: Run during market hours (Mon-Fri)

## Test Output

### Successful Test
```
tests/test_integration.py::TestMarketOrderTrading::test_place_market_order

✅ Market Order Placed:
   Position ID: 123456789
   Entry Price: 1.09234
   ✅ Position closed
PASSED
```

### Failed Test
```
tests/test_integration.py::TestMarketOrderTrading::test_place_market_order

❌ Market order error: Market is closed
FAILED
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements-dev.txt
      - run: pytest tests/test_integration.py
        env:
          CTRADER_CLIENT_ID: ${{ secrets.CTRADER_CLIENT_ID }}
          CTRADER_CLIENT_SECRET: ${{ secrets.CTRADER_CLIENT_SECRET }}
          CTRADER_ACCESS_TOKEN: ${{ secrets.CTRADER_ACCESS_TOKEN }}
          CTRADER_ACCOUNT_ID: ${{ secrets.CTRADER_ACCOUNT_ID }}
```

## Best Practices

1. **Always use demo account** for testing
2. **Run verify_setup.py** before tests
3. **Check market hours** for trading tests
4. **Review logs** for detailed error info
5. **Keep credentials secure** (never commit .env)

## Resources

- Test Code: `tests/test_integration.py`
- Test Documentation: `tests/README.md`
- Test Summary: `TEST_SUMMARY.md`
- Package Documentation: `README.md`

---

**Ready?** Run `python verify_setup.py` to get started!
