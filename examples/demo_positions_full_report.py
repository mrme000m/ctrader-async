"""Dump an extended positions report that mirrors the "Positions for Today" grid.

Exports every open position with the columns the cTrader web UI shows (ID, creation
and modification times, margin, entry/TP/SL, PnL numbers, label/comment, etc.) so
you can consume it in spreadsheets or pipelines. The script also includes the
conversion fee, closing commission and a placeholder for the UI-level "Reset to
default" column.

Credentials are read from the environment to keep secrets out of the repository:
- CTC_CLIENT_ID
- CTC_CLIENT_SECRET
- CTC_ACCESS_TOKEN
- CTC_ACCOUNT_ID

Optionally set CTC_HOST_TYPE=live when you want to run against a live account
instead of the demo server.
"""

import asyncio
import csv
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Optional, Sequence, Tuple

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None

if load_dotenv:
    load_dotenv()

from ctc import CTraderClient
from ctc.messages.OpenApiMessages_pb2 import (
    ProtoOAReconcileReq,
    ProtoOAGetPositionUnrealizedPnLReq,
)
from ctc.messages.OpenApiModelMessages_pb2 import ProtoOATradeSide

TARGET_TZ = timezone(timedelta(hours=6))  # UTC+6 shipping timezone
HEADER = [
    "ID",
    "V Created (UTC+6)",
    "Last modification time (UTC+6)",
    "V Margin",
    "V Symbol",
    "V Quantity",
    "Volume / Direction",
    "V Entry",
    "V TP",
    "V SL",
    "Swap",
    "v Commissions",
    "Closing Commissions",
    "Unrealised Conversion Fee",
    "Channel",
    "Label",
    "Comment",
    "Pips",
    "Gross USD",
    "V Net USD",
    "Reset to default",
]


ENV_PREFIXES = ("CTC", "CTRADER")


def _prefixed_env(key: str) -> Optional[str]:
    for prefix in ENV_PREFIXES:
        value = os.environ.get(f"{prefix}_{key}")
        if value:
            return value
    return None


def _require_env(key: str) -> str:
    value = _prefixed_env(key)
    if not value:
        env_names = ", ".join(f"{prefix}_{key}" for prefix in ENV_PREFIXES)
        raise SystemExit(f"Please set one of the environment variables: {env_names}.")
    return value


def _format_timestamp(ms: Optional[int]) -> str:
    if not ms:
        return ""
    dt = datetime.fromtimestamp(ms / 1000.0, timezone.utc).astimezone(TARGET_TZ)
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z")


def _format_money(value: Optional[float], digits: int) -> str:
    if value is None:
        return ""
    return f"{value:.{digits}f}"


def _format_price(value: Optional[float], digits: int) -> str:
    if value is None or value == 0:
        return ""
    return f"{value:.{digits}f}"


def _parse_side(trade_data: Any) -> str:
    side_val = getattr(trade_data, "tradeSide", None)
    if side_val is None:
        return "UNKNOWN"
    try:
        return ProtoOATradeSide.Name(int(side_val))
    except Exception:
        return str(side_val)


async def _fetch_unrealized_pnl_map(
    client: CTraderClient,
) -> Tuple[Mapping[int, Tuple[float, float]], int]:
    req = ProtoOAGetPositionUnrealizedPnLReq()
    req.ctidTraderAccountId = client.config.account_id

    response = await client._protocol.send_request(
        req,
        timeout=client.config.request_timeout,
        request_type="PositionUnrealizedPnL",
    )

    money_digits = int(getattr(response, "moneyDigits", 2) or 2)
    divisor = 10 ** money_digits

    pnl_entries = list(getattr(response, "positionUnrealizedPnL", []) or [])
    return (
        {
            int(getattr(entry, "positionId", 0) or 0): (
                float(getattr(entry, "grossUnrealizedPnL", 0) or 0) / divisor,
                float(getattr(entry, "netUnrealizedPnL", 0) or 0) / divisor,
            )
            for entry in pnl_entries
        },
        money_digits,
    )


