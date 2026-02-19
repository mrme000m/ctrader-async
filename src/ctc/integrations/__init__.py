"""
Integrations for cTrader async client.

This module provides optional integrations with third-party services
like BetterStack for logging, monitoring, and error tracking.

All integrations are opt-in and have zero impact if not configured.
"""

from __future__ import annotations

# BetterStack integration - only available if configured
from .betterstack import (
    BetterStackHandler,
    BetterStackConfig,
    BetterStackLogHandler,
    setup_betterstack_logging,
    betterstack_enabled,
    send_betterstack_log,
    send_betterstack_heartbeat,
    capture_betterstack_exception,
)

__all__ = [
    # BetterStack logging and monitoring
    "BetterStackHandler",
    "BetterStackConfig",
    "BetterStackLogHandler",
    "setup_betterstack_logging",
    "betterstack_enabled",
    "send_betterstack_log",
    "send_betterstack_heartbeat",
    "capture_betterstack_exception",
]
