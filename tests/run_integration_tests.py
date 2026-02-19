#!/usr/bin/env python3
"""
Integration test runner for the cTrader async client.

Runs all integration test suites in a logical order against the demo account
configured in .env (or via environment variables).

Usage
-----
Basic (all suites):
    python tests/run_integration_tests.py

Single suite:
    python tests/run_integration_tests.py --suite risk
    python tests/run_integration_tests.py --suite history
    python tests/run_integration_tests.py --suite market
    python tests/run_integration_tests.py --suite session
    python tests/run_integration_tests.py --suite events
    python tests/run_integration_tests.py --suite core
    python tests/run_integration_tests.py --suite new_features

Verbose / extra pytest args:
    python tests/run_integration_tests.py -v -s --tb=long

Exit codes
----------
0  All suites passed
1  One or more suites failed
2  Pre-flight checks failed (missing .env / credentials)
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_HERE = Path(__file__).resolve().parent          # tests/
_ROOT = _HERE.parent                              # project root
_ENV_FILE = _ROOT / ".env"

# ---------------------------------------------------------------------------
# Suite registry
# Order matters: start with connection/auth, finish with destructive trading.
# ---------------------------------------------------------------------------

SUITES: dict[str, dict] = {
    "core": {
        "label": "Core — Connection, Account, Symbols, Orders, Positions",
        "file": "test_integration.py",
        "description": (
            "Connects to the demo server, verifies auth, exercises all 4 order "
            "types (market/limit/stop/stop-limit), position management, and bulk ops."
        ),
    },
    "new_features": {
        "label": "New Features — Typed Events, Multi-Tick Fanout, Model Bridge",
        "file": "test_integration_new_features.py",
        "description": (
            "Typed TickEvent/ExecutionEvent delivery, multi-symbol fanout streams, "
            "bulk trading helpers, model bridge + state-cache updater."
        ),
    },
    "market": {
        "label": "Market Data — Candles, Ticks, Depth, CandleStream",
        "file": "test_integration_market_data_extended.py",
        "description": (
            "Historical tick data (ProtoOAGetTickDataReq), candles across 6 timeframes, "
            "live tick streaming (single + multi-symbol), fanout, depth stream, "
            "and the fixed CandleStream (delta-decoded prices, correct dispatcher wiring)."
        ),
    },
    "risk": {
        "label": "Risk API — Margin, PnL, Leverage, Margin Calls, Subscriptions",
        "file": "test_integration_risk_api.py",
        "description": (
            "Expected margin, position PnL (client + server realtime), dynamic leverage, "
            "margin call list, update_margin_call, validate_trade_risk, "
            "subscribe_margin_events / subscribe_margin_call_events with real unsubscribe handles."
        ),
    },
    "history": {
        "label": "History API — Deals, Transactions, Orders by Position",
        "file": "test_integration_history_api.py",
        "description": (
            "Deal list (30-day window + post-trade), transaction list, archived order "
            "history, orders by position ID, performance summary."
        ),
    },
    "session": {
        "label": "Session & Assets — Server Version, cTID, Assets, Symbol by ID",
        "file": "test_integration_session_assets.py",
        "description": (
            "Server version, cTID profile, token refresh (if CTRADER_REFRESH_TOKEN set), "
            "full asset catalog, symbol catalog extended methods (by-id, search, categories)."
        ),
    },
    "events": {
        "label": "Event Bus — All Named Events, on/off/once API",
        "file": "test_integration_events_bus.py",
        "description": (
            "Verifies every typed event name the client emits: tick, execution.*, "
            "order.error, account.trader_updated, risk.margin_changed, protobuf.envelope, "
            "and all wired-only events. Also tests EventBus on/off/once semantics."
        ),
    },
}

# ---------------------------------------------------------------------------
# Pre-flight
# ---------------------------------------------------------------------------

REQUIRED_ENV = [
    "CTRADER_CLIENT_ID",
    "CTRADER_CLIENT_SECRET",
    "CTRADER_ACCESS_TOKEN",
    "CTRADER_ACCOUNT_ID",
]


def _load_dotenv() -> None:
    if not _ENV_FILE.exists():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(_ENV_FILE)
    except ImportError:
        # Manual parse for key=value lines
        for line in _ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


def _preflight() -> bool:
    """Check .env presence and required credentials. Returns True if OK."""
    ok = True

    if not _ENV_FILE.exists():
        print("⚠️  .env file not found.")
        print(f"   Copy .env.example → .env and fill in your credentials.")
        print(f"   (looked in: {_ENV_FILE})")
        ok = False
    else:
        print(f"✅ .env file found: {_ENV_FILE}")

    _load_dotenv()

    missing = [k for k in REQUIRED_ENV if not os.getenv(k)]
    if missing:
        print(f"\n❌ Missing required environment variables:")
        for k in missing:
            print(f"   {k}")
        ok = False
    else:
        acct = os.getenv("CTRADER_ACCOUNT_ID", "?")
        host = os.getenv("CTRADER_HOST_TYPE", "demo")
        print(f"✅ Credentials present — account_id={acct}  host={host}")

    return ok


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def _run_suite(
    suite_key: str,
    extra_args: list[str],
    env: dict,
) -> tuple[int, float]:
    """Run a single suite. Returns (returncode, elapsed_seconds)."""
    suite = SUITES[suite_key]
    test_file = _HERE / suite["file"]

    if not test_file.exists():
        print(f"   ⚠️  Test file not found: {test_file} — skipping")
        return 0, 0.0

    cmd = [
        sys.executable, "-m", "pytest",
        str(test_file),
        "--tb=short",
        "-v",
    ] + extra_args

    t0 = time.monotonic()
    result = subprocess.run(cmd, env={**os.environ, **env})
    elapsed = time.monotonic() - t0
    return result.returncode, elapsed


def _banner(text: str, width: int = 72, char: str = "=") -> str:
    return f"\n{char * width}\n  {text}\n{char * width}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--suite", "-s",
        choices=list(SUITES.keys()) + ["all"],
        default="all",
        help="Which test suite to run (default: all)",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available suites and exit",
    )
    parser.add_argument(
        "--fail-fast", "-x",
        action="store_true",
        help="Stop after first suite failure",
    )
    parser.add_argument(
        "--no-preflight",
        action="store_true",
        help="Skip credential pre-flight checks",
    )
    # Remaining args forwarded to pytest
    args, extra_pytest_args = parser.parse_known_args(argv)

    # ── list ──────────────────────────────────────────────────────────────
    if args.list:
        print(_banner("Available integration test suites"))
        for key, meta in SUITES.items():
            print(f"\n  --suite {key}")
            print(f"    {meta['label']}")
            print(f"    File : {meta['file']}")
            print(f"    About: {meta['description']}")
        return 0

    # ── header ────────────────────────────────────────────────────────────
    print(_banner("cTrader Async Client — Integration Test Runner"))
    print(f"  Project root : {_ROOT}")
    print(f"  Tests dir    : {_HERE}")
    print(f"  Suite(s)     : {args.suite}")

    # ── pre-flight ────────────────────────────────────────────────────────
    if not args.no_preflight:
        print(_banner("Pre-flight checks", char="-"))
        if not _preflight():
            print("\n❌ Pre-flight failed. Fix the issues above and retry.")
            return 2
    else:
        _load_dotenv()

    # Integration flag required by conftest.py fixture
    extra_env = {"CTRADER_RUN_INTEGRATION": "true"}

    # ── select suites ─────────────────────────────────────────────────────
    if args.suite == "all":
        selected = list(SUITES.keys())
    else:
        selected = [args.suite]

    # ── run ───────────────────────────────────────────────────────────────
    results: dict[str, tuple[int, float]] = {}
    total_t0 = time.monotonic()

    for key in selected:
        meta = SUITES[key]
        print(_banner(f"Suite: {meta['label']}", char="-"))
        print(f"  {meta['description']}\n")

        rc, elapsed = _run_suite(key, extra_pytest_args, extra_env)
        results[key] = (rc, elapsed)

        status = "✅ PASSED" if rc == 0 else "❌ FAILED"
        print(f"\n  {status}  ({elapsed:.1f}s)")

        if args.fail_fast and rc != 0:
            print("\n  --fail-fast: stopping after first failure.")
            break

    total_elapsed = time.monotonic() - total_t0

    # ── summary ───────────────────────────────────────────────────────────
    print(_banner("Summary"))
    passed = sum(1 for rc, _ in results.values() if rc == 0)
    failed = sum(1 for rc, _ in results.values() if rc != 0)
    skipped_suites = [k for k in selected if k not in results]

    for key, (rc, elapsed) in results.items():
        icon = "✅" if rc == 0 else "❌"
        label = SUITES[key]["label"]
        print(f"  {icon}  {label:<55}  {elapsed:5.1f}s")

    for key in skipped_suites:
        print(f"  ⏭️   {SUITES[key]['label']:<55}  (not reached)")

    print(f"\n  Total: {passed} passed, {failed} failed  —  {total_elapsed:.1f}s")

    if failed:
        print("\n❌ Some suites FAILED. Check output above for details.")
        return 1

    print("\n✅ All suites PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

