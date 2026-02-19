# Contributing to cTrader Async Client

Thank you for your interest in contributing to the cTrader Async Client! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Testing](#testing)
- [Documentation](#documentation)
- [Release Process](#release-process)

## Code of Conduct

This project adheres to a code of conduct that we expect all contributors to follow:

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different viewpoints and experiences

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Create a new branch for your feature or bug fix
4. Make your changes
5. Run the tests
6. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.10 or higher
- pip or uv for package management
- Git

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/ctrader-async.git
cd ctrader-async

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Or with uv
uv pip install -e ".[dev]"
```

### Verify Setup

```bash
# Run tests to verify everything works
pytest tests/ -v

# Run type checking
mypy src/ctc

# Run linting
ruff check src/ctc
```

## Contributing Guidelines

### Branch Naming

- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Commit Messages

Use clear, descriptive commit messages:

```
feat: Add WebSocket transport support

- Implement AsyncWebSocketTransport class
- Add WebSocket framing support
- Include reconnection logic for WebSocket
```

### Code Style

We use the following tools to maintain code quality:

- **Black** - Code formatting (100 character line length)
- **Ruff** - Fast Python linting
- **MyPy** - Static type checking

Run before committing:

```bash
# Format code
black src/ctc tests/

# Run linter
ruff check src/ctc tests/

# Type check
mypy src/ctc
```

### Type Hints

All public APIs must have complete type hints:

```python
async def place_market_order(
    self,
    symbol: str,
    side: TradeSide,
    volume: float,
    *,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
) -> Position:
    """Place a market order.
    
    Args:
        symbol: Symbol name (e.g., "EURUSD")
        side: Trade side (BUY or SELL)
        volume: Volume in lots
        stop_loss: Stop loss price (optional)
        take_profit: Take profit price (optional)
        
    Returns:
        Created position
        
    Raises:
        TradingError: If order fails
    """
```

## Testing

### Test Structure

```
tests/
├── test_account_api.py      # Account API tests
├── test_risk_api.py         # Risk API tests
├── test_history_api.py      # History API tests
├── test_integration.py      # Integration tests (requires live connection)
└── conftest.py              # Test fixtures and configuration
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ctc --cov-report=html

# Run specific test file
pytest tests/test_account_api.py -v

# Run integration tests (requires credentials)
export CTRADER_RUN_INTEGRATION=true
export CTRADER_CLIENT_ID=your_id
export CTRADER_CLIENT_SECRET=your_secret
export CTRADER_ACCESS_TOKEN=your_token
export CTRADER_ACCOUNT_ID=your_account
pytest tests/test_integration.py -v
```

### Writing Tests

#### Unit Tests

Test models and pure functions without network:

```python
def test_margin_info_calculation():
    info = MarginInfo(margin=100.0, money_digits=2)
    assert info.formatted_margin == "100.00"
```

#### Integration Tests

Tests requiring live connection should be marked:

```python
import pytest

@pytest.mark.integration
@pytest.mark.asyncio
async def test_place_market_order():
    async with CTraderClient.from_env() as client:
        position = await client.trading.place_market_order(
            "EURUSD", TradeSide.BUY, 0.01
        )
        assert position.id > 0
```

### Mocking

Use pytest-asyncio and unittest.mock for mocking:

```python
@pytest.mark.asyncio
async def test_trading_with_mock():
    with patch('ctc.api.trading.ProtoOANewOrderReq') as mock_req:
        # Test logic
        pass
```

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
async def get_expected_margin(
    self,
    symbol: str,
    volume: float,
) -> MarginInfo:
    """Calculate expected margin for a proposed trade.
    
    Use this before placing orders to ensure sufficient margin is available.
    
    Args:
        symbol: Symbol name (e.g., "EURUSD")
        volume: Trade volume in lots
        
    Returns:
        MarginInfo with required margin details
        
    Raises:
        ValueError: If symbol not found
        TimeoutError: If request times out
        
    Example:
        >>> margin = await client.risk.get_expected_margin("EURUSD", 1.0)
        >>> print(f"Required margin: {margin.formatted_margin}")
    """
```

### README Updates

When adding new features:

1. Update the feature list in README.md
2. Add a usage example
3. Update API_REFERENCE.md

### Changelog

Add entries to CHANGELOG.md under `[Unreleased]`:

```markdown
### Added
- New feature description

### Fixed
- Bug fix description
```

## Architecture Guidelines

### Adding a New API Method

1. **Define the message types** in the appropriate API class
2. **Create data models** in `models.py` if needed
3. **Implement the method** with proper error handling
4. **Add tests** in the appropriate test file
5. **Update documentation**

Example:

```python
# In src/ctc/api/my_api.py
class MyAPI:
    async def new_method(self, param: str) -> Result:
        """Docstring here."""
        from ..messages.OpenApiMessages_pb2 import (
            ProtoOANewReq,
            ProtoOANewRes,
        )
        
        req = ProtoOANewReq()
        req.ctidTraderAccountId = self.config.account_id
        req.param = param
        
        response = await self.protocol.send_request(
            req,
            timeout=self.config.request_timeout,
            request_type="NewMethod"
        )
        
        if not isinstance(response, ProtoOANewRes):
            raise ValueError(f"Unexpected response: {type(response)}")
            
        return Result(data=response.data)
```

### Adding a New Stream

1. Create a new stream class in `streams/`
2. Inherit from `BaseStream`
3. Implement `subscribe()` and `unsubscribe()` methods
4. Add stream method to `MarketDataAPI`

Example:

```python
# In src/ctc/streams/my_stream.py
class MyStream(BaseStream[T]):
    """Stream for my data type."""
    
    async def subscribe(self) -> None:
        req = ProtoOASubscribeMyDataReq()
        # ... setup request
        await self._send_subscribe(req)
        
    async def unsubscribe(self) -> None:
        req = ProtoOAUnsubscribeMyDataReq()
        await self._send_unsubscribe(req)
```

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md with release date
3. Create a git tag: `git tag v0.2.0`
4. Push tag: `git push origin v0.2.0`
5. GitHub Actions will build and publish to PyPI

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions
- Join our Discord for real-time chat

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
