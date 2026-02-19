# Security Policy

## Supported Versions

The following versions of `ctrader-async` are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report security vulnerabilities via email to: **security@yourproject.com**

Include the following details in your report:

- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the vulnerability
- Suggested fix (if any)

### Response Timeline

We will acknowledge receipt of your vulnerability report within **48 hours** and will send a more detailed response within **5 business days** indicating the next steps in handling your report.

After the initial reply to your report, we will endeavor to keep you informed of the progress towards a fix and full announcement, and may ask for additional information or guidance.

### Disclosure Policy

When we receive a security bug report, we will:

1. Confirm the problem and determine the affected versions
2. Audit code to find any similar problems
3. Prepare fixes for all supported versions
4. Release new versions as soon as possible
5. Publicly disclose the issue after the fix is released

## Security Best Practices

When using `ctrader-async`, please follow these security guidelines:

### Credential Management

- **Never hardcode credentials** in your source code
- Use environment variables or secure secret management systems
- Keep your `.env` file out of version control (it's already in `.gitignore`)
- Rotate access tokens regularly
- Use the token refresh functionality instead of long-lived tokens

```python
# Good: Using environment variables
import os
from ctc import CTraderClient

client = CTraderClient(
    client_id=os.environ["CTRADER_CLIENT_ID"],
    client_secret=os.environ["CTRADER_CLIENT_SECRET"],
    access_token=os.environ["CTRADER_ACCESS_TOKEN"],
    account_id=int(os.environ["CTRADER_ACCOUNT_ID"]),
)

# Bad: Hardcoding credentials
client = CTraderClient(
    client_id="12345",  # DON'T DO THIS
    client_secret="secret123",  # DON'T DO THIS
    access_token="token123",  # DON'T DO THIS
    account_id=12345,
)
```

### TLS/SSL

- TLS is enabled by default (`use_tls=True`)
- Never disable TLS in production environments
- The client uses Python's default SSL context with certificate validation

### Network Security

- The client connects to official cTrader API endpoints only
- Demo: `demo.ctraderapi.com:5035`
- Live: `live.ctraderapi.com:5035`
- Be cautious when using WebSocket transport through proxies

### Token Security

- Access tokens expire after a limited time (typically 1 hour)
- Use refresh tokens to obtain new access tokens
- Store refresh tokens securely
- Enable token auto-refresh for long-running applications:

```python
client = CTraderClient(
    ...,
    refresh_token="your_refresh_token",
    token_auto_refresh_enabled=True,
    token_refresh_margin_seconds=60,
)
```

### Logging and Debugging

- Be careful when enabling debug logging in production
- Debug logs may contain sensitive information (tokens, account details)
- Use structured JSON logging for better security monitoring

```python
client = CTraderClient(
    ...,
    log_level="INFO",  # Use DEBUG only for development
    log_format="json",  # Better for security monitoring
)
```

### Rate Limiting

The client includes built-in rate limiting to prevent accidental abuse:
- Trading operations: 50 requests/second
- Historical data: 5 requests/second

These defaults help prevent your account from being rate-limited or blocked.

## Known Security Considerations

### Dependencies

This project depends on:
- `protobuf` - Protocol buffer serialization
- `typing_extensions` - Backport of typing features
- `websockets` (optional) - WebSocket transport

We monitor these dependencies for security vulnerabilities. Please ensure you keep your dependencies up to date:

```bash
pip install --upgrade ctrader-async
```

### SSL Certificate Validation

The client uses Python's default SSL context which validates server certificates. If you encounter SSL errors:

1. Check your system's CA certificates are up to date
2. Ensure your system time is correctly set
3. Do NOT disable certificate validation in production

### OAuth Flow

When implementing OAuth:

1. Use HTTPS redirect URIs in production
2. Validate the state parameter to prevent CSRF attacks
3. Store tokens securely (never in client-side code)
4. Implement proper token refresh logic

```python
from ctc.auth import OAuthHelper

oauth = OAuthHelper(
    client_id="...",
    client_secret="...",
    redirect_uri="https://yourapp.com/callback"  # Use HTTPS
)

# Generate state for CSRF protection
import secrets
state = secrets.token_urlsafe(32)

auth_url = oauth.get_auth_uri(state=state)
# ... redirect user ...

# Verify state on callback
if callback_state != stored_state:
    raise SecurityError("Invalid state parameter")
```

## Security-Related Configuration

| Option | Default | Security Impact |
|--------|---------|-----------------|
| `use_tls` | `True` | Always keep `True` in production |
| `verify_ssl` | `True` | Always keep `True` in production |
| `log_level` | `"INFO"` | Use `"DEBUG"` only for development |
| `drop_inbound_when_full` | `False` | Set `True` for DoS protection |

## Contact

For security-related questions or concerns, please contact:

- Email: security@yourproject.com
- Please allow 48 hours for a response

## Acknowledgments

We thank the following individuals for responsibly disclosing security issues:

- *No disclosures yet*

---

Last updated: 2024-02-19
