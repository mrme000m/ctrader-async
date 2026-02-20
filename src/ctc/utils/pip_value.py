"""Pip value calculation utilities.

Provides functions for calculating pip values in deposit currency.
"""

from __future__ import annotations

import inspect
import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..models import Symbol
    from .fx_converter import DefaultAssetConverter

logger = logging.getLogger(__name__)


def _get_converter_method(converter):
    """Get the appropriate conversion method from a converter object.
    
    Handles:
    - DefaultAssetConverter (uses convert_async)
    - Objects with async convert() method
    - Objects with convert_async() method
    """
    if converter is None:
        return None
    
    # Prefer convert_async if available (DefaultAssetConverter)
    if hasattr(converter, 'convert_async'):
        return converter.convert_async
    
    # Check if convert is async
    if hasattr(converter, 'convert'):
        if inspect.iscoroutinefunction(converter.convert):
            return converter.convert
        else:
            # Sync convert - wrap in async
            async def async_wrapper(*, amount, from_asset, to_asset):
                return converter.convert(amount=amount, from_asset=from_asset, to_asset=to_asset)
            return async_wrapper
    
    return None


async def calculate_pip_value(
    symbol: "Symbol",
    *,
    lots: float = 1.0,
    deposit_currency: str,
    converter: "DefaultAssetConverter",
) -> Optional[float]:
    """Calculate pip value per lot in deposit currency.
    
    This computes the monetary value of a single pip movement
    for the given symbol and lot size, converted to the
    account's deposit currency.
    
    Args:
        symbol: Trading symbol with pip_size and lot_size_units populated
        lots: Trade volume in lots (default: 1.0)
        deposit_currency: Account deposit currency (e.g., "USD")
        converter: Asset converter for FX rate lookups
        
    Returns:
        Pip value in deposit currency, or None if calculation fails
        
    Example:
        >>> symbol = await client.symbols.get_symbol("EURUSD")
        >>> pip_val = await calculate_pip_value(
        ...     symbol,
        ...     lots=1.0,
        ...     deposit_currency="USD",
        ...     converter=client.fx_converter
        ... )
        >>> print(f"1 pip = ${pip_val:.2f}")
    """
    if not symbol.pip_size or symbol.pip_size <= 0:
        logger.error(f"Invalid pip_size for {symbol.name}: {symbol.pip_size}")
        return None
    
    if not symbol.lot_size_units or symbol.lot_size_units <= 0:
        logger.error(f"Invalid lot_size_units for {symbol.name}: {symbol.lot_size_units}")
        return None
    
    # Base pip value in quote currency
    # pip_size (e.g., 0.0001 for EURUSD) * lot_size_units (e.g., 100000) * lots
    base_pip_value = symbol.pip_size * symbol.lot_size_units * lots
    
    # If quote currency matches deposit currency, no conversion needed
    if symbol.quote_asset_id:
        try:
            quote_asset = await converter.assets.get_asset_by_id(symbol.quote_asset_id)
            if quote_asset and quote_asset.name.upper() == deposit_currency.upper():
                return base_pip_value
        except Exception as e:
            logger.debug(f"Could not get quote asset for {symbol.name}: {e}")
    
    # Need to convert from quote currency to deposit currency
    # Try to get quote currency name
    quote_currency = None
    if symbol.quote_asset_id:
        try:
            quote_asset = await converter.assets.get_asset_by_id(symbol.quote_asset_id)
            if quote_asset:
                quote_currency = quote_asset.name
        except Exception:
            pass
    
    if not quote_currency:
        # Fallback: infer from symbol name (e.g., EURUSD -> USD)
        if len(symbol.name) >= 6:
            quote_currency = symbol.name[3:6]
        else:
            logger.error(f"Cannot determine quote currency for {symbol.name}")
            return None
    
    try:
        convert_method = _get_converter_method(converter)
        if convert_method is None:
            logger.error(f"Converter has no convert/convert_async method: {type(converter)}")
            return None
        converted_value = await convert_method(
            amount=base_pip_value,
            from_asset=quote_currency,
            to_asset=deposit_currency,
        )
        return converted_value
    except Exception as e:
        logger.error(f"Failed to convert pip value: {e}")
        return None
