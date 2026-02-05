"""Integration test debug helpers.

Only used in opt-in integration tests.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any


def _safe(obj: Any) -> Any:
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    if isinstance(obj, dict):
        return {str(k): _safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_safe(v) for v in obj]
    # fallback: compact repr
    return repr(obj)


def snapshot_client_state(client) -> dict[str, Any]:
    """Return a compact snapshot of caches for debugging."""
    trading = getattr(client, "trading", None)
    snap: dict[str, Any] = {}

    if trading is None:
        return {"trading": None}

    orders = getattr(trading, "_orders", [])
    positions = getattr(trading, "_positions", [])

    snap["orders"] = [
        {
            "id": getattr(o, "id", None),
            "symbol": getattr(o, "symbol_name", None),
            "volume": getattr(o, "volume", None),
            "type": getattr(o, "order_type", None),
            "status": getattr(o, "status", None),
        }
        for o in orders
    ]
    snap["positions"] = [
        {
            "id": getattr(p, "id", None),
            "symbol": getattr(p, "symbol_name", None),
            "volume": getattr(p, "volume", None),
            "side": getattr(p, "side", None),
            "entry": getattr(p, "entry_price", None),
        }
        for p in positions
    ]

    return snap


def dump_debug(label: str, payload: dict[str, Any]) -> str:
    data = {"label": label, **payload}
    return json.dumps(_safe(data), indent=2, sort_keys=True)
