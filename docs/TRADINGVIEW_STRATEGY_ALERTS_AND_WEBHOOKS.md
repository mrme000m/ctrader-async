# TradingView Strategy Alerts & Webhooks — Integration Guide 🔧💡

## Purpose
This document summarizes how TradingView Pine Script strategies can produce alerts suitable for automation via webhooks and lists concrete implementation guidance for extending this client to support strategy‑based signals for automated trade execution.

---

## Key concepts (summary) ✅
- Strategies produce two main types of script alert events:
  - Order fill events (recommended for automation): generated when the broker emulator executes an order. They fire *immediately* when the simulated/order fills and are not constrained by strategy "calc_on_every_tick" timing.
  - alert() function calls: flexible and dynamic; in strategies they default to triggering at bar close unless `calc_on_every_tick = true` is used.
- Customizing order alerts:
  - Use the `alert_message` parameter on `strategy.entry()`, `strategy.exit()`, `strategy.order()` calls to include a custom per-order message.
  - Alternatively, use the `//@strategy_alert_message` compiler annotation to set a default message template (placeholders supported).
  - When creating the alert in TradingView UI, include the `{{strategy.order.alert_message}}` placeholder in the Alert Message field to ensure your `alert_message` contents are delivered.
- Placeholders: TradingView supports placeholders in messages (e.g. `{{ticker}}`, `{{time}}`, `{{plot("RSI")}}`, and strategy-specific placeholders like `{{strategy.order.action}}`, `{{strategy.order.price}}`, `{{strategy.position_size}}`). Use placeholders to build structured messages (prefer JSON).
- Frequency and recalculation:
  - Order-fill alerts are not limited by `calc_on_every_tick` and trigger on execution time.
  - alert() calls in strategies use `alert.freq_once_per_bar_close` by default unless `calc_on_every_tick` is enabled.
- Important caveats:
  - Alerts are run on TradingView’s servers using a snapshot of script + inputs at alert creation time. Updating script inputs requires creating a new alert.
  - `process_orders_on_close = true` may cause alerts to trigger after market close — be cautious for real-world order execution.
  - Repainting risks: prefer bar-close frequency when you need reliability over immediacy.

---

## Best practice for automation (recommended) ⚠️✅
1. Author strategy to use order-based alerts for execution-critical signals. Use `alert_message` per order (or `@strategy_alert_message`) and make that message a compact, predictable JSON payload.
2. Keep the payload deterministic and include: action, symbol/ticker, side, qty/qty_percent, order_type (market/limit/stop), price (if applicable), order id (if you set one), and a timestamp.
3. In TradingView's "Create Alert" dialog for the strategy, select the strategy and enable **Order fills** (and optionally script `alert()` events if you want additional non-order signals). In the Message field add `{{strategy.order.alert_message}}` (or full JSON with placeholders).
4. Test alerts thoroughly with a paper endpoint / staging webhook URL before live trading. Validate behavior for stop/limit (fills may occur later or never), partial fills, and market hours.

---

## Example Pine snippets
### 1) Set a default annotation message
```pinescript
// @strategy_alert_message {"action":"{{strategy.order.action}}","symbol":"{{ticker}}","side":"{{strategy.order.action}}","size":"{{strategy.position_size}}","price":"{{strategy.order.price}}","id":"{{strategy.order.id}}"}
strategy("Alert Message Demo")
// ... strategy logic ...
```
Note: the annotation sets the default message that will be available as `{{strategy.order.alert_message}}` in the Create Alert dialog.

### 2) Per-order alert_message (dynamic)
```pinescript
if ta.crossover(fast, slow)
    strategy.entry("Long", strategy.long, qty=1, alert_message='{"type":"order","side":"buy","symbol":"' + ticker + '","price":' + str.tostring(strategy.opentrades.entry_price(0)) + '}')
```
When creating an alert on order fills, the user should include `{{strategy.order.alert_message}}` in the Message field so the JSON is sent when the order fills.

### 3) Using alert() for non‑order warnings
```pinescript
// only for non-execution warnings, not replacements for order-fill alerts
if divergingCondition
    alert('WARNING: Divergence detected: ' + str.tostring(rsi), alert.freq_once_per_bar_close)
```

---

## Webhook / Receiver design recommendations (server side) 🛡️
- Endpoint design
  - Provide a secure endpoint (HTTPS) like POST /webhooks/tradingview/{integration_key}
  - Keep the URL secret (users paste it into TradingView as the webhook URL). Optionally support a header-based shared secret or HMAC verification if you choose to include a secret token in the TradingView Message.
- Message parsing
  - Expect two common patterns:
    1. JSON produced by `{{strategy.order.alert_message}}` already containing structured fields.
    2. Free-form messages built from placeholders — parse safely using a tolerant JSON extractor or fall back to regex/key=value parsing.
  - Always validate fields: symbol, side, quantity, price, timestamp.
- Idempotency & deduplication
  - TradingView may re-send alerts in network glitches; support dedup keys (e.g., hash of message + timestamp) and idempotency checks.
- Safety checks before execution
  - Map TradingView ticker → exchange/symbol used by your broker client.
  - Sanity check sizes and prices (apply limits and maximum order size caps).
  - Enforce risk rules and do not execute unverified messages blindly.
- Audit & observability
  - Log inbound alerts, parsed payload, validation steps, and rejection reasons.
  - Provide replay or manual re-try for failed executions.

---

## Recommended features to add to this client (actionable checklist) 📋
1. Webhook receiver service (script or small HTTP server) with basic authentication and TLS support. ✅
2. Robust message parser that supports both explicit JSON `{{strategy.order.alert_message}}` payloads and fallback parsing for placeholder-based messages. ✅
3. Mapping layer: TradingView ticker → repo symbol, quantity rules, allowed order types. ✅
4. Execution worker that converts parsed alert into internal order requests (with safe rate limiting and pre-execution checks). ✅
5. Tests: unit tests for parsing, integration tests with a test webhook URL and a mocked broker. ✅
6. Example repo script to deploy a webhook receiver for local development (ngrok instructions or equivalent). ✅

---

## Caveats & gotchas (short) ⚠️
- Order fill alerts are the most reliable for automated execution (they fire at fill time), whereas alert() in strategies typically triggers at bar close unless `calc_on_every_tick` is used.
- `process_orders_on_close` can delay alerting until bar close — avoid for intraday execution unless intentional.
- Alerts are executed by TradingView servers using a *snapshot* of the script + inputs at alert creation time. Recreate alerts after changing script inputs.
- Stop/limit orders may not execute immediately (or at all); design your execution logic accordingly.

---

## Quick checklist for a safe automation flow ✅
1. Build strategy that sets `alert_message` with structured JSON.
2. Create strategy alert in TradingView, include "Order fills" and set Message to `{{strategy.order.alert_message}}` (or embed it inside a larger JSON wrapper).
3. Use an HTTPS webhook URL with a unique secret for exposure minimization.
4. Validate inbound messages, map symbols and sizes, enforce risk checks, then execute via broker API.
5. Log and monitor every step; run live tests in a paper account first.

---

## References
- TradingView Pine Script — Alerts (concepts): https://www.tradingview.com/pine-script-docs/concepts/alerts/
- TradingView Pine Script — Strategies (concepts): https://www.tradingview.com/pine-script-docs/concepts/strategies/

---

If you'd like, I can also:
- Add a minimal webhook receiver script under `scripts/` and unit tests for message parsing, or
- Add example strategies (Pine v6) to the `examples/` directory that include `alert_message` JSON templates and test instructions.

Choose one and I’ll scaffold the code and tests next. ✨