async def _build_position_rows(client: CTraderClient) -> Sequence[Sequence[str]]:
    symbol_cache: dict[int, Any] = {}
    pnl_map, pnl_digits = await _fetch_unrealized_pnl_map(client)

    req = ProtoOAReconcileReq()
    req.ctidTraderAccountId = client.config.account_id

    response = await client._protocol.send_request(
        req,
        timeout=client.config.request_timeout,
        request_type="Reconcile",
    )

    rows: list[list[str]] = []

    for pos in getattr(response, "position", []) or []:
        trade_data = getattr(pos, "tradeData", None)
        position_id = int(getattr(pos, "positionId", 0) or 0)

        symbol_id = int(getattr(trade_data, "symbolId", 0) or 0) if trade_data else 0
        symbol_info = symbol_cache.get(symbol_id)
        if symbol_id and symbol_info is None:
            symbol_info = await client.symbols.get_symbol_by_id(symbol_id)
            symbol_cache[symbol_id] = symbol_info

        volume_proto = int(getattr(trade_data, "volume", 0) or 0)
        if volume_proto and symbol_info:
            volume = symbol_info.protocol_volume_to_lots(volume_proto)
        elif volume_proto:
            volume = float(volume_proto) / 100.0
        else:
            volume = 0.0

        money_digits = int(getattr(pos, "moneyDigits", 2) or 2)
        divisor = 10 ** money_digits

        swap = float(getattr(pos, "swap", 0) or 0) / divisor
        commission = float(getattr(pos, "commission", 0) or 0) / divisor
        closing_commission = float(getattr(pos, "mirroringCommission", 0) or 0) / divisor
        used_margin_raw = getattr(pos, "usedMargin", None)
        used_margin = (
            float(used_margin_raw) / divisor
            if used_margin_raw is not None
            else None
        )

        entry_price = float(getattr(pos, "price", 0) or 0)
        stop_loss = float(getattr(pos, "stopLoss", 0) or 0) or None
        take_profit = float(getattr(pos, "takeProfit", 0) or 0) or None
        created_ts = int(getattr(trade_data, "openTimestamp", 0) or 0) if trade_data else None
        modified_ts = int(getattr(pos, "utcLastUpdateTimestamp", 0) or 0) or None

        side_name = _parse_side(trade_data)
        volume_direction = f"{volume:.2f} / {side_name}" if volume else ""

        channel_value = getattr(trade_data, "channel", None)
        channel = str(channel_value) if channel_value is not None else ""

        label = (str(getattr(trade_data, "label", "")) if trade_data else "").strip()
        comment = (
            str(getattr(trade_data, "comment", "")) if trade_data else ""
        ).strip()

        pnl_entry = pnl_map.get(position_id, (0.0, 0.0))
        gross = pnl_entry[0]
        net = pnl_entry[1]
        conversion_fee = gross - net - swap - commission

        pip_value_total = None
        if symbol_info and symbol_info.pip_size and symbol_info.lot_size_units and volume:
            pip_value_per_lot = symbol_info.pip_size * symbol_info.lot_size_units
            if pip_value_per_lot:
                pip_value_total = pip_value_per_lot * volume
        if pip_value_total:
            pips = gross / pip_value_total
            pips_text = f"{pips:+.2f}"
        else:
            pips_text = ""

        price_digits = symbol_info.digits if symbol_info and symbol_info.digits else 5
        rows.append([
            str(position_id),
            _format_timestamp(created_ts),
            _format_timestamp(modified_ts),
            _format_money(used_margin, money_digits),
            symbol_info.name if symbol_info else str(symbol_id),
            f"{volume:.2f}",
            volume_direction,
            _format_price(entry_price, price_digits),
            _format_price(take_profit, price_digits),
            _format_price(stop_loss, price_digits),
            _format_money(swap, money_digits),
            _format_money(commission, money_digits),
            _format_money(closing_commission, money_digits),
            _format_money(conversion_fee, money_digits),
            channel,
            label,
            comment,
            pips_text,
            _format_money(gross, pnl_digits),
            _format_money(net, pnl_digits),
            "",
        ])

    return rows


async def main() -> None:
    client_id = _require_env("CLIENT_ID")
    client_secret = _require_env("CLIENT_SECRET")
    access_token = _require_env("ACCESS_TOKEN")
    account_id_str = _require_env("ACCOUNT_ID")
    try:
        account_id = int(account_id_str)
    except ValueError:
        raise SystemExit("CTC_ACCOUNT_ID must be an integer")

    host_type = _prefixed_env("HOST_TYPE") or "demo"

    async with CTraderClient(
        client_id=client_id,
        client_secret=client_secret,
        access_token=access_token,
        account_id=account_id,
        host_type=host_type,
    ) as client:
        rows = await _build_position_rows(client)

    writer = csv.writer(sys.stdout)
    writer.writerow(HEADER)
    if not rows:
        print("No open positions returned by the server.")
    else:
        for row in rows:
            writer.writerow(row)


if __name__ == "__main__":
    asyncio.run(main())
