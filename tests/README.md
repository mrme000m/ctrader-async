# Integration Tests

Comprehensive integration tests that connect to real cTrader demo server.

## Setup

1. Copy `.env.example` to `.env` in the root directory
2. Fill in your cTrader demo account credentials
3. Install test dependencies: `pip install -r requirements-dev.txt`

## Running Tests

Run all tests:
```bash
cd ctrader_async
pytest tests/test_integration.py -v -s
```

Run specific test class:
```bash
pytest tests/test_integration.py::TestMarketOrderTrading -v -s
```

Run specific test:
```bash
pytest tests/test_integration.py::TestAllOrderTypes::test_all_order_types_sequence -v -s
```

## Test Coverage

### Connection Tests
- Context manager connection
- Manual connect/disconnect

### Account API
- Get account info
- Account info caching

### Symbols API
- Get all symbols
- Get specific symbol
- Search symbols

### Trading - Market Orders
- Place market order
- Market order with SL/TP

### Trading - Limit Orders
- Place limit order
- Limit order with SL/TP

### Trading - Stop Orders
- Place stop order
- Stop order with SL/TP

### Trading - Stop-Limit Orders
- Place stop-limit order
- Stop-limit order with all parameters

### Position Management
- Modify position SL/TP
- Get all positions
- Partial close
- Close all positions

### Order Management
- Get all orders
- Cancel order
- Cancel all orders

### Market Data
- Get historical candles
- Stream real-time ticks

### Comprehensive Test
- All 4 order types in sequence

## Notes

- Tests use micro lots (0.01) to minimize impact
- All positions/orders are cleaned up after tests
- Tests place orders far from market to avoid execution
- Some tests may fail during market close hours
