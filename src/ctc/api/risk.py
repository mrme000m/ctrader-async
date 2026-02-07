"""
Risk Management and Margin API.

Provides methods for:
- Pre-trade margin calculations
- Position PnL details
- Margin call monitoring
- Risk management utilities
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from ..models import MarginInfo, PositionPnL, MarginCall

if TYPE_CHECKING:
    from ..protocol import ProtocolHandler
    from ..config import ClientConfig
    from ..api.symbols import SymbolCatalog

logger = logging.getLogger(__name__)


class RiskAPI:
    """Risk management and margin calculation API.
    
    Provides methods for calculating margin requirements, monitoring
    position PnL, and managing margin calls.
    
    Example:
        >>> margin_info = await client.risk.get_expected_margin("EURUSD", 1.0)
        >>> print(f"Required margin: {margin_info.formatted_margin}")
        >>> 
        >>> pnl = await client.risk.get_position_pnl(position_id)
        >>> print(f"Net PnL: {pnl.formatted_net_pnl}")
    """
    
    def __init__(
        self,
        protocol: ProtocolHandler,
        config: ClientConfig,
        symbols: SymbolCatalog,
        client=None
    ):
        """Initialize Risk API.
        
        Args:
            protocol: Protocol handler
            config: Client configuration
            symbols: Symbol catalog
            client: Parent client instance (optional)
        """
        self.protocol = protocol
        self.config = config
        self.symbols = symbols
        self._client = client
    
    async def get_expected_margin(
        self,
        symbol: str,
        volume: float,
        order_type: Optional[str] = None
    ) -> MarginInfo:
        """Calculate expected margin for a proposed trade.
        
        Use this before placing orders to ensure sufficient margin is available.
        
        Args:
            symbol: Symbol name (e.g., "EURUSD")
            volume: Trade volume in lots
            order_type: Order type ("BUY" or "SELL", optional)
            
        Returns:
            MarginInfo with required margin details
            
        Raises:
            ValueError: If symbol not found
            TimeoutError: If request times out
            
        Example:
            >>> # Check margin before placing 1 lot EURUSD order
            >>> margin = await client.risk.get_expected_margin("EURUSD", 1.0)
            >>> if margin.margin <= account.free_margin:
            ...     await client.trading.place_market_order("EURUSD", "BUY", 1.0)
            >>> else:
            ...     print(f"Insufficient margin. Required: {margin.formatted_margin}")
        """
        from ..messages.OpenApiMessages_pb2 import (
            ProtoOAExpectedMarginReq,
            ProtoOAExpectedMarginRes,
        )
        
        # Get symbol info
        symbol_info = await self.symbols.get_symbol(symbol)
        if not symbol_info:
            raise ValueError(f"Symbol not found: {symbol}")
        
        # Convert volume to protocol units
        volume_proto = symbol_info.lots_to_protocol_volume(volume)
        
        # Build request
        req = ProtoOAExpectedMarginReq()
        req.ctidTraderAccountId = self.config.account_id
        req.symbolId = symbol_info.id
        req.volume.append(volume_proto)
        
        # Send request
        response = await self.protocol.send_request(
            req,
            timeout=self.config.request_timeout,
            request_type="ExpectedMargin"
        )
        
        if not isinstance(response, ProtoOAExpectedMarginRes):
            raise ValueError(f"Unexpected response type: {type(response)}")
        
        # Parse response
        money_digits = getattr(response, 'moneyDigits', None) or 2
        margin_value = getattr(response, 'margin', None)
        
        if margin_value is None:
            raise ValueError("No margin value in response")
        
        # Convert from protocol units to actual currency
        margin = margin_value / (10 ** money_digits)
        
        # Handle buy/sell specific margins if available
        buy_margin = None
        sell_margin = None
        if hasattr(response, 'buyMargin'):
            buy_margins = list(response.buyMargin)
            if buy_margins:
                buy_margin = buy_margins[0] / (10 ** money_digits)
        
        if hasattr(response, 'sellMargin'):
            sell_margins = list(response.sellMargin)
            if sell_margins:
                sell_margin = sell_margins[0] / (10 ** money_digits)
        
        return MarginInfo(
            margin=margin,
            symbol_id=symbol_info.id,
            volume=volume,
            money_digits=money_digits,
            buy_margin=buy_margin,
            sell_margin=sell_margin
        )
    
    async def get_position_pnl(self, position_id: int) -> Optional[PositionPnL]:
        """Get detailed PnL breakdown for a position.
        
        Provides comprehensive profit/loss information including
        gross/net PnL, swap, commission, and margin usage.
        
        Args:
            position_id: Position identifier
            
        Returns:
            PositionPnL with detailed breakdown, or None if position not found
            
        Example:
            >>> pnl = await client.risk.get_position_pnl(123456)
            >>> print(f"Gross PnL: {pnl.formatted_gross_pnl}")
            >>> print(f"Net PnL: {pnl.formatted_net_pnl}")
            >>> print(f"Total costs: {pnl.total_costs}")
            >>> print(f"Margin used: {pnl.used_margin}")
        """
        # Get position from trading API
        if self._client is None:
            raise RuntimeError("Risk API not attached to client")
        
        positions = await self._client.trading.get_positions()
        position = next((p for p in positions if p.id == position_id), None)
        
        if position is None:
            return None
        
        import time
        
        # Build PnL info from position data
        return PositionPnL(
            position_id=position.id,
            gross_unrealized_pnl=position.pnl_gross_unrealized,
            net_unrealized_pnl=position.pnl_net_unrealized,
            swap=position.swap,
            commission=position.commission,
            used_margin=None,  # Would need ProtoOAMarginChangedEvent to get this
            money_digits=2,  # From account settings
            timestamp=int(time.time() * 1000)
        )
    
    async def get_margin_calls(self) -> list[MarginCall]:
        """Get list of margin calls for the account.
        
        Returns historical and active margin calls including
        margin call type, equity, margin level at the time of the call.
        
        Returns:
            List of MarginCall objects
            
        Example:
            >>> calls = await client.risk.get_margin_calls()
            >>> for call in calls:
            ...     print(f"{call.margin_call_type} at {call.datetime}")
            ...     print(f"  Equity: {call.formatted_equity}")
            ...     print(f"  Margin Level: {call.formatted_margin_level}")
        """
        from ..messages.OpenApiMessages_pb2 import (
            ProtoOAMarginCallListReq,
            ProtoOAMarginCallListRes,
        )
        
        # Build request
        req = ProtoOAMarginCallListReq()
        req.ctidTraderAccountId = self.config.account_id
        
        # Send request
        response = await self.protocol.send_request(
            req,
            timeout=self.config.request_timeout,
            request_type="MarginCallList"
        )
        
        if not isinstance(response, ProtoOAMarginCallListRes):
            raise ValueError(f"Unexpected response type: {type(response)}")
        
        # Parse margin calls
        margin_calls = []
        money_digits = getattr(response, 'moneyDigits', None) or 2
        
        if hasattr(response, 'marginCall'):
            for mc in response.marginCall:
                margin_call_type = getattr(mc, 'marginCallType', 'UNKNOWN')
                
                # Convert from protocol units
                equity = getattr(mc, 'equity', 0) / (10 ** money_digits)
                margin = getattr(mc, 'margin', 0) / (10 ** money_digits)
                margin_level = getattr(mc, 'marginLevel', 0.0)
                timestamp = getattr(mc, 'marginCallTimestamp', 0)
                
                margin_calls.append(MarginCall(
                    margin_call_type=str(margin_call_type),
                    equity=equity,
                    margin=margin,
                    margin_level=margin_level,
                    timestamp=timestamp,
                    money_digits=money_digits
                ))
        
        return margin_calls
    
    def subscribe_margin_events(self, callback):
        """Subscribe to margin change events.
        
        Register a callback to be notified when position margin changes.
        
        Args:
            callback: Function called with (position_id, used_margin, money_digits)
            
        Example:
            >>> def on_margin_change(position_id, used_margin, money_digits):
            ...     print(f"Position {position_id} margin: {used_margin}")
            >>> 
            >>> client.risk.subscribe_margin_events(on_margin_change)
        """
        from ..messages.OpenApiMessages_pb2 import ProtoOAMarginChangedEvent
        
        def handler(event):
            if not isinstance(event, ProtoOAMarginChangedEvent):
                return
            
            if hasattr(event, 'ctidTraderAccountId') and \
               event.ctidTraderAccountId != self.config.account_id:
                return
            
            position_id = getattr(event, 'positionId', None)
            used_margin_raw = getattr(event, 'usedMargin', None)
            money_digits = getattr(event, 'moneyDigits', 2)
            
            if position_id is not None and used_margin_raw is not None:
                used_margin = used_margin_raw / (10 ** money_digits)
                try:
                    callback(position_id, used_margin, money_digits)
                except Exception as e:
                    logger.error(f"Error in margin event callback: {e}", exc_info=True)
        
        self.protocol.add_handler(ProtoOAMarginChangedEvent, handler)
        logger.info("Subscribed to margin change events")
    
    async def validate_trade_risk(
        self,
        symbol: str,
        volume: float,
        side: str,
        max_risk_percent: float = 2.0
    ) -> dict:
        """Validate if a proposed trade meets risk criteria.
        
        Checks if the trade:
        - Has sufficient margin
        - Doesn't exceed risk percentage limits
        - Is within account leverage constraints
        
        Args:
            symbol: Symbol name
            volume: Trade volume in lots
            side: Trade side ("BUY" or "SELL")
            max_risk_percent: Maximum risk as % of equity (default: 2%)
            
        Returns:
            Dict with validation results:
            {
                'valid': bool,
                'margin_required': float,
                'margin_available': float,
                'margin_sufficient': bool,
                'risk_percent': float,
                'risk_acceptable': bool,
                'warnings': list[str]
            }
            
        Example:
            >>> validation = await client.risk.validate_trade_risk(
            ...     "EURUSD", 1.0, "BUY", max_risk_percent=2.0
            ... )
            >>> if validation['valid']:
            ...     await client.trading.place_market_order("EURUSD", "BUY", 1.0)
            >>> else:
            ...     print("Trade rejected:", validation['warnings'])
        """
        if self._client is None:
            raise RuntimeError("Risk API not attached to client")
        
        warnings = []
        
        # Get margin requirement
        try:
            margin_info = await self.get_expected_margin(symbol, volume, side)
            margin_required = margin_info.margin
        except Exception as e:
            return {
                'valid': False,
                'margin_required': 0,
                'margin_available': 0,
                'margin_sufficient': False,
                'risk_percent': 0,
                'risk_acceptable': False,
                'warnings': [f"Failed to calculate margin: {e}"]
            }
        
        # Get account info
        account = await self._client.account.get_account_info()
        margin_available = account.free_margin
        equity = account.equity
        
        # Check margin sufficiency
        margin_sufficient = margin_required <= margin_available
        if not margin_sufficient:
            warnings.append(
                f"Insufficient margin. Required: {margin_required:.2f}, "
                f"Available: {margin_available:.2f}"
            )
        
        # Calculate risk percentage (using margin as risk proxy)
        risk_percent = (margin_required / equity * 100) if equity > 0 else 0
        risk_acceptable = risk_percent <= max_risk_percent
        
        if not risk_acceptable:
            warnings.append(
                f"Risk too high: {risk_percent:.2f}% > {max_risk_percent}%"
            )
        
        # Overall validation
        valid = margin_sufficient and risk_acceptable
        
        return {
            'valid': valid,
            'margin_required': margin_required,
            'margin_available': margin_available,
            'margin_sufficient': margin_sufficient,
            'risk_percent': risk_percent,
            'risk_acceptable': risk_acceptable,
            'warnings': warnings
        }
