# BetterStack Integration Setup Guide

This guide explains how to set up BetterStack logging and monitoring integration with the cTrader async client.

## Overview

The BetterStack integration is **completely optional** and **zero-impact** if not configured. When enabled, it provides:

- **Structured log ingestion** to BetterStack Logs
- **Automatic error tracking** with stack traces
- **Heartbeat monitoring** for uptime tracking
- **Debug and audit logging** for troubleshooting

## Quick Start

### 1. Sign up for BetterStack

1. Go to [https://betterstack.com](https://betterstack.com)
2. Sign up for a free account (includes 3GB logs/month)
3. Create a new source in the Logs section

### 2. Get your credentials

From your BetterStack dashboard, get:
- **Ingest Host**: e.g., `in.logtail.com`
- **Source Token**: Your unique source token

Optional (for uptime monitoring):
- **Heartbeat URL**: From Uptime > Heartbeats section

### 3. Set environment variables

```bash
export BETTERSTACK_INGEST_HOST="in.logtail.com"
export BETTERSTACK_SOURCE_TOKEN="your_source_token_here"

# Optional: For uptime heartbeat
export BETTERSTACK_UPTIME_HEARTBEAT_URL="https://uptime.betterstack.com/..."
```

### 4. Enable in your code

**Option A: Auto-enable via environment**
```python
import ctc

# BetterStack is auto-enabled if env vars are set
client = ctc.CTraderClient(
    client_id="...",
    client_secret="...",
    access_token="...",
    account_id=12345,
    betterstack_enabled=True,  # Enable BetterStack
)
```

**Option B: Manual setup**
```python
from ctc.integrations import setup_betterstack_logging

# Setup BetterStack logging
setup_betterstack_logging(level=logging.INFO)

# Or get the handler for more control
handler = setup_betterstack_logging()
```

## Configuration Options

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BETTERSTACK_INGEST_HOST` | BetterStack ingest host (e.g., `in.logtail.com`) | Yes |
| `BETTERSTACK_SOURCE_TOKEN` | Your BetterStack source token | Yes |
| `BETTERSTACK_UPTIME_HEARTBEAT_URL` | Heartbeat URL for uptime monitoring | No |
| `BETTERSTACK_LOG_LEVEL` | Minimum log level to send (default: `INFO`) | No |
| `BETTERSTACK_SERVICE_NAME` | Service identifier (default: `ctrader-client`) | No |
| `BETTERSTACK_ENVIRONMENT` | Environment name (default: `development`) | No |

### Client Configuration

```python
from ctc import CTraderClient

client = CTraderClient(
    # ... credentials ...
    
    # BetterStack options
    betterstack_enabled=True,
    betterstack_ingest_host="in.logtail.com",
    betterstack_source_token="your_token",
    betterstack_log_level="INFO",
    betterstack_service_name="my-trading-bot",
    betterstack_environment="production",
)
```

## Usage Examples

### Basic Integration

```python
import asyncio
import logging
import ctc

async def main():
    # BetterStack is auto-configured if env vars are set
    async with ctc.CTraderClient(
        client_id="...",
        client_secret="...",
        access_token="...",
        account_id=12345,
        host_type="demo",
        betterstack_enabled=True,
    ) as client:
        
        # All logs automatically sent to BetterStack
        logging.info("Trading started")
        
        # Your trading code here...
        
# Run
asyncio.run(main())
```

### Manual Log Sending

```python
from ctc.integrations import send_betterstack_log

# Send a custom log event
await send_betterstack_log({
    "message": "Custom event occurred",
    "level": "info",
    "event": "custom.event",
    "metadata": {"key": "value"},
})
```

### Error Tracking

```python
from ctc.integrations import capture_betterstack_exception

try:
    risky_operation()
except Exception:
    # Capture and send exception to BetterStack
    await capture_betterstack_exception()
    raise
```

### Heartbeat Monitoring

```python
from ctc.integrations import send_betterstack_heartbeat

# Send heartbeat (if BETTERSTACK_UPTIME_HEARTBEAT_URL is set)
await send_betterstack_heartbeat()
```

## Advanced Usage

### Custom Configuration

```python
from ctc.integrations import BetterStackConfig, BetterStackHandler

# Create custom configuration
config = BetterStackConfig(
    ingest_host="in.logtail.com",
    source_token="your_token",
    log_level="DEBUG",
    service_name="my-bot",
    environment="staging",
    batch_size=10,  # Batch logs before sending
    flush_interval_seconds=5.0,
)

# Create handler
handler = BetterStackHandler(config)
await handler.initialize()

# Use handler directly
await handler.send_log({
    "message": "Custom log",
    "level": "info",
})

# Shutdown
await handler.shutdown()
```

### Python Logging Handler

```python
import logging
from ctc.integrations import BetterStackLogHandler, BetterStackConfig

# Create handler
config = BetterStackConfig.from_env()
handler = BetterStackLogHandler(config)
handler.setLevel(logging.INFO)

# Add to logger
logger = logging.getLogger("my_logger")
logger.addHandler(handler)

# Logs now sent to BetterStack
logger.info("This goes to BetterStack")
```

### With Debug Mode

```python
import ctc

# Enable debug mode for more verbose logging
ctc.set_debug_mode(True)

# Now both console and BetterStack get debug logs
async with ctc.CTraderClient(...) as client:
    # Debug logs automatically sent to BetterStack
    pass
```

## Troubleshooting

### Check if BetterStack is enabled

```python
from ctc.integrations import betterstack_enabled

if betterstack_enabled():
    print("✅ BetterStack is configured")
else:
    print("❌ BetterStack not configured - check env vars")
```

### Verify configuration

```python
from ctc.integrations import BetterStackConfig

config = BetterStackConfig.from_env()
print(config.to_dict())  # Sanitized output
```

### Debug logging issues

```python
import logging

# Enable debug logging for BetterStack module
logging.getLogger("ctc.integrations.betterstack").setLevel(logging.DEBUG)
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Logs not appearing | Check `BETTERSTACK_INGEST_HOST` and `BETTERSTACK_SOURCE_TOKEN` |
| Connection timeouts | Check network connectivity to BetterStack |
| Missing logs | Verify `BETTERSTACK_LOG_LEVEL` setting |
| Heartbeat not working | Check `BETTERSTACK_UPTIME_HEARTBEAT_URL` is correct |

## Privacy and Security

- **Never commit tokens** to version control
- Use environment variables or secure secret management
- The integration fails silently if misconfigured (won't crash your app)
- Logs are sent over HTTPS
- Review BetterStack's privacy policy at https://betterstack.com/privacy

## Pricing

BetterStack offers a generous free tier:
- **3 GB logs/month** with 3-day retention
- **100,000 exceptions/month**
- **10 monitors & heartbeats**
- **1 status page**

See [BetterStack Pricing](https://betterstack.com/pricing) for details.

## Support

- BetterStack Docs: https://betterstack.com/docs
- BetterStack Support: https://betterstack.com/community
- cTrader Client Issues: https://github.com/yourusername/ctrader-async/issues

## References

- [BetterStack Logs Ingestion](https://betterstack.com/docs/logs/ingesting-data/http/logs/)
- [BetterStack Errors](https://betterstack.com/docs/errors/start/)
- [BetterStack Uptime](https://betterstack.com/docs/uptime/monitoring-start/)
