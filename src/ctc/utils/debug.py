"""Runtime debug flags controlled via environment variables.

These flags are read at runtime (and cached) so users can enable extra diagnostics
without code changes.

Environment variables:
- CTRADER_CONNECTION_DEBUG: if truthy, emit more connection/reconnect logs at INFO/WARNING
  instead of DEBUG.

Truthiness: 1, true, yes, on (case-insensitive).
"""

from __future__ import annotations

import os
from functools import lru_cache


def _is_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@lru_cache(maxsize=1)
def connection_debug_enabled() -> bool:
    return _is_truthy(os.getenv("CTRADER_CONNECTION_DEBUG"))
