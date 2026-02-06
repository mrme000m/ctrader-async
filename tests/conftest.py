"""Pytest configuration for ctc integration tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import pytest_asyncio


def _load_dotenv_if_present() -> None:
    """Load .env file if python-dotenv is installed and file exists."""
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return

    try:
        from dotenv import load_dotenv

        load_dotenv(env_path)
    except Exception:
        # dotenv is optional; if missing, rely on environment variables
        pass


_load_dotenv_if_present()


@pytest_asyncio.fixture
async def client():
    """Create and connect a client for integration tests.

    Integration tests are opt-in to keep CI/local runs fast and deterministic.

    Enable by setting:
        CTRADER_RUN_INTEGRATION=true

    And providing required credentials in env (.env supported).
    """
    if os.getenv("CTRADER_RUN_INTEGRATION", "").lower() not in ("1", "true", "yes", "on"):
        pytest.skip("Integration tests disabled (set CTRADER_RUN_INTEGRATION=true to enable)")

    # Basic credential presence check
    required = [
        "CTRADER_CLIENT_ID",
        "CTRADER_CLIENT_SECRET",
        "CTRADER_ACCESS_TOKEN",
        "CTRADER_ACCOUNT_ID",
    ]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        pytest.skip(f"Missing integration env vars: {', '.join(missing)}")

    from ctc import CTraderClient

    client = CTraderClient.from_env()

    try:
        await client.connect()
        yield client
    finally:
        # Cleanup: close all positions and cancel all orders
        try:
            if client.is_ready and client.trading is not None:
                await client.trading.close_all_positions()
                await client.trading.cancel_all_orders()
        except Exception:
            pass

        await client.disconnect()
