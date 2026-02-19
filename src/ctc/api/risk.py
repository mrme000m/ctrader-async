"""
Risk Management and Margin API.

Provides methods for:
- Pre-trade margin calculations
- Position PnL details
- Margin call monitoring
- Dynamic leverage queries
- Risk management utilities
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from ..models import MarginInfo, PositionPnL, PositionPnLRealtime, MarginCall

if TYPE_CHECKING:
    from ..protocol import ProtocolHandler
    from ..config import ClientConfig
    from ..api.symbols import SymbolCatalog

logger = logging.getLogger(__name__)


@dataclass
class LeverageTier:
    """Dynamic leverage tier information.
    
    Represents a tier in a broker's dynamic leverage schedule.
    Higher volumes typically result in lower leverage (higher margin requirements).
    
    Attributes:
        tier_id: Tier identifier
        volume_from: Starting volume for this tier (in lots or units)
        volume_to: Ending volume for this tier (None = unlimited)
        leverage: Leverage for this tier (e.g., 100.0 for 1:100)
        margin_percent: Required margin percentage (e.g., 1.0 for 1%)
    """
    tier_id: int
    volume_from: float
    volume_to: Optional[float]
    leverage: float
    
    @property
    def margin_percent(self) -> float:
        """Calculate margin percentage from leverage."""
        return 100.0 / self.leverage if self.leverage > 0 else 0.0
    
    def __repr__(self) -> str:
        vol_to = f"{self.volume_to:.2f}" if self.volume_to else "∞"
        return (
            f"<LeverageTier {self.tier_id}: "
            f"{self.volume_from:.2f}-{vol_to} @ 1:{self.leverage:.0f}>"
        )


@dataclass
class DynamicLeverage:
    """Dynamic leverage information for a symbol.
    
    Contains the tiered leverage schedule that applies to a symbol.
    
    Attributes:
        symbol_id: Symbol identifier
        symbol_name: Symbol name
        tiers: List of leverage tiers (ordered by volume)
        total_volume: Total open volume for margin calculation
    """
    symbol_id: int
    symbol_name: Optional[str]
    tiers: list[LeverageTier]
    total_volume: float = 0.0
    
    def get_leverage_for_volume(self, volume: float) -> float:
        """Get the applicable leverage for a given volume.
        
        Args:
            volume: Trade volume in lots
            
        Returns:
            Leverage value (e.g., 100.0 for 1:100)
        """
        for tier in self.tiers:
            if tier.volume_to is None or volume <= tier.volume_to:
                return tier.leverage
        # If volume exceeds all tiers, use the last tier's leverage
        return self.tiers[-1].leverage if self.tiers else 100.0
    
    def calculate_margin(self, volume: float, notional_value: float) -> float:
        """Calculate margin required for a given volume.
        
        Args:
            volume: Trade volume in lots
            notional_value: Notional value of the position in base currency
            
        Returns:
            Required margin in account currency
        """
        leverage = self.get_leverage_for_volume(volume)
        return notional_value / leverage if leverage > 0 else 0.0


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
        self._margin_event_handlers: list[Callable] = []
        self._margin_call_handlers: list[Callable] = []
    
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
        divisor = 10 ** money_digits

        # cTrader returns repeated ProtoOAExpectedMargin entries in response.margin,
        # one per requested volume. This API requests one volume, but we still
        # handle matching by volume defensively.
        margin_entries = list(getattr(response, 'margin', []))
        if not margin_entries:
            raise ValueError("No margin value in response")

        selected_entry = next(
            (m for m in margin_entries if getattr(m, 'volume', None) == volume_proto),
            margin_entries[0],
        )

        buy_margin_raw = getattr(selected_entry, 'buyMargin', None)
        sell_margin_raw = getattr(selected_entry, 'sellMargin', None)

        buy_margin = (
            float(buy_margin_raw) / divisor if buy_margin_raw is not None else None
        )
        sell_margin = (
            float(sell_margin_raw) / divisor if sell_margin_raw is not None else None
        )

        side = (order_type or '').upper()
        if side == 'BUY' and buy_margin is not None:
            margin = buy_margin
        elif side == 'SELL' and sell_margin is not None:
            margin = sell_margin
        elif buy_margin is not None and sell_margin is not None:
            margin = max(buy_margin, sell_margin)
        elif buy_margin is not None:
            margin = buy_margin
        elif sell_margin is not None:
            margin = sell_margin
        else:
            raise ValueError("No buy/sell margin value in response")
        
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
    
    async def get_position_pnl_realtime(self, position_id: int) -> Optional[PositionPnLRealtime]:
        """Get real-time unrealized PnL for a position from server.
        
        This fetches server-calculated unrealized PnL which is more accurate
        than client-side calculations as it uses the broker's exact pricing.
        
        Args:
            position_id: Position identifier
            
        Returns:
            PositionPnLRealtime with server-calculated PnL, or None if position not found
            
        Example:
            >>> pnl = await client.risk.get_position_pnl_realtime(123456)
            >>> print(f"Server Gross PnL: {pnl.formatted_gross_pnl}")
            >>> print(f"Server Net PnL: {pnl.formatted_net_pnl}")
        """
        from ..messages.OpenApiMessages_pb2 import (
            ProtoOAGetPositionUnrealizedPnLReq,
            ProtoOAGetPositionUnrealizedPnLRes,
        )
        
        # Build request
        req = ProtoOAGetPositionUnrealizedPnLReq()
        req.ctidTraderAccountId = self.config.account_id
        req.positionId = position_id
        
        # Send request
        response = await self.protocol.send_request(
            req,
            timeout=self.config.request_timeout,
            request_type="PositionUnrealizedPnL"
        )
        
        if not isinstance(response, ProtoOAGetPositionUnrealizedPnLRes):
            raise ValueError(f"Unexpected response type: {type(response)}")
        
        # Check if position exists
        if hasattr(response, 'positionId') and response.positionId != position_id:
            return None
        
        # Parse response
        money_digits = getattr(response, 'moneyDigits', 2)
        divisor = 10 ** money_digits
        
        gross_pnl = getattr(response, 'grossUnrealizedPnL', 0) / divisor
        net_pnl = getattr(response, 'netUnrealizedPnL', 0) / divisor
        swap = getattr(response, 'swap', 0) / divisor
        commission = getattr(response, 'commission', 0) / divisor
        timestamp = getattr(response, 'timestamp', None)
        
        return PositionPnLRealtime(
            position_id=position_id,
            gross_unrealized_pnl=gross_pnl,
            net_unrealized_pnl=net_pnl,
            swap=swap,
            commission=commission,
            timestamp=timestamp,
            money_digits=money_digits
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
    
    async def get_dynamic_leverage(self, symbol: str) -> Optional[DynamicLeverage]:
        """Get dynamic leverage tiers for a symbol.
        
        Dynamic leverage allows brokers to offer different leverage levels
        based on position size. Higher volumes typically have lower leverage.
        
        Args:
            symbol: Symbol name (e.g., "EURUSD")
            
        Returns:
            DynamicLeverage with tier information, or None if not available
            
        Example:
            >>> leverage_info = await client.risk.get_dynamic_leverage("EURUSD")
            >>> for tier in leverage_info.tiers:
            ...     print(f"Volume {tier.volume_from}-{tier.volume_to}: 1:{tier.leverage}")
            >>> 
            >>> # Get leverage for specific volume
            >>> lev = leverage_info.get_leverage_for_volume(5.0)
            >>> print(f"Leverage for 5 lots: 1:{lev}")
        """
        from ..messages.OpenApiMessages_pb2 import (
            ProtoOAGetDynamicLeverageByIDReq,
            ProtoOAGetDynamicLeverageByIDRes,
        )
        
        # Get symbol info
        symbol_info = await self.symbols.get_symbol(symbol)
        if not symbol_info:
            raise ValueError(f"Symbol not found: {symbol}")
        
        # Build request
        req = ProtoOAGetDynamicLeverageByIDReq()
        req.ctidTraderAccountId = self.config.account_id
        req.symbolId = symbol_info.id
        
        # Send request
        response = await self.protocol.send_request(
            req,
            timeout=self.config.request_timeout,
            request_type="DynamicLeverage"
        )
        
        if not isinstance(response, ProtoOAGetDynamicLeverageByIDRes):
            raise ValueError(f"Unexpected response type: {type(response)}")
        
        # Check if dynamic leverage data exists
        if not hasattr(response, 'dynamicLeverage') or not response.dynamicLeverage:
            return None
        
        # Parse tiers
        tiers = []
        for i, tier_data in enumerate(response.dynamicLeverage):
            volume_from = getattr(tier_data, 'volumeFrom', 0) / 100.0  # Convert from cents
            volume_to_raw = getattr(tier_data, 'volumeTo', None)
            volume_to = volume_to_raw / 100.0 if volume_to_raw else None
            leverage = getattr(tier_data, 'leverage', 100) / 100.0  # Convert from cents
            
            tiers.append(LeverageTier(
                tier_id=i + 1,
                volume_from=volume_from,
                volume_to=volume_to,
                leverage=leverage
            ))
        
        # Get total volume if available
        total_volume = 0.0
        if hasattr(response, 'totalVolume'):
            total_volume = response.totalVolume / 100.0
        
        return DynamicLeverage(
            symbol_id=symbol_info.id,
            symbol_name=symbol,
            tiers=tiers,
            total_volume=total_volume
        )
    
    async def update_margin_call(
        self,
        margin_call_type: str,
        margin_level_threshold: float,
    ) -> None:
        """Update a margin call threshold for the account.

        Uses ``ProtoOAMarginCallUpdateReq`` to set the margin level at which
        a margin call warning or stop-out is triggered. This allows customising
        the broker's margin call behaviour programmatically.

        Args:
            margin_call_type: Type string as defined by the broker, e.g.
                ``"MARGIN_CALL"``, ``"STOP_OUT"``, ``"MARGIN_CALL_2"``
            margin_level_threshold: Margin level (%) at which the event fires,
                e.g. ``100.0`` for 100%

        Raises:
            ValueError: If the response is unexpected
            TradingError: If the server rejects the update

        Example:
            >>> # Set margin call warning at 120%
            >>> await client.risk.update_margin_call("MARGIN_CALL", 120.0)
            >>> # Set stop-out at 50%
            >>> await client.risk.update_margin_call("STOP_OUT", 50.0)
        """
        from ..messages.OpenApiMessages_pb2 import (
            ProtoOAMarginCallUpdateReq,
            ProtoOAMarginCallUpdateRes,
        )
        from ..messages.OpenApiModelMessages_pb2 import ProtoOAMarginCall

        mc = ProtoOAMarginCall()
        mc.marginCallType = margin_call_type
        mc.marginLevelThreshold = float(margin_level_threshold)

        req = ProtoOAMarginCallUpdateReq()
        req.ctidTraderAccountId = self.config.account_id
        req.marginCall.CopyFrom(mc)

        response = await self.protocol.send_request(
            req,
            timeout=self.config.request_timeout,
            request_type="MarginCallUpdate",
        )

        if not isinstance(response, ProtoOAMarginCallUpdateRes):
            raise ValueError(f"Unexpected response type: {type(response)}")

        logger.info(
            f"Margin call updated: type={margin_call_type}, "
            f"threshold={margin_level_threshold}%"
        )

    def subscribe_margin_events(
        self,
        callback: Callable[[int, float, int], None],
    ) -> Callable[[], None]:
        """Subscribe to margin change events.

        Registers *callback* on the client event bus so it is called whenever
        a ``ProtoOAMarginChangedEvent`` arrives from the server.

        Args:
            callback: Callable invoked as ``callback(position_id, used_margin, money_digits)``.

        Returns:
            An *unsubscribe* callable — call it with no arguments to stop
            receiving events::

                unsub = client.risk.subscribe_margin_events(my_handler)
                # later …
                unsub()

        Example:
            >>> def on_margin_change(position_id, used_margin, money_digits):
            ...     print(f"Position {position_id} margin: {used_margin:.2f}")
            >>>
            >>> unsub = client.risk.subscribe_margin_events(on_margin_change)
        """
        if self._client is None:
            raise RuntimeError("Risk API not attached to client — cannot subscribe to events")

        async def _handler(data: dict) -> None:
            position_id = data.get("position_id")
            used_margin = data.get("used_margin", 0.0)
            money_digits = data.get("money_digits", 2)
            if position_id is not None:
                try:
                    callback(position_id, used_margin, money_digits)
                except Exception as e:
                    logger.error(f"Error in margin event callback: {e}", exc_info=True)

        self._client.events.on("risk.margin_changed", _handler)
        self._margin_event_handlers.append(_handler)

        def _unsubscribe() -> None:
            self._client.events.off("risk.margin_changed", _handler)
            try:
                self._margin_event_handlers.remove(_handler)
            except ValueError:
                pass

        logger.info("Subscribed to margin change events")
        return _unsubscribe

    def subscribe_margin_call_events(
        self,
        callback: Callable[[str, float, float, float], None],
    ) -> Callable[[], None]:
        """Subscribe to margin call and stop-out events.

        Registers *callback* on the client event bus for both
        ``ProtoOAMarginCallUpdateEvent`` (threshold crossed) and
        ``ProtoOAMarginCallTriggerEvent`` (stop-out fired).

        Args:
            callback: Callable invoked as
                ``callback(event_type, equity, margin, margin_level)`` where
                *event_type* is ``"MARGIN_CALL_UPDATE"`` or ``"MARGIN_CALL_TRIGGER"``.

        Returns:
            An *unsubscribe* callable — call it with no arguments to stop
            receiving events::

                unsub = client.risk.subscribe_margin_call_events(my_handler)
                # later …
                unsub()

        Example:
            >>> def on_margin_call(event_type, equity, margin, margin_level):
            ...     print(f"{event_type}: Margin Level = {margin_level:.2f}%")
            ...     if event_type == "MARGIN_CALL_TRIGGER":
            ...         print("CRITICAL: Positions may be liquidated!")
            >>>
            >>> unsub = client.risk.subscribe_margin_call_events(on_margin_call)
        """
        if self._client is None:
            raise RuntimeError("Risk API not attached to client — cannot subscribe to events")

        async def _update_handler(data: dict) -> None:
            try:
                callback(
                    data.get("event_type", "MARGIN_CALL_UPDATE"),
                    data.get("equity", 0.0),
                    data.get("margin", 0.0),
                    data.get("margin_level", 0.0),
                )
            except Exception as e:
                logger.error(f"Error in margin call update callback: {e}", exc_info=True)

        async def _trigger_handler(data: dict) -> None:
            try:
                callback(
                    data.get("event_type", "MARGIN_CALL_TRIGGER"),
                    data.get("equity", 0.0),
                    data.get("margin", 0.0),
                    data.get("margin_level", 0.0),
                )
            except Exception as e:
                logger.error(f"Error in margin call trigger callback: {e}", exc_info=True)

        self._client.events.on("risk.margin_call_update", _update_handler)
        self._client.events.on("risk.margin_call_trigger", _trigger_handler)
        self._margin_call_handlers.append((_update_handler, _trigger_handler))

        def _unsubscribe() -> None:
            self._client.events.off("risk.margin_call_update", _update_handler)
            self._client.events.off("risk.margin_call_trigger", _trigger_handler)
            try:
                self._margin_call_handlers.remove((_update_handler, _trigger_handler))
            except ValueError:
                pass

        logger.info("Subscribed to margin call events")
        return _unsubscribe
    
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
        account = await self._client.account.get_full_account_info()
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
