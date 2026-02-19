"""
Trading History API.

Provides methods for:
- Deal/trade history retrieval
- Position-specific deal tracking
- Order details and history
- Performance reporting and reconciliation
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional
from datetime import datetime, timezone, timedelta

from ..models import Deal, Order
from dataclasses import dataclass

if TYPE_CHECKING:
    from ..protocol import ProtocolHandler
    from ..config import ClientConfig
    from ..api.symbols import SymbolCatalog

logger = logging.getLogger(__name__)


@dataclass
class DealOffset:
    """Deal offset information (for netting accounts).
    
    In netting accounts, deals can offset each other to close positions.
    This represents the relationship between opening and closing deals.
    
    Attributes:
        offset_id: Offset identifier
        open_deal_id: Opening deal ID
        close_deal_id: Closing deal ID
        volume: Volume offset (in lots)
        timestamp: Offset timestamp
    """
    offset_id: int
    open_deal_id: int
    close_deal_id: int
    volume: float
    timestamp: int


class HistoryAPI:
    """Trading history and reporting API.
    
    Provides methods for retrieving historical trade data, deal tracking,
    and order history for reporting and reconciliation purposes.
    
    Example:
        >>> # Get last 30 days of deals
        >>> deals = await client.history.get_deals(days=30)
        >>> for deal in deals:
        ...     print(f"{deal.symbol_name} {deal.side} {deal.volume} @ {deal.execution_price}")
        >>> 
        >>> # Get all deals for a specific position
        >>> position_deals = await client.history.get_deals_by_position(position_id)
    """
    
    def __init__(
        self,
        protocol: ProtocolHandler,
        config: ClientConfig,
        symbols: SymbolCatalog,
        client=None
    ):
        """Initialize History API.
        
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
    
    async def get_deals(
        self,
        from_timestamp: Optional[int] = None,
        to_timestamp: Optional[int] = None,
        days: Optional[int] = None,
        max_rows: int = 1000
    ) -> list[Deal]:
        """Get deal history (executed trades).
        
        Retrieves the list of executed deals (trade fills) for the account.
        Useful for performance analysis, reporting, and reconciliation.
        
        Args:
            from_timestamp: Start time in milliseconds (optional)
            to_timestamp: End time in milliseconds (optional)
            days: Get deals from last N days (alternative to timestamps)
            max_rows: Maximum number of deals to return (default: 1000)
            
        Returns:
            List of Deal objects
            
        Example:
            >>> # Get deals from last 7 days
            >>> deals = await client.history.get_deals(days=7)
            >>> 
            >>> # Get deals for specific time range
            >>> from_ts = int((datetime.now() - timedelta(days=30)).timestamp() * 1000)
            >>> to_ts = int(datetime.now().timestamp() * 1000)
            >>> deals = await client.history.get_deals(from_timestamp=from_ts, to_timestamp=to_ts)
            >>> 
            >>> # Calculate total PnL
            >>> total_pnl = sum(deal.pnl for deal in deals)
            >>> print(f"Total PnL: {total_pnl:.2f}")
        """
        from ..messages.OpenApiMessages_pb2 import (
            ProtoOADealListReq,
            ProtoOADealListRes,
        )
        
        # Calculate timestamps if days specified
        if days is not None:
            to_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
            from_timestamp = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000)
        
        # Default to last 30 days if no time range specified
        if from_timestamp is None:
            from_timestamp = int((datetime.now(timezone.utc) - timedelta(days=30)).timestamp() * 1000)
        if to_timestamp is None:
            to_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
        
        # Build request
        req = ProtoOADealListReq()
        req.ctidTraderAccountId = self.config.account_id
        req.fromTimestamp = from_timestamp
        req.toTimestamp = to_timestamp
        req.maxRows = max_rows
        
        # Send request
        response = await self.protocol.send_request(
            req,
            timeout=self.config.request_timeout,
            request_type="DealList"
        )
        
        if not isinstance(response, ProtoOADealListRes):
            raise ValueError(f"Unexpected response type: {type(response)}")
        
        # Parse deals
        deals = []
        
        if hasattr(response, 'deal'):
            for deal_proto in response.deal:
                deal = await self._parse_deal(deal_proto)
                if deal:
                    deals.append(deal)
        
        logger.info(f"Retrieved {len(deals)} deals")
        return deals
    
    async def get_deals_by_position(self, position_id: int) -> list[Deal]:
        """Get all deals for a specific position.
        
        Retrieves all trade executions (fills) that are associated with
        a particular position. Useful for tracking position lifecycle.
        
        Args:
            position_id: Position identifier
            
        Returns:
            List of Deal objects for the position
            
        Example:
            >>> # Get all deals that opened/modified/closed a position
            >>> deals = await client.history.get_deals_by_position(123456)
            >>> for deal in deals:
            ...     print(f"{deal.datetime}: {deal.side} {deal.volume} @ {deal.execution_price}")
            >>> 
            >>> # Calculate average entry price
            >>> entry_deals = [d for d in deals if d.volume > 0]
            >>> total_volume = sum(d.volume for d in entry_deals)
            >>> avg_entry = sum(d.execution_price * d.volume for d in entry_deals) / total_volume
        """
        from ..messages.OpenApiMessages_pb2 import (
            ProtoOADealListByPositionIdReq,
            ProtoOADealListByPositionIdRes,
        )

        # ProtoOADealListByPositionIdReq requires fromTimestamp and toTimestamp
        # Use a wide window to get all deals for the position
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        far_past_ms = 0  # epoch = get all history

        # Build request
        req = ProtoOADealListByPositionIdReq()
        req.ctidTraderAccountId = self.config.account_id
        req.positionId = position_id
        req.fromTimestamp = far_past_ms
        req.toTimestamp = now_ms
        
        # Send request
        response = await self.protocol.send_request(
            req,
            timeout=self.config.request_timeout,
            request_type="DealListByPositionId"
        )
        
        if not isinstance(response, ProtoOADealListByPositionIdRes):
            raise ValueError(f"Unexpected response type: {type(response)}")
        
        # Parse deals
        deals = []
        
        if hasattr(response, 'deal'):
            for deal_proto in response.deal:
                deal = await self._parse_deal(deal_proto)
                if deal:
                    deals.append(deal)
        
        logger.info(f"Retrieved {len(deals)} deals for position {position_id}")
        return deals
    
    async def get_order_details(self, order_id: int) -> Optional[Order]:
        """Get detailed information about a specific order.
        
        Retrieves comprehensive details about an order including all
        modifications, status changes, and execution details.
        
        Args:
            order_id: Order identifier
            
        Returns:
            Order object with full details, or None if not found
            
        Example:
            >>> order = await client.history.get_order_details(789012)
            >>> if order:
            ...     print(f"Order {order.id}: {order.status}")
            ...     print(f"Created: {order.create_datetime}")
            ...     print(f"Volume: {order.volume} lots")
        """
        from ..messages.OpenApiMessages_pb2 import (
            ProtoOAOrderDetailsReq,
            ProtoOAOrderDetailsRes,
        )
        
        # Build request
        req = ProtoOAOrderDetailsReq()
        req.ctidTraderAccountId = self.config.account_id
        req.orderId = order_id
        
        # Send request
        try:
            response = await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="OrderDetails"
            )
            
            if not isinstance(response, ProtoOAOrderDetailsRes):
                raise ValueError(f"Unexpected response type: {type(response)}")
            
            # Parse order
            if hasattr(response, 'order'):
                order = await self._parse_order(response.order)
                return order
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to get order details for {order_id}: {e}")
            return None
    
    async def _parse_deal(self, deal_proto) -> Optional[Deal]:
        """Parse a deal from protobuf message.
        
        Args:
            deal_proto: ProtoOADeal message
            
        Returns:
            Deal object or None
        """
        try:
            deal_id = getattr(deal_proto, 'dealId', None)
            if deal_id is None:
                return None
            
            position_id = getattr(deal_proto, 'positionId', None)
            order_id = getattr(deal_proto, 'orderId', None)
            symbol_id = getattr(deal_proto, 'symbolId', None)
            
            # Get symbol name
            symbol_name = None
            if symbol_id:
                symbol_info = await self.symbols.get_symbol_by_id(symbol_id)
                if symbol_info:
                    symbol_name = symbol_info.name
            
            # Parse volume
            volume_proto = getattr(deal_proto, 'filledVolume', None) or getattr(deal_proto, 'volume', None)
            volume = None
            if volume_proto and symbol_id:
                symbol_info = await self.symbols.get_symbol_by_id(symbol_id)
                if symbol_info:
                    volume = symbol_info.protocol_volume_to_lots(volume_proto)
            
            # Parse side using enum names (avoid hardcoded ints)
            from ..messages.OpenApiModelMessages_pb2 import ProtoOATradeSide
            trade_side_val = getattr(deal_proto, 'tradeSide', None)
            side = None
            if trade_side_val is not None:
                try:
                    side = ProtoOATradeSide.Name(int(trade_side_val))
                except Exception:
                    side = str(trade_side_val)
            
            # executionPrice in ProtoOADeal is a proto double — already a real price,
            # no scaling needed (unlike price fields in ProtoOAPosition/ProtoOAOrder
            # which use int scaled by 10^digits).
            execution_price = getattr(deal_proto, 'executionPrice', None)
            if execution_price:
                execution_price = float(execution_price)
            
            # Parse money values
            money_digits = getattr(deal_proto, 'moneyDigits', None) or 2
            commission_proto = getattr(deal_proto, 'commission', None)
            commission = commission_proto / (10 ** money_digits) if commission_proto else 0.0
            
            # Parse close position detail for PnL if available
            pnl = 0.0
            swap = 0.0
            if hasattr(deal_proto, 'closePositionDetail') and deal_proto.HasField('closePositionDetail'):
                close_detail = deal_proto.closePositionDetail
                if hasattr(close_detail, 'grossProfit'):
                    pnl = close_detail.grossProfit / (10 ** money_digits)
                if hasattr(close_detail, 'swap'):
                    swap = close_detail.swap / (10 ** money_digits)
            
            # Parse timestamp
            timestamp = getattr(deal_proto, 'executionTimestamp', None) or \
                       getattr(deal_proto, 'createTimestamp', None)
            
            return Deal(
                deal_id=deal_id,
                position_id=position_id,
                order_id=order_id,
                symbol_id=symbol_id,
                symbol_name=symbol_name,
                side=side,
                volume=volume,
                execution_price=execution_price,
                commission=commission,
                swap=swap,
                pnl=pnl,
                timestamp=timestamp
            )
        
        except Exception as e:
            logger.error(f"Error parsing deal: {e}", exc_info=True)
            return None
    
    async def _parse_order(self, order_proto) -> Optional[Order]:
        """Parse an order from protobuf message.

        ProtoOAOrder fields:
            orderId, tradeData (ProtoOATradeData), orderType, orderStatus,
            expirationTimestamp, executionPrice, executedVolume,
            utcLastUpdateTimestamp, limitPrice, stopPrice, stopLoss,
            takeProfit, clientOrderId, timeInForce, positionId,
            trailingStopLoss, stopTriggerMethod

        ProtoOATradeData fields:
            symbolId, volume, tradeSide, openTimestamp, label,
            guaranteedStopLoss, comment
        """
        try:
            order_id = getattr(order_proto, 'orderId', None)
            if order_id is None:
                return None

            # tradeData is a nested ProtoOATradeData message — access as attribute, not dict
            trade_data = getattr(order_proto, 'tradeData', None)
            symbol_id = int(getattr(trade_data, 'symbolId', 0)) if trade_data else None

            # Get symbol name and info
            symbol_name = None
            symbol_info = None
            if symbol_id:
                symbol_info = await self.symbols.get_symbol_by_id(symbol_id)
                if symbol_info:
                    symbol_name = symbol_info.name

            # Parse volume from tradeData
            volume_proto = int(getattr(trade_data, 'volume', 0)) if trade_data else 0
            volume = None
            if volume_proto and symbol_info:
                volume = symbol_info.protocol_volume_to_lots(volume_proto)
            elif volume_proto:
                volume = float(volume_proto) / 100.0

            # Parse side from tradeData using enum names
            from ..messages.OpenApiModelMessages_pb2 import ProtoOATradeSide
            trade_side_val = int(getattr(trade_data, 'tradeSide', 0)) if trade_data else 0
            side = ProtoOATradeSide.Name(trade_side_val) if trade_side_val else "UNKNOWN"

            # Parse order type using enum names
            from ..messages.OpenApiModelMessages_pb2 import ProtoOAOrderType
            order_type_val = getattr(order_proto, 'orderType', None)
            order_type = "UNKNOWN"
            if order_type_val is not None:
                try:
                    order_type = ProtoOAOrderType.Name(int(order_type_val))
                except Exception:
                    order_type = str(order_type_val)

            # Parse status using enum names
            from ..messages.OpenApiModelMessages_pb2 import ProtoOAOrderStatus
            status_val = getattr(order_proto, 'orderStatus', None)
            status = "UNKNOWN"
            if status_val is not None:
                try:
                    status = ProtoOAOrderStatus.Name(int(status_val))
                except Exception:
                    status = str(status_val)

            # Timestamps: tradeData.openTimestamp = creation time
            create_timestamp = int(getattr(trade_data, 'openTimestamp', 0) or 0) if trade_data else None
            last_update_timestamp = int(getattr(order_proto, 'utcLastUpdateTimestamp', 0) or 0) or None
            expiration_timestamp = int(getattr(order_proto, 'expirationTimestamp', 0) or 0) or None

            # Prices
            limit_price_raw = getattr(order_proto, 'limitPrice', None)
            stop_price_raw = getattr(order_proto, 'stopPrice', None)
            stop_loss_raw = getattr(order_proto, 'stopLoss', None)
            take_profit_raw = getattr(order_proto, 'takeProfit', None)
            price_scale = 10 ** (symbol_info.digits if symbol_info else 5)

            def to_price(raw):
                if not raw:
                    return None
                return float(raw) / price_scale

            return Order(
                id=order_id,
                symbol_id=symbol_id or 0,
                symbol_name=symbol_name,
                volume=volume or 0.0,
                side=side,
                order_type=order_type,
                status=status,
                limit_price=to_price(limit_price_raw),
                stop_price=to_price(stop_price_raw),
                stop_loss=to_price(stop_loss_raw),
                take_profit=to_price(take_profit_raw),
                client_order_id=getattr(order_proto, 'clientOrderId', None) or None,
                label=getattr(trade_data, 'label', None) or None,
                comment=getattr(trade_data, 'comment', None) or None,
                create_timestamp=create_timestamp or None,
                last_update_timestamp=last_update_timestamp,
                expiration_timestamp=expiration_timestamp,
            )

        except Exception as e:
            logger.error(f"Error parsing order: {e}", exc_info=True)
            return None
    
    async def get_deal_offsets(self, deal_id: int) -> list[DealOffset]:
        """Get deal offsets for a specific deal (netting accounts).

        Uses ``ProtoOADealOffsetListReq`` which takes a single ``dealId`` and
        returns two lists: deals that *this* deal offsets (``offsetBy``) and
        deals that offset *this* deal (``offsetting``).

        ``ProtoOADealOffset`` fields: ``dealId``, ``volume``,
        ``executionTimestamp``, ``executionPrice``.

        Args:
            deal_id: The deal ID to look up offsets for.

        Returns:
            List of DealOffset objects from both offsetBy and offsetting lists.

        Example:
            >>> offsets = await client.history.get_deal_offsets(deal_id=123456)
            >>> for offset in offsets:
            ...     print(f"Offset deal {offset.open_deal_id} vol={offset.volume}")
        """
        from ..messages.OpenApiMessages_pb2 import (
            ProtoOADealOffsetListReq,
            ProtoOADealOffsetListRes,
        )

        req = ProtoOADealOffsetListReq()
        req.ctidTraderAccountId = self.config.account_id
        req.dealId = int(deal_id)

        response = await self.protocol.send_request(
            req,
            timeout=self.config.request_timeout,
            request_type="DealOffsetList",
        )

        if not isinstance(response, ProtoOADealOffsetListRes):
            raise ValueError(f"Unexpected response type: {type(response)}")

        offsets = []

        # ProtoOADealOffset: dealId, volume, executionTimestamp, executionPrice
        for offset_proto in list(getattr(response, 'offsetBy', []) or []):
            offsets.append(DealOffset(
                offset_id=int(deal_id),
                open_deal_id=int(deal_id),
                close_deal_id=int(getattr(offset_proto, 'dealId', 0)),
                volume=float(getattr(offset_proto, 'volume', 0)) / 100.0,
                timestamp=int(getattr(offset_proto, 'executionTimestamp', 0)),
            ))

        for offset_proto in list(getattr(response, 'offsetting', []) or []):
            offsets.append(DealOffset(
                offset_id=int(deal_id),
                open_deal_id=int(getattr(offset_proto, 'dealId', 0)),
                close_deal_id=int(deal_id),
                volume=float(getattr(offset_proto, 'volume', 0)) / 100.0,
                timestamp=int(getattr(offset_proto, 'executionTimestamp', 0)),
            ))

        logger.info(f"Retrieved {len(offsets)} deal offsets for deal {deal_id}")
        return offsets
    
    async def get_orders_by_position(self, position_id: int) -> list[Order]:
        """Get all orders linked to a specific position.

        Uses ``ProtoOAOrderListByPositionIdReq`` to retrieve every order
        (opening, modification, close) that was ever associated with the
        given position. Useful for full position lifecycle analysis.

        Args:
            position_id: Position identifier

        Returns:
            List of Order objects for the position

        Example:
            >>> orders = await client.history.get_orders_by_position(123456)
            >>> for order in orders:
            ...     print(f"Order {order.id}: {order.order_type} {order.status}")
        """
        from ..messages.OpenApiMessages_pb2 import (
            ProtoOAOrderListByPositionIdReq,
            ProtoOAOrderListByPositionIdRes,
        )

        # ProtoOAOrderListByPositionIdReq requires fromTimestamp and toTimestamp
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

        req = ProtoOAOrderListByPositionIdReq()
        req.ctidTraderAccountId = self.config.account_id
        req.positionId = int(position_id)
        req.fromTimestamp = 0          # epoch = include all history
        req.toTimestamp = now_ms

        response = await self.protocol.send_request(
            req,
            timeout=self.config.request_timeout,
            request_type="OrderListByPositionId",
        )

        if not isinstance(response, ProtoOAOrderListByPositionIdRes):
            raise ValueError(f"Unexpected response type: {type(response)}")

        orders = []
        for order_proto in list(getattr(response, "order", []) or []):
            order = await self._parse_order(order_proto)
            if order:
                orders.append(order)

        logger.info(f"Retrieved {len(orders)} orders for position {position_id}")
        return orders

    async def get_performance_summary(
        self,
        days: int = 30
    ) -> dict:
        """Get performance summary for a time period.
        
        Calculates various performance metrics from deal history.
        
        Args:
            days: Number of days to analyze (default: 30)
            
        Returns:
            Dict with performance metrics:
            {
                'total_deals': int,
                'winning_deals': int,
                'losing_deals': int,
                'win_rate': float,
                'total_pnl': float,
                'total_commission': float,
                'total_swap': float,
                'net_pnl': float,
                'avg_win': float,
                'avg_loss': float,
                'largest_win': float,
                'largest_loss': float,
                'profit_factor': float
            }
            
        Example:
            >>> summary = await client.history.get_performance_summary(days=30)
            >>> print(f"Win Rate: {summary['win_rate']:.1f}%")
            >>> print(f"Net PnL: {summary['net_pnl']:.2f}")
            >>> print(f"Profit Factor: {summary['profit_factor']:.2f}")
        """
        deals = await self.get_deals(days=days)
        
        if not deals:
            return {
                'total_deals': 0,
                'winning_deals': 0,
                'losing_deals': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'total_commission': 0.0,
                'total_swap': 0.0,
                'net_pnl': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0,
                'profit_factor': 0.0
            }
        
        # Calculate metrics
        total_pnl = sum(d.pnl for d in deals)
        total_commission = sum(d.commission for d in deals)
        total_swap = sum(d.swap for d in deals)
        
        winning_deals = [d for d in deals if d.pnl > 0]
        losing_deals = [d for d in deals if d.pnl < 0]
        
        total_wins = sum(d.pnl for d in winning_deals)
        total_losses = abs(sum(d.pnl for d in losing_deals))
        
        return {
            'total_deals': len(deals),
            'winning_deals': len(winning_deals),
            'losing_deals': len(losing_deals),
            'win_rate': (len(winning_deals) / len(deals) * 100) if deals else 0.0,
            'total_pnl': total_pnl,
            'total_commission': total_commission,
            'total_swap': total_swap,
            'net_pnl': total_pnl + total_commission + total_swap,
            'avg_win': total_wins / len(winning_deals) if winning_deals else 0.0,
            'avg_loss': total_losses / len(losing_deals) if losing_deals else 0.0,
            'largest_win': max((d.pnl for d in winning_deals), default=0.0),
            'largest_loss': min((d.pnl for d in losing_deals), default=0.0),
            'profit_factor': (total_wins / total_losses) if total_losses > 0 else 0.0
        }
