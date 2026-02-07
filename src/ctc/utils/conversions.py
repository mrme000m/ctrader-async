from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..models import Symbol, Asset


@dataclass(frozen=True)
class Notional:
    """A money amount in a specific asset/currency."""

    asset: str
    value: float


def lots_to_base_units(symbol: Symbol, lots: float) -> float:
    """Convert lots to base asset units (exact by contract spec)."""
    return float(lots) * float(symbol.lot_size_units)


def base_units_to_lots(symbol: Symbol, base_units: float) -> float:
    """Convert base asset units to lots."""
    lot = float(symbol.lot_size_units)
    if lot <= 0:
        raise ValueError("symbol.lot_size_units must be positive")
    return float(base_units) / lot


def base_units_to_quote_notional(*, base_units: float, price: float) -> float:
    """Convert base units to quote-currency notional using price.

    For symbols quoted as BASE/QUOTE, quote_notional = base_units * price.
    """
    if price <= 0:
        raise ValueError("price must be positive")
    return float(base_units) * float(price)


def quote_notional_to_base_units(*, quote_notional: float, price: float) -> float:
    """Convert quote-currency notional to base units using price."""
    if price <= 0:
        raise ValueError("price must be positive")
    return float(quote_notional) / float(price)


def lots_to_quote_notional(symbol: Symbol, *, lots: float, price: float) -> float:
    base_units = lots_to_base_units(symbol, lots)
    return base_units_to_quote_notional(base_units=base_units, price=price)


def quote_notional_to_lots(symbol: Symbol, *, quote_notional: float, price: float) -> float:
    base_units = quote_notional_to_base_units(quote_notional=quote_notional, price=price)
    return base_units_to_lots(symbol, base_units)


def round_money(amount: float, asset: Optional[Asset]) -> float:
    """Round money amount using asset digits if known."""
    if asset is None or asset.digits is None:
        return float(amount)
    return round(float(amount), int(asset.digits))


# Optional provision for deposit currency conversions:
# Users can supply an external converter that knows FX rates between assets.
class AssetConverter:
    def convert(self, *, amount: float, from_asset: str, to_asset: str) -> float:
        raise NotImplementedError


def quote_to_deposit_notional(
    *,
    quote_amount: float,
    quote_asset: str,
    deposit_asset: str,
    converter: Optional[AssetConverter] = None,
) -> float:
    """Convert quote currency notional to deposit currency.

    If no converter is provided and assets differ, raises.
    """
    if quote_asset.upper() == deposit_asset.upper():
        return float(quote_amount)
    if converter is None:
        raise ValueError("No converter provided for quote->deposit conversion")
    return float(converter.convert(amount=float(quote_amount), from_asset=quote_asset, to_asset=deposit_asset))
