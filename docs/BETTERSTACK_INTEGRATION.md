# Better Stack: Free Tier — Opportunities for this repo ✅

Summary
- Better Stack offers a useful free tier for open-source and small projects: **10 monitors & heartbeats**, **1 status page**, **3 GB logs (3 days retention)**, **3 GB metrics**, and **100,000 exceptions/month** for error tracking. These map well to the needs of this repo (CI, examples, integration tests, and maintainers).

Why it matters for this repo 🔧
- The repo is a client library with example scripts and scheduled/integration tests. The free-tier features can bring:
  - **Visibility:** uptime monitors + status page for a demo/CI endpoint or hosted docs → public confidence and quick alerting.
  - **Rapid error detection:** Error tracking (Sentry-compatible) captures runtime exceptions from CI runs, examples, or user installations (100k exceptions/mo is generous for an OSS library).
  - **Lightweight logging & telemetry:** 3 GB/month logging is sufficient to capture CI/test logs, example run telemetry, and a few days of live debug logs.
  - **Heartbeats:** ensure scheduled jobs (nightly test runs, cron tasks) are actually running.
  - **On-call / alerts & integrations:** Slack/email alerts for maintainers for failed monitors or high-severity errors.

Recommended services & mapping to repo features ✅
1. Uptime (monitors) & Status Page
   - Use free monitors to watch any important HTTP endpoints we own (e.g., docs site, demo servers, or a small demo webhook) and create one status page (public or private) to show library health.
   - Use monitors for: hosted documentation, demo service REST endpoints, and any API gateway used in examples.

2. Heartbeats
   - Add heartbeats for scheduled tasks such as nightly integration tests or any cron-style scripts in `examples/`.
   - Implement a CI job step that POSTs a heartbeat on success (see implementation below).

3. Error tracking (Sentry-compatible)
   - Use Better Stack Errors as a drop-in replacement for Sentry. Instrument the library's example scripts and any long-running demo process.
   - Capture uncaught exceptions from CI runs (useful to surface flaky/integration errors) and production user errors if consumers opt in.

4. Log ingestion / Telemetry
   - Send structured logs from example scripts and CI runs to Better Stack via the HTTP ingest API, Vector or OpenTelemetry. Use logs to correlate with errors and uptime incidents.
   - Keep logs ephemeral (3-day retention) for troubleshooting while keeping long-term artifacts in CI or a separate archive.

5. Alerts & Integrations
   - Configure Slack/email alerts for failures; integrate incident management if team on-call is needed later.

Implementation pattern (practical, low-effort) — Python-focused 🔧

Environment variables (store in CI secrets / dev env):
- `BETTERSTACK_ERRORS_DSN` (or the Sentry DSN-style URL Better Stack provides for Errors)
- `BETTERSTACK_SOURCE_TOKEN` (for Telemetry/Logs ingestion)
- `BETTERSTACK_INGEST_HOST` (ingest hostname returned by Better Stack)
- `BETTERSTACK_UPTIME_HEARTBEAT_URL` (heartbeat URL from Uptime > Heartbeats)

1) Error tracking (Sentry-compatible)
- Minimal example (integrate into `examples/basic_usage.py` or new `examples/with_error_tracking.py`):

```py
# examples/with_error_tracking.py
import os
import sentry_sdk

DSN = os.getenv('BETTERSTACK_ERRORS_DSN')
if DSN:
    sentry_sdk.init(DSN, traces_sample_rate=0.0)

# rest of example code — exceptions will be captured automatically
```

Notes:
- Better Stack documents that it is Sentry SDK-compatible. Use the same init pattern and DSN.
- Set traces_sample_rate to 0 if you don't want transaction traces, or tune as needed.

2) Log ingestion (HTTP REST)
- Use the HTTP ingest API for concise structured logs from examples and CI. Example helper function to send events:

```py
# src/integrations/betterstack.py
import os
import requests

INGEST_HOST = os.getenv('BETTERSTACK_INGEST_HOST')
SOURCE_TOKEN = os.getenv('BETTERSTACK_SOURCE_TOKEN')

def send_log(event: dict):
    if not INGEST_HOST or not SOURCE_TOKEN:
        return
    url = f"https://{INGEST_HOST}/"
    headers = {
        'Authorization': f'Bearer {SOURCE_TOKEN}',
        'Content-Type': 'application/json'
    }
    try:
        requests.post(url, json=event, headers=headers, timeout=5)
    except Exception:
        # don't raise from helper — failures to report logs mustn't break main flows
        pass
```

- Use this helper in `examples/` and in a CI step to upload run metadata.

3) Heartbeat in CI (GitHub Actions example)
- Add a final job step to POST the heartbeat on success. Example snippet for `.github/workflows/ci.yml`:

```yaml
- name: Send success heartbeat
  if: success()
  run: |
    curl -fsS -X POST "$BETTERSTACK_UPTIME_HEARTBEAT_URL" || true
  env:
    BETTERSTACK_UPTIME_HEARTBEAT_URL: ${{ secrets.BETTERSTACK_UPTIME_HEARTBEAT_URL }}
```

4) Monitor important endpoints via API or web console
- Use the Uptime API (or UI) to add monitors for key URLs (docs site, demo endpoints). The Uptime API is documented in Better Stack docs and supports CRUD for monitors.

5) Optional: OpenTelemetry / Tracing
- If more advanced traces are needed, instrument library or examples with OpenTelemetry -> Better Stack traces. Not necessary on day 1.

Repo-level additions recommended (small, safe changes) 🧩
- Add `docs/BETTERSTACK_INTEGRATION.md` (this file)
- Add `src/integrations/betterstack.py` (log helper + small utilities)
- Add `examples/with_error_tracking.py` (Sentry-style example)
- Add GitHub Actions snippet to send heartbeats on CI success
- Update `README.md` or `CONTRIBUTING.md` with opt-in telemetry guidance and env var usage

Notes on privacy & limits ⚠️
- Free tier retention is short (3 days) for logs; don't rely on it as long-term storage. Ship archive logs to CI artifacts or S3 for long-term needs.
- Use environment variables and **do not** commit tokens. Use repo secrets for CI.
- Error volume limit is 100k exceptions/month on free tier — reasonable for an OSS library but monitor usage.

Quick Implementation roadmap (2–3 small PRs) 🚀
1. PR1: Add `src/integrations/betterstack.py` and `examples/with_error_tracking.py` + docs entry in `README`.
2. PR2: Add GitHub Actions snippet to post heartbeat after integration tests; add CI secret documentation.
3. PR3 (optional): Add log uploads for failing runs (attach logs to Better Stack) and configure monitors/status page.

Why this approach is low-risk and high-value 💡
- Non-invasive: everything is opt-in and based on environment variables/secrets.
- Provides quick operational visibility for maintainers (alerts + monitors + errors) without paid commitment.
- Cheap observability that catches flaky/integration/regression failures faster than manual triage.

References
- Better Stack Logs ingestion docs: https://betterstack.com/docs/logs/ingesting-data/http/logs/
- Better Stack Errors (Sentry-compatible): https://betterstack.com/docs/errors/start/
- Better Stack Uptime Monitoring docs: https://betterstack.com/docs/uptime/monitoring-start/
- Pricing / free-tier summary: https://betterstack.com/pricing

---

If you'd like, I can open a PR that adds the `src/integrations/betterstack.py` helper, `examples/with_error_tracking.py`, and a GitHub Actions heartbeat step. Which change would you like first?