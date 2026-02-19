"""Root conftest — excludes integration test files from collection unless enabled."""
from __future__ import annotations

import os
from pathlib import Path

_INTEGRATION_ENABLED = os.getenv("CTRADER_RUN_INTEGRATION", "").lower() in (
    "1", "true", "yes", "on",
)

_TESTS_DIR = Path(__file__).parent / "tests"

_INTEGRATION_FILES = [
    "test_integration.py",
    "test_integration_new_features.py",
    "test_integration_risk_api.py",
    "test_integration_history_api.py",
    "test_integration_market_data_extended.py",
    "test_integration_session_assets.py",
    "test_integration_events_bus.py",
]

# collect_ignore is read by pytest from the rootdir conftest before collection.
# List the full paths so pytest skips them entirely (no import, no timeout).
if not _INTEGRATION_ENABLED:
    collect_ignore = [str(_TESTS_DIR / f) for f in _INTEGRATION_FILES]

