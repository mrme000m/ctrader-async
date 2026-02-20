"""Position sizing utilities based on risk management.

Provides functions for calculating position sizes from risk parameters.
"""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING, Optional, Tuple

if TYPE_CHECKING:
    from ..client import CTraderClient

logger = logging.getLogger(__name__)


async def size_from_risk(
    *,
    client: "CTraderClient",
    symbol: str,
    stop_loss_pips: float,
    risk_percent: float,
    use_equity: bool = True,
) -> Optional[float]:
    """Calculate lot size for a given risk percentage and SL distance.
    
    This is the correct way to size positions based on account risk,
    as opposed to margin-based sizing.
    
    Formula: lots = risk_amount / (stop_loss_pips * pip_value)
    
    Args:
        client: CTrader client instance
        symbol: Symbol name (e.g., "EURUSD")
        stop_loss_pips: Stop loss distance in pips
        risk_percent: Maximum risk as % of account (e.g., 2.0 for 2%)
        use_equity: Use equity (True) or balance (False) for calculation
        
    Returns:
        Recommended lot size, or None if calculation fails
        
    Example:
        >>> lots = await size_from_risk(
        ...     client=client,
        ...     symbol="EURUSD",
        ...     stop_loss_pips=50,
        ...     risk_percent=2.0,
        ... )
        >>> print(f"Trade {lots:.2f} lots for 2% risk with 50 pip SL")
        
    Note:
        The returned lot size is snapped to the symbol's volume constraints
        (min_lots, max_lots, step_lots). If the calculated size is below
        minimum, returns 0.0.
    """
    from .pip_value import calculate_pip_value
    
    if risk_percent <= 0 or stop_loss_pips <= 0:
        logger.error("risk_percent and stop_loss_pips must be positive")
        return None
    
    # Get account info
    try:
        account = await client.account.get_info()
        if not account.currency:
            logger.error("Account currency not available")
            return None
    except Exception as e:
        logger.error(f"Failed to get account info: {e}")
        return None
    
    # Get symbol info
    try:
        sym = await client.symbols.get_symbol(symbol)
        if not sym:
            logger.error(f"Symbol not found: {symbol}")
            return None
    except Exception as e:
        logger.error(f"Failed to get symbol: {e}")
        return None
    
    # Calculate risk amount
    base_amount = account.equity if use_equity else account.balance
    risk_amount = base_amount * (risk_percent / 100.0)
    
    # Get pip value for 1 lot
    # Try to get converter from client (fx_converter or asset_converter)
    converter = getattr(client, 'fx_converter', None) or getattr(client, 'asset_converter', None)
    if converter is None:
        logger.error("No asset converter available (client.fx_converter or client.asset_converter)")
        return None
    
    pip_value_per_lot = await calculate_pip_value(
        sym,
        lots=1.0,
        deposit_currency=account.currency,
        converter=converter,
    )
    
    if pip_value_per_lot is None or pip_value_per_lot <= 0:
        logger.error(f"Could not calculate pip value for {symbol}")
        return None
    
    # Calculate risk per lot (SL pips × pip value)
    risk_per_lot = stop_loss_pips * pip_value_per_lot
    
    # Calculate lots
    lots = risk_amount / risk_per_lot
    
    # Get volume constraints
    min_lots, max_lots, step_lots = sym.volume_constraints_lots()
    
    # Snap to constraints
    if min_lots is not None and lots < min_lots:
        logger.warning(f"Calculated lots ({lots:.4f}) below minimum ({min_lots})")
        return 0.0
    
    if max_lots is not None:
        lots = min(lots, max_lots)
    
    if step_lots is not None and step_lots > 0:
        # Round down to nearest step
        lots = math.floor(lots / step_lots) * step_lots
    
    logger.info(
        f"Position sizing: {symbol}, SL={stop_loss_pips}pips, "
        f"Risk={risk_percent}%, Lots={lots:.4f}"
    )
    
    return lots


async def calculate_position_risk(
    *,
    client: "CTraderClient",
    symbol: str,
    volume: float,
    stop_loss_pips: float,
) -> Optional[Tuple[float, float]]:
    """Calculate the actual risk amount and percentage for a position.
    
    Args:
        client: CTrader client instance
        symbol: Symbol name
        volume: Trade volume in lots
        stop_loss_pips: Stop loss distance in pips
        
    Returns:
        Tuple of (risk_amount, risk_percent) or None if calculation fails
    """
    from .pip_value import calculate_pip_value
    
    try:
        account = await client.account.get_info()
        sym = await client.symbols.get_symbol(symbol)
        
        if not sym:
            return None
        
        converter = getattr(client, 'fx_converter', None) or getattr(client, 'asset_converter', None)
        if not converter:
            return None
        
        pip_value = await calculate_pip_value(
            sym,
            lots=volume,
            deposit_currency=account.currency,
            converter=converter,
        )
        
        if pip_value is None:
            return None
        
        risk_amount = stop_loss_pips * pip_value
        risk_percent = (risk_amount / account.equity) * 100.0
        
        return (risk_amount, risk_percent)
        
    except Exception as e:
        logger.error(f"Failed to calculate position risk: {e}")
        return None
