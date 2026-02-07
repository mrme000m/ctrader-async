"""
High-level trading API for orders and positions.
"""

from __future__ import annotations

import asyncio
import uuid
import logging
from typing import Optional, TYPE_CHECKING

from ..models import Position, Order, Deal
from ..enums import TradeSide, OrderType, TimeInForce, OrderTriggerMethod
from ..utils.errors import TradingError, MarketClosedError, OrderError
from ..utils.rate_limiter import TokenBucketRateLimiter

if TYPE_CHECKING:
    from ..protocol import ProtocolHandler
    from ..config import ClientConfig
    from .symbols import SymbolCatalog

logger = logging.getLogger(__name__)


def _summarize_execution_event(ev: object) -> dict:
    """Best-effort summary of ProtoOAExecutionEvent.

    We avoid dumping the whole protobuf to keep logs readable.
    """
    def _has(name: str) -> bool:
        try:
            return hasattr(ev, name) and getattr(ev, name) is not None
        except Exception:
            return False

    def _get(name: str):
        try:
            return getattr(ev, name)
        except Exception:
            return None

    out: dict = {
        "type": type(ev).__name__,
        "has_position": _has("position"),
        "has_order": _has("order"),
        "has_deal": _has("deal"),
        "has_reject": _has("reject"),
    }

    # Common fields (may or may not exist depending on pb2)
    for k in [
        "executionType",
        "orderId",
        "positionId",
        "dealId",
        "errorCode",
        "description",
        "reasonCode",
    ]:
        v = _get(k)
        if v not in (None, 0, ""):
            out[k] = str(v)

    # Nested rejection/error details if present
    rej = _get("reject")
    if rej is not None:
        try:
            out["reject"] = {
                "errorCode": str(getattr(rej, "errorCode", "") or ""),
                "description": str(getattr(rej, "description", "") or ""),
                "reasonCode": str(getattr(rej, "reasonCode", "") or ""),
            }
        except Exception:
            out["reject"] = "<unreadable>"

    # Nested order/position ids if present
    try:
        pos = _get("position")
        if pos is not None:
            out["position_fields"] = {
                "positionId": int(getattr(pos, "positionId", 0) or 0) or None,
                "price": float(getattr(pos, "price", 0.0) or 0.0) or None,
            }
    except Exception:
        pass

    try:
        order = _get("order")
        if order is not None:
            out["order_fields"] = {
                "orderId": int(getattr(order, "orderId", 0) or 0) or None,
                "clientOrderId": str(getattr(order, "clientOrderId", "") or "") or None,
            }
    except Exception:
        pass

    return out


class TradingAPI:
    """High-level API for trading operations.
    
    Provides clean, intuitive methods for:
    - Placing market, limit, stop, and stop-limit orders
    - Managing positions (modify SL/TP, close)
    - Managing orders (modify, cancel)
    - Querying positions and orders
    
    Example:
        >>> trading = TradingAPI(protocol, config, symbols)
        >>> position = await trading.place_market_order(
        ...     symbol="EURUSD",
        ...     side=TradeSide.BUY,
        ...     volume=0.01,
        ...     stop_loss=1.0900
        ... )
    """
    
    def __init__(
        self,
        protocol: ProtocolHandler,
        config: ClientConfig,
        symbols: SymbolCatalog
    ):
        """Initialize trading API.
        
        Args:
            protocol: Protocol handler for sending requests
            config: Client configuration
            symbols: Symbol catalog for volume conversion
        """
        self.protocol = protocol
        self.config = config
        self.symbols = symbols
        
        # Rate limiter for trading operations (50 requests per second)
        self._rate_limiter = TokenBucketRateLimiter(
            rate=config.rate_limit_trading,
            capacity=config.rate_limit_trading
        )
        
        # Cached positions and orders
        self._positions: list[Position] = []
        self._orders: list[Order] = []
        self._positions_lock = asyncio.Lock()
        self._orders_lock = asyncio.Lock()
    
    async def place_market_order(
        self,
        symbol: str,
        side: TradeSide,
        volume: float,
        *,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        comment: Optional[str] = None,
        label: Optional[str] = None,
    ) -> Position:
        """Place a market order.
        
        Args:
            symbol: Symbol name (e.g., "EURUSD")
            side: Trade side (BUY or SELL)
            volume: Volume in lots
            stop_loss: Stop loss price (optional)
            take_profit: Take profit price (optional)
            comment: Order comment (optional)
            label: Order label (optional)
            
        Returns:
            Created position
            
        Raises:
            TradingError: If order fails
            MarketClosedError: If market is closed
            
        Example:
            >>> position = await trading.place_market_order(
            ...     symbol="EURUSD",
            ...     side=TradeSide.BUY,
            ...     volume=0.01,
            ...     stop_loss=1.0900,
            ...     take_profit=1.1100
            ... )
        """
        await self._rate_limiter.acquire()
        
        try:
            from ..messages.OpenApiMessages_pb2 import (
                ProtoOANewOrderReq,
                ProtoOAExecutionEvent,
            )
            from ..messages.OpenApiModelMessages_pb2 import (
                ProtoOAOrderType,
                ProtoOATradeSide,
            )
            
            # Get symbol info for volume conversion
            symbol_info = await self.symbols.get_symbol(symbol)
            if not symbol_info:
                raise TradingError(f"Symbol not found: {symbol}")
            
            # Build request
            req = ProtoOANewOrderReq()
            req.ctidTraderAccountId = self.config.account_id
            req.symbolId = symbol_info.id
            # Order type is MARKET; trade side is BUY/SELL.
            req.orderType = ProtoOAOrderType.MARKET
            req.tradeSide = side.to_proto(ProtoOATradeSide)
            req.volume = symbol_info.lots_to_protocol_volume(volume)
            
            if comment:
                req.comment = comment
            if label:
                req.label = label
            
            # Send request
            response = await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="NewMarketOrder"
            )
            
            # Check for error
            if self._is_error_response(response):
                error_code = getattr(response, 'errorCode', 'UNKNOWN')
                error_desc = getattr(response, 'description', '')
                
                if error_code == 'MARKET_CLOSED':
                    raise MarketClosedError(error_desc)
                
                raise TradingError(
                    f"Order failed: {error_code}",
                    code=error_code,
                    description=error_desc
                )
            
            # Extract position from execution event
            if isinstance(response, ProtoOAExecutionEvent):
                if hasattr(response, 'position'):
                    # Prefer execution event data, but reconcile immediately to get authoritative volume/price.
                    position = self._parse_position(response.position, symbol_info)

                    # Reconcile to refresh positions and pull the updated position fields.
                    # In practice, the execution event may arrive before the position object is fully populated,
                    # so we retry reconciliation briefly.
                    try:
                        for _ in range(5):
                            await self.refresh_positions()
                            refreshed = await self._find_position_by_id(position.id)
                            if refreshed is not None and refreshed.volume > 0 and refreshed.entry_price > 0:
                                position = refreshed
                                break
                            await asyncio.sleep(0.2)
                    except Exception:
                        # Best effort; keep execution event position
                        pass

                    # Apply SL/TP if requested
                    if stop_loss or take_profit:
                        await self.modify_position(
                            position.id,
                            stop_loss=stop_loss,
                            take_profit=take_profit
                        )

                        # Update position object
                        if stop_loss:
                            position.stop_loss = stop_loss
                        if take_profit:
                            position.take_profit = take_profit

                    # Update cache
                    async with self._positions_lock:
                        # replace existing if present
                        self._positions = [p for p in self._positions if p.id != position.id]
                        self._positions.append(position)

                    logger.info(
                        f"Market order executed: {symbol} {side.name} {volume} lots, "
                        f"position={position.id}, price={position.entry_price}"
                    )

                    return position
            
            # Always log what we got back for market orders when we can't extract a position.
            if isinstance(response, ProtoOAExecutionEvent):
                logger.error(
                    "Market order execution event missing position. summary=%s",
                    _summarize_execution_event(response),
                )
                # Extra: log a protobuf dict if possible (usually small in rejection cases).
                try:
                    from google.protobuf.json_format import MessageToDict  # type: ignore

                    d = MessageToDict(response, preserving_proto_field_name=True)
                    logger.error("Market order execution event raw_dict=%s", d)
                except Exception:
                    pass
            else:
                logger.warning(
                    "Market order response was not execution event. type=%s repr=%r",
                    type(response).__name__,
                    response,
                )

            raise TradingError("No position in execution response")
        
        except (TradingError, MarketClosedError):
            raise
        except Exception as e:
            logger.error(f"Market order error: {e}", exc_info=True)
            raise TradingError(f"Market order failed: {e}")
    
    async def place_limit_order(
        self,
        symbol: str,
        side: TradeSide,
        volume: float,
        price: float,
        *,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        time_in_force: TimeInForce = TimeInForce.GOOD_TILL_CANCEL,
        expiration_timestamp: Optional[int] = None,
        comment: Optional[str] = None,
        label: Optional[str] = None,
        # Advanced protection/behavior (protobuf-supported)
        slippage_in_points: int | None = None,
        relative_stop_loss: int | None = None,
        relative_take_profit: int | None = None,
        guaranteed_stop_loss: bool | None = None,
        trailing_stop_loss: bool | None = None,
        stop_trigger_method: OrderTriggerMethod | None = None,
        # Hedging/netting support: target an existing position (account/broker dependent)
        position_id: int | None = None,
    ) -> Order:
        """Place a limit order.
        
        Args:
            symbol: Symbol name
            side: Trade side
            volume: Volume in lots
            price: Limit price
            stop_loss: Stop loss price (optional)
            take_profit: Take profit price (optional)
            time_in_force: Time in force
            expiration_timestamp: Expiration time in milliseconds (for GTD)
            comment: Order comment (optional)
            label: Order label (optional)
            
        Returns:
            Created order
            
        Raises:
            TradingError: If order fails
        """
        await self._rate_limiter.acquire()
        
        try:
            from ..messages.OpenApiMessages_pb2 import ProtoOANewOrderReq
            from ..messages.OpenApiModelMessages_pb2 import (
                ProtoOAOrderType,
                ProtoOATradeSide,
                ProtoOATimeInForce,
            )
            
            symbol_info = await self.symbols.get_symbol(symbol)
            if not symbol_info:
                raise TradingError(f"Symbol not found: {symbol}")
            
            req = ProtoOANewOrderReq()
            req.ctidTraderAccountId = self.config.account_id
            req.symbolId = symbol_info.id
            req.orderType = ProtoOAOrderType.LIMIT
            req.tradeSide = side.to_proto(ProtoOATradeSide)
            req.volume = symbol_info.lots_to_protocol_volume(volume)
            req.limitPrice = symbol_info.round_price(price)
            
            if stop_loss:
                req.stopLoss = symbol_info.round_price(stop_loss)
            if take_profit:
                req.takeProfit = symbol_info.round_price(take_profit)
            
            req.timeInForce = time_in_force.to_proto(ProtoOATimeInForce)
            
            if expiration_timestamp:
                req.expirationTimestamp = expiration_timestamp
            
            if comment:
                req.comment = comment
            if label:
                req.label = label

            # Advanced fields (protobuf-supported)
            if slippage_in_points is not None:
                req.slippageInPoints = int(slippage_in_points)
            if relative_stop_loss is not None:
                req.relativeStopLoss = int(relative_stop_loss)
            if relative_take_profit is not None:
                req.relativeTakeProfit = int(relative_take_profit)
            if guaranteed_stop_loss is not None:
                req.guaranteedStopLoss = bool(guaranteed_stop_loss)
            if trailing_stop_loss is not None:
                req.trailingStopLoss = bool(trailing_stop_loss)
            if stop_trigger_method is not None:
                from ..messages.OpenApiModelMessages_pb2 import ProtoOAOrderTriggerMethod

                req.stopTriggerMethod = stop_trigger_method.to_proto(ProtoOAOrderTriggerMethod)
            if position_id is not None:
                req.positionId = int(position_id)
            
            # Generate client order ID for tracking
            client_order_id = str(uuid.uuid4())
            req.clientOrderId = client_order_id
            
            response = await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="NewLimitOrder"
            )
            
            if self._is_error_response(response):
                error_code = getattr(response, 'errorCode', 'UNKNOWN')
                error_desc = getattr(response, 'description', '')
                raise OrderError(
                    f"Limit order failed: {error_code}",
                    code=error_code,
                    description=error_desc
                )
            
            # Refresh orders to get the created order
            await asyncio.sleep(0.2)  # Small delay for server processing
            await self.refresh_orders()
            
            # Find the created order by client order ID
            order = await self._find_order_by_client_id(client_order_id)
            
            if order:
                logger.info(
                    f"Limit order created: {symbol} {side.name} {volume} lots @ {price}, "
                    f"order={order.id}"
                )
                return order
            
            # If not found, create a placeholder order
            order = Order(
                id=0,
                symbol_id=symbol_info.id,
                symbol_name=symbol,
                volume=volume,
                side=side.name,
                order_type="LIMIT",
                limit_price=price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                client_order_id=client_order_id
            )
            
            return order
        
        except (TradingError, OrderError):
            raise
        except Exception as e:
            logger.error(f"Limit order error: {e}", exc_info=True)
            raise OrderError(f"Limit order failed: {e}")
    
    async def place_stop_order(
        self,
        symbol: str,
        side: TradeSide,
        volume: float,
        stop_price: float,
        *,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        time_in_force: TimeInForce = TimeInForce.GOOD_TILL_CANCEL,
        expiration_timestamp: Optional[int] = None,
        comment: Optional[str] = None,
        label: Optional[str] = None,
        # Advanced protection/behavior (protobuf-supported)
        slippage_in_points: int | None = None,
        relative_stop_loss: int | None = None,
        relative_take_profit: int | None = None,
        guaranteed_stop_loss: bool | None = None,
        trailing_stop_loss: bool | None = None,
        stop_trigger_method: OrderTriggerMethod | None = None,
        position_id: int | None = None,
    ) -> Order:
        """Place a stop order.
        
        A stop order becomes a market order when the stop price is reached.
        
        Args:
            symbol: Symbol name
            side: Trade side
            volume: Volume in lots
            stop_price: Stop trigger price
            stop_loss: Stop loss price (optional)
            take_profit: Take profit price (optional)
            time_in_force: Time in force
            expiration_timestamp: Expiration time in milliseconds (for GTD)
            comment: Order comment (optional)
            label: Order label (optional)
            
        Returns:
            Created order
            
        Raises:
            TradingError: If order fails
        """
        await self._rate_limiter.acquire()
        
        try:
            from ..messages.OpenApiMessages_pb2 import ProtoOANewOrderReq
            from ..messages.OpenApiModelMessages_pb2 import (
                ProtoOAOrderType,
                ProtoOATradeSide,
                ProtoOATimeInForce,
            )
            
            symbol_info = await self.symbols.get_symbol(symbol)
            if not symbol_info:
                raise TradingError(f"Symbol not found: {symbol}")
            
            req = ProtoOANewOrderReq()
            req.ctidTraderAccountId = self.config.account_id
            req.symbolId = symbol_info.id
            req.orderType = ProtoOAOrderType.STOP
            req.tradeSide = side.to_proto(ProtoOATradeSide)
            req.volume = symbol_info.lots_to_protocol_volume(volume)
            req.stopPrice = symbol_info.round_price(stop_price)
            
            if stop_loss:
                req.stopLoss = symbol_info.round_price(stop_loss)
            if take_profit:
                req.takeProfit = symbol_info.round_price(take_profit)
            
            req.timeInForce = time_in_force.to_proto(ProtoOATimeInForce)
            
            if expiration_timestamp:
                req.expirationTimestamp = expiration_timestamp
            
            if comment:
                req.comment = comment
            if label:
                req.label = label

            # Advanced fields (protobuf-supported)
            if slippage_in_points is not None:
                req.slippageInPoints = int(slippage_in_points)
            if relative_stop_loss is not None:
                req.relativeStopLoss = int(relative_stop_loss)
            if relative_take_profit is not None:
                req.relativeTakeProfit = int(relative_take_profit)
            if guaranteed_stop_loss is not None:
                req.guaranteedStopLoss = bool(guaranteed_stop_loss)
            if trailing_stop_loss is not None:
                req.trailingStopLoss = bool(trailing_stop_loss)
            if stop_trigger_method is not None:
                from ..messages.OpenApiModelMessages_pb2 import ProtoOAOrderTriggerMethod

                req.stopTriggerMethod = stop_trigger_method.to_proto(ProtoOAOrderTriggerMethod)
            if position_id is not None:
                req.positionId = int(position_id)
            
            # Generate client order ID for tracking
            client_order_id = str(uuid.uuid4())
            req.clientOrderId = client_order_id
            
            response = await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="NewStopOrder"
            )
            
            if self._is_error_response(response):
                error_code = getattr(response, 'errorCode', 'UNKNOWN')
                error_desc = getattr(response, 'description', '')
                raise OrderError(
                    f"Stop order failed: {error_code}",
                    code=error_code,
                    description=error_desc
                )
            
            # Refresh orders to get the created order
            await asyncio.sleep(0.2)
            await self.refresh_orders()
            
            # Find the created order by client order ID
            order = await self._find_order_by_client_id(client_order_id)
            
            if order:
                logger.info(
                    f"Stop order created: {symbol} {side.name} {volume} lots @ {stop_price}, "
                    f"order={order.id}"
                )
                return order
            
            # If not found, create a placeholder order
            order = Order(
                id=0,
                symbol_id=symbol_info.id,
                symbol_name=symbol,
                volume=volume,
                side=side.name,
                order_type="STOP",
                stop_price=stop_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                client_order_id=client_order_id
            )
            
            return order
        
        except (TradingError, OrderError):
            raise
        except Exception as e:
            logger.error(f"Stop order error: {e}", exc_info=True)
            raise OrderError(f"Stop order failed: {e}")
    
    async def place_stop_limit_order(
        self,
        symbol: str,
        side: TradeSide,
        volume: float,
        stop_price: float,
        limit_price: float,
        *,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        time_in_force: TimeInForce = TimeInForce.GOOD_TILL_CANCEL,
        expiration_timestamp: Optional[int] = None,
        comment: Optional[str] = None,
        label: Optional[str] = None,
        # Advanced protection/behavior (protobuf-supported)
        slippage_in_points: int | None = None,
        relative_stop_loss: int | None = None,
        relative_take_profit: int | None = None,
        guaranteed_stop_loss: bool | None = None,
        trailing_stop_loss: bool | None = None,
        stop_trigger_method: OrderTriggerMethod | None = None,
        position_id: int | None = None,
    ) -> Order:
        """Place a stop-limit order.
        
        A stop-limit order becomes a limit order when the stop price is reached.
        
        Args:
            symbol: Symbol name
            side: Trade side
            volume: Volume in lots
            stop_price: Stop trigger price
            limit_price: Limit price (after stop is triggered)
            stop_loss: Stop loss price (optional)
            take_profit: Take profit price (optional)
            time_in_force: Time in force
            expiration_timestamp: Expiration time in milliseconds (for GTD)
            comment: Order comment (optional)
            label: Order label (optional)
            
        Returns:
            Created order
            
        Raises:
            TradingError: If order fails
        """
        await self._rate_limiter.acquire()
        
        try:
            from ..messages.OpenApiMessages_pb2 import ProtoOANewOrderReq
            from ..messages.OpenApiModelMessages_pb2 import (
                ProtoOAOrderType,
                ProtoOATradeSide,
                ProtoOATimeInForce,
            )
            
            symbol_info = await self.symbols.get_symbol(symbol)
            if not symbol_info:
                raise TradingError(f"Symbol not found: {symbol}")
            
            req = ProtoOANewOrderReq()
            req.ctidTraderAccountId = self.config.account_id
            req.symbolId = symbol_info.id
            req.orderType = ProtoOAOrderType.STOP_LIMIT
            req.tradeSide = side.to_proto(ProtoOATradeSide)
            req.volume = symbol_info.lots_to_protocol_volume(volume)
            req.stopPrice = symbol_info.round_price(stop_price)
            req.limitPrice = symbol_info.round_price(limit_price)
            
            if stop_loss:
                req.stopLoss = symbol_info.round_price(stop_loss)
            if take_profit:
                req.takeProfit = symbol_info.round_price(take_profit)
            
            req.timeInForce = time_in_force.to_proto(ProtoOATimeInForce)
            
            if expiration_timestamp:
                req.expirationTimestamp = expiration_timestamp
            
            if comment:
                req.comment = comment
            if label:
                req.label = label

            # Advanced fields (protobuf-supported)
            if slippage_in_points is not None:
                req.slippageInPoints = int(slippage_in_points)
            if relative_stop_loss is not None:
                req.relativeStopLoss = int(relative_stop_loss)
            if relative_take_profit is not None:
                req.relativeTakeProfit = int(relative_take_profit)
            if guaranteed_stop_loss is not None:
                req.guaranteedStopLoss = bool(guaranteed_stop_loss)
            if trailing_stop_loss is not None:
                req.trailingStopLoss = bool(trailing_stop_loss)
            if stop_trigger_method is not None:
                from ..messages.OpenApiModelMessages_pb2 import ProtoOAOrderTriggerMethod

                req.stopTriggerMethod = stop_trigger_method.to_proto(ProtoOAOrderTriggerMethod)
            if position_id is not None:
                req.positionId = int(position_id)
            
            # Generate client order ID for tracking
            client_order_id = str(uuid.uuid4())
            req.clientOrderId = client_order_id
            
            response = await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="NewStopLimitOrder"
            )
            
            if self._is_error_response(response):
                error_code = getattr(response, 'errorCode', 'UNKNOWN')
                error_desc = getattr(response, 'description', '')
                raise OrderError(
                    f"Stop-limit order failed: {error_code}",
                    code=error_code,
                    description=error_desc
                )
            
            # Refresh orders to get the created order
            await asyncio.sleep(0.2)
            await self.refresh_orders()
            
            # Find the created order by client order ID
            order = await self._find_order_by_client_id(client_order_id)
            
            if order:
                logger.info(
                    f"Stop-limit order created: {symbol} {side.name} {volume} lots, "
                    f"stop={stop_price}, limit={limit_price}, order={order.id}"
                )
                return order
            
            # If not found, create a placeholder order
            order = Order(
                id=0,
                symbol_id=symbol_info.id,
                symbol_name=symbol,
                volume=volume,
                side=side.name,
                order_type="STOP_LIMIT",
                stop_price=stop_price,
                limit_price=limit_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                client_order_id=client_order_id
            )
            
            return order
        
        except (TradingError, OrderError):
            raise
        except Exception as e:
            logger.error(f"Stop-limit order error: {e}", exc_info=True)
            raise OrderError(f"Stop-limit order failed: {e}")
    
    async def close_position(
        self,
        position_id: int,
        volume: Optional[float] = None
    ):
        """Close a position (fully or partially).
        
        Args:
            position_id: Position ID to close
            volume: Volume to close in lots (None = close all)
            
        Raises:
            TradingError: If close fails
        """
        await self._rate_limiter.acquire()
        
        try:
            from ..messages.OpenApiMessages_pb2 import ProtoOAClosePositionReq
            
            req = ProtoOAClosePositionReq()
            req.ctidTraderAccountId = self.config.account_id
            req.positionId = position_id

            # The protobuf schema for ProtoOAClosePositionReq uses a required `volume`.
            # If caller doesn't pass a volume, we close the full position volume.
            close_lots: Optional[float] = volume
            if close_lots is None:
                position = await self._find_position_by_id(position_id)
                if position is None:
                    await self.refresh_positions()
                    position = await self._find_position_by_id(position_id)
                if position is None:
                    # If the position is not found, it may have already been closed by the server
                    # (e.g., immediately after a partial close or due to SL/TP).
                    logger.info(f"Position {position_id} not found; assuming already closed")
                    return
                close_lots = position.volume

            position = await self._find_position_by_id(position_id)
            if position and position.symbol_name:
                symbol_info = await self.symbols.get_symbol(position.symbol_name)
                if symbol_info:
                    req.volume = symbol_info.lots_to_protocol_volume(close_lots)
                else:
                    # Fallback: assume volume is already in protocol units of cents
                    req.volume = int(round(close_lots * 100.0))
            else:
                # If we don't know the symbol, best-effort fallback
                req.volume = int(round(close_lots * 100.0))
            
            response = await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="ClosePosition"
            )
            
            if self._is_error_response(response):
                error_code = getattr(response, 'errorCode', 'UNKNOWN')
                error_desc = getattr(response, 'description', '')
                raise TradingError(
                    f"Close position failed: {error_code}",
                    code=error_code,
                    description=error_desc
                )
            
            # Remove from cache
            async with self._positions_lock:
                self._positions = [p for p in self._positions if p.id != position_id]
            
            logger.info(f"Position closed: {position_id}")
        
        except TradingError:
            raise
        except Exception as e:
            logger.error(f"Close position error: {e}", exc_info=True)
            raise TradingError(f"Close position failed: {e}")
    
    async def modify_position(
        self,
        position_id: int,
        *,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        guaranteed_stop_loss: bool | None = None,
        trailing_stop_loss: bool | None = None,
        stop_loss_trigger_method: OrderTriggerMethod | None = None,
    ):
        """Modify position SL/TP.
        
        Args:
            position_id: Position ID
            stop_loss: New stop loss price (optional)
            take_profit: New take profit price (optional)
            
        Raises:
            TradingError: If modification fails
        """
        await self._rate_limiter.acquire()
        
        try:
            from ..messages.OpenApiMessages_pb2 import ProtoOAAmendPositionSLTPReq
            
            req = ProtoOAAmendPositionSLTPReq()
            req.ctidTraderAccountId = self.config.account_id
            req.positionId = position_id
            
            if stop_loss is not None:
                req.stopLoss = float(stop_loss)
            if take_profit is not None:
                req.takeProfit = float(take_profit)
            if guaranteed_stop_loss is not None:
                req.guaranteedStopLoss = bool(guaranteed_stop_loss)
            if trailing_stop_loss is not None:
                req.trailingStopLoss = bool(trailing_stop_loss)
            if stop_loss_trigger_method is not None:
                from ..messages.OpenApiModelMessages_pb2 import ProtoOAOrderTriggerMethod

                req.stopLossTriggerMethod = stop_loss_trigger_method.to_proto(ProtoOAOrderTriggerMethod)
            
            response = await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="AmendPositionSLTP"
            )
            
            if self._is_error_response(response):
                error_code = getattr(response, 'errorCode', 'UNKNOWN')
                error_desc = getattr(response, 'description', '')
                raise TradingError(
                    f"Modify position failed: {error_code}",
                    code=error_code,
                    description=error_desc
                )
            
            logger.info(f"Position modified: {position_id}, SL={stop_loss}, TP={take_profit}")
        
        except TradingError:
            raise
        except Exception as e:
            logger.error(f"Modify position error: {e}", exc_info=True)
            raise TradingError(f"Modify position failed: {e}")
    
    async def modify_order(
        self,
        order_id: int,
        *,
        volume: float | None = None,
        limit_price: float | None = None,
        stop_price: float | None = None,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        expiration_timestamp: int | None = None,
        slippage_in_points: int | None = None,
        relative_stop_loss: int | None = None,
        relative_take_profit: int | None = None,
        guaranteed_stop_loss: bool | None = None,
        trailing_stop_loss: bool | None = None,
        stop_trigger_method: OrderTriggerMethod | None = None,
    ):
        """Amend a pending order.

        Supports price/SL/TP/volume/expiration plus advanced flags supported by
        `ProtoOAAmendOrderReq` (slippage, relative SL/TP, guaranteed/trailing SL,
        stop trigger method).

        Note: price fields are expected in *absolute price* terms.
        """
        await self._rate_limiter.acquire()

        try:
            from ..messages.OpenApiMessages_pb2 import ProtoOAAmendOrderReq

            req = ProtoOAAmendOrderReq()
            req.ctidTraderAccountId = self.config.account_id
            req.orderId = int(order_id)

            # Volume in protocol units is symbol-dependent. If caller passes volume, we attempt conversion
            # based on cached order symbol name.
            if volume is not None:
                order = None
                async with self._orders_lock:
                    order = next((o for o in self._orders if o.id == order_id), None)
                if order and order.symbol_name:
                    symbol_info = await self.symbols.get_symbol(order.symbol_name)
                    if symbol_info:
                        req.volume = symbol_info.lots_to_protocol_volume(volume)
                    else:
                        req.volume = int(round(volume * 100.0))
                else:
                    req.volume = int(round(volume * 100.0))

            if limit_price is not None:
                req.limitPrice = float(limit_price)
            if stop_price is not None:
                req.stopPrice = float(stop_price)
            if stop_loss is not None:
                req.stopLoss = float(stop_loss)
            if take_profit is not None:
                req.takeProfit = float(take_profit)
            if expiration_timestamp is not None:
                req.expirationTimestamp = int(expiration_timestamp)

            if slippage_in_points is not None:
                req.slippageInPoints = int(slippage_in_points)
            if relative_stop_loss is not None:
                req.relativeStopLoss = int(relative_stop_loss)
            if relative_take_profit is not None:
                req.relativeTakeProfit = int(relative_take_profit)
            if guaranteed_stop_loss is not None:
                req.guaranteedStopLoss = bool(guaranteed_stop_loss)
            if trailing_stop_loss is not None:
                req.trailingStopLoss = bool(trailing_stop_loss)
            if stop_trigger_method is not None:
                from ..messages.OpenApiModelMessages_pb2 import ProtoOAOrderTriggerMethod

                req.stopTriggerMethod = stop_trigger_method.to_proto(ProtoOAOrderTriggerMethod)

            response = await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="AmendOrder",
            )

            if self._is_error_response(response):
                error_code = getattr(response, "errorCode", "UNKNOWN")
                error_desc = getattr(response, "description", "")
                raise OrderError(
                    f"Modify order failed: {error_code}",
                    code=error_code,
                    description=error_desc,
                )

            logger.info(
                f"Order modified: {order_id}, vol={volume}, limit={limit_price}, stop={stop_price}, SL={stop_loss}, TP={take_profit}"
            )
        except OrderError:
            raise
        except Exception as e:
            logger.error(f"Modify order error: {e}", exc_info=True)
            raise OrderError(f"Modify order failed: {e}")

    async def cancel_order(self, order_id: int):
        """Cancel a pending order.
        
        Args:
            order_id: Order ID to cancel
            
        Raises:
            TradingError: If cancellation fails
        """
        await self._rate_limiter.acquire()
        
        try:
            from ..messages.OpenApiMessages_pb2 import ProtoOACancelOrderReq
            
            req = ProtoOACancelOrderReq()
            req.ctidTraderAccountId = self.config.account_id
            req.orderId = order_id
            
            response = await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="CancelOrder"
            )
            
            if self._is_error_response(response):
                error_code = getattr(response, 'errorCode', 'UNKNOWN')
                error_desc = getattr(response, 'description', '')
                raise OrderError(
                    f"Cancel order failed: {error_code}",
                    code=error_code,
                    description=error_desc
                )
            
            # Remove from cache
            async with self._orders_lock:
                self._orders = [o for o in self._orders if o.id != order_id]
            
            logger.info(f"Order cancelled: {order_id}")
        
        except OrderError:
            raise
        except Exception as e:
            logger.error(f"Cancel order error: {e}", exc_info=True)
            raise OrderError(f"Cancel order failed: {e}")
    
    async def get_positions(self) -> list[Position]:
        """Get all open positions.
        
        Returns:
            List of positions
        """
        await self.refresh_positions()
        
        async with self._positions_lock:
            return self._positions.copy()
    
    async def get_orders(self) -> list[Order]:
        """Get all pending orders.
        
        Returns:
            List of orders
        """
        await self.refresh_orders()
        
        async with self._orders_lock:
            return self._orders.copy()

    async def iter_deals_history(
        self,
        *,
        from_timestamp: int,
        to_timestamp: int,
        max_rows: int = 500,
    ):
        """Iterate executed deals in a time window.

        This uses `ProtoOADealListReq` / `ProtoOADealListRes` and paginates while `hasMore` is true.

        Args:
            from_timestamp: start time in milliseconds (inclusive)
            to_timestamp: end time in milliseconds (inclusive)
            max_rows: page size (server may cap)

        Yields:
            `models.Deal` objects
        """
        await self._rate_limiter.acquire()

        from ..messages.OpenApiMessages_pb2 import ProtoOADealListReq

        # cTrader paging model: request a window; response returns `deal[]` and `hasMore`.
        # For safety, when hasMore is true we advance the window start based on the last deal timestamp.
        cursor_from = int(from_timestamp)

        while True:
            req = ProtoOADealListReq()
            req.ctidTraderAccountId = self.config.account_id
            req.fromTimestamp = int(cursor_from)
            req.toTimestamp = int(to_timestamp)
            if max_rows:
                req.maxRows = int(max_rows)

            response = await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="DealList",
            )

            deals_pb = list(getattr(response, "deal", []) or [])
            for d in deals_pb:
                yield await self._parse_deal(d)

            has_more = bool(getattr(response, "hasMore", False))
            if not has_more or not deals_pb:
                break

            # Advance cursor conservatively.
            last = deals_pb[-1]
            last_ts = getattr(last, "executionTimestamp", None)
            if last_ts is None:
                last_ts = getattr(last, "createTimestamp", None)
            if isinstance(last_ts, (int, float)):
                cursor_from = int(last_ts) + 1
            else:
                # If timestamps are missing, avoid infinite loop
                break

    async def get_deals_history(
        self,
        *,
        from_timestamp: int,
        to_timestamp: int,
        max_rows: int = 500,
    ) -> list[Deal]:
        """Get executed deals in a time window.

        Convenience wrapper over `iter_deals_history`.
        """
        deals: list[Deal] = []
        async for d in self.iter_deals_history(
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            max_rows=max_rows,
        ):
            deals.append(d)
        return deals
    
    async def refresh_positions(self):
        """Refresh positions from server."""
        try:
            from ..messages.OpenApiMessages_pb2 import ProtoOAReconcileReq
            
            req = ProtoOAReconcileReq()
            req.ctidTraderAccountId = self.config.account_id
            
            response = await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="Reconcile"
            )
            
            positions = []
            for pos_data in getattr(response, 'position', []):
                symbol_id = pos_data.tradeData.symbolId
                symbol_name = await self.symbols.get_symbol_name(symbol_id)
                symbol_info = await self.symbols.get_symbol(symbol_name) if symbol_name else None
                
                position = self._parse_position(pos_data, symbol_info)
                positions.append(position)
            
            async with self._positions_lock:
                self._positions = positions
        
        except Exception as e:
            logger.error(f"Refresh positions error: {e}", exc_info=True)
    
    async def refresh_orders(self):
        """Refresh orders from server."""
        try:
            from ..messages.OpenApiMessages_pb2 import ProtoOAReconcileReq
            
            req = ProtoOAReconcileReq()
            req.ctidTraderAccountId = self.config.account_id
            
            response = await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="Reconcile"
            )
            
            orders = []
            for order_data in getattr(response, 'order', []):
                symbol_id = order_data.tradeData.symbolId
                symbol_name = await self.symbols.get_symbol_name(symbol_id)
                symbol_info = await self.symbols.get_symbol(symbol_name) if symbol_name else None
                
                order = self._parse_order(order_data, symbol_info)
                orders.append(order)
            
            async with self._orders_lock:
                self._orders = orders
        
        except Exception as e:
            logger.error(f"Refresh orders error: {e}", exc_info=True)
    
    async def close_positions_bulk(self, position_ids: list[int], *, concurrency: int = 5):
        """Close multiple positions with bounded concurrency."""
        from ..utils.concurrency import gather_limited

        async def make(pid: int):
            return await self.close_position(pid)

        factories = [lambda pid=pid: make(pid) for pid in position_ids]
        return await gather_limited(factories, limit=concurrency)

    async def cancel_orders_bulk(self, order_ids: list[int], *, concurrency: int = 10):
        """Cancel multiple orders with bounded concurrency."""
        from ..utils.concurrency import gather_limited

        async def make(oid: int):
            return await self.cancel_order(oid)

        factories = [lambda oid=oid: make(oid) for oid in order_ids]
        return await gather_limited(factories, limit=concurrency)

    async def modify_orders_bulk(
        self,
        modifications: list[
            tuple[
                int,
                float | None,
                float | None,
                float | None,
                float | None,
                float | None,
                int | None,
            ]
        ],
        *,
        concurrency: int = 10,
    ):
        """Amend multiple orders with bounded concurrency.

        Args:
            modifications: list of tuples:
                (order_id, volume, limit_price, stop_price, stop_loss, take_profit, expiration_timestamp)
            concurrency: parallelism limit
        """
        from ..utils.concurrency import gather_limited

        async def make(oid: int, vol, lp, sp, sl, tp, exp):
            return await self.modify_order(
                oid,
                volume=vol,
                limit_price=lp,
                stop_price=sp,
                stop_loss=sl,
                take_profit=tp,
                expiration_timestamp=exp,
            )

        factories = [
            lambda oid=oid, vol=vol, lp=lp, sp=sp, sl=sl, tp=tp, exp=exp: make(oid, vol, lp, sp, sl, tp, exp)
            for (oid, vol, lp, sp, sl, tp, exp) in modifications
        ]
        return await gather_limited(factories, limit=concurrency)

    async def modify_positions_bulk(
        self,
        modifications: list[tuple[int, float | None, float | None]],
        *,
        concurrency: int = 10,
    ):
        """Modify SL/TP for multiple positions.

        Args:
            modifications: list of (position_id, stop_loss, take_profit)
            concurrency: parallelism limit
        """
        from ..utils.concurrency import gather_limited

        async def make(pid: int, sl: float | None, tp: float | None):
            return await self.modify_position(pid, stop_loss=sl, take_profit=tp)

        factories = [lambda pid=pid, sl=sl, tp=tp: make(pid, sl, tp) for pid, sl, tp in modifications]
        return await gather_limited(factories, limit=concurrency)

    async def close_all_positions(self):
        """Close all open positions."""
        positions = await self.get_positions()
        await self.close_positions_bulk([p.id for p in positions])

    async def cancel_all_orders(self):
        """Cancel all pending orders."""
        orders = await self.get_orders()
        await self.cancel_orders_bulk([o.id for o in orders])
    
    def _parse_position(self, pos_data: any, symbol_info: Optional[any]) -> Position:
        """Parse position from protobuf data."""
        from ..enums import TradeSide
        from ..messages.OpenApiModelMessages_pb2 import ProtoOATradeSide
        
        volume_lots = (
            symbol_info.protocol_volume_to_lots(pos_data.tradeData.volume)
            if symbol_info else pos_data.tradeData.volume / 100.0
        )
        
        return Position(
            id=pos_data.positionId,
            symbol_id=pos_data.tradeData.symbolId,
            symbol_name=symbol_info.name if symbol_info else None,
            volume=volume_lots,
            side=TradeSide.from_proto(ProtoOATradeSide, pos_data.tradeData.tradeSide).name,
            # `price` is the open price for positions in ProtoOAPosition
            entry_price=float(getattr(pos_data, 'price', 0.0)),
            stop_loss=(float(getattr(pos_data, 'stopLoss', 0.0)) if getattr(pos_data, 'stopLoss', 0) else None),
            take_profit=(float(getattr(pos_data, 'takeProfit', 0.0)) if getattr(pos_data, 'takeProfit', 0) else None),
            last_update_timestamp=(int(getattr(pos_data, 'utcLastUpdateTimestamp', 0)) or None),
        )
    
    async def _parse_deal(self, deal_data: any) -> Deal:
        """Parse a deal from protobuf data into `models.Deal`."""
        symbol_id = int(getattr(deal_data, "symbolId", 0) or 0) or None
        symbol_name = None
        symbol_info = None
        if symbol_id:
            try:
                symbol_name = await self.symbols.get_symbol_name(symbol_id)
                if symbol_name:
                    symbol_info = await self.symbols.get_symbol(symbol_name)
            except Exception:
                symbol_name = None
                symbol_info = None

        raw_vol = getattr(deal_data, "volume", None)
        lots = None
        if isinstance(raw_vol, (int, float)) and symbol_info is not None:
            try:
                lots = float(symbol_info.protocol_volume_to_lots(int(raw_vol)))
            except Exception:
                lots = None
        elif isinstance(raw_vol, (int, float)):
            # Fallback heuristic used elsewhere in this repo: proto volume ~ cents => lots ~ volume/100.
            lots = float(raw_vol) / 100.0

        ts = getattr(deal_data, "executionTimestamp", None)
        if ts is None:
            ts = getattr(deal_data, "createTimestamp", None)

        return Deal(
            deal_id=int(getattr(deal_data, "dealId", 0) or 0),
            order_id=(int(getattr(deal_data, "orderId", 0) or 0) or None),
            position_id=(int(getattr(deal_data, "positionId", 0) or 0) or None),
            symbol_id=symbol_id,
            symbol_name=(str(symbol_name) if symbol_name else None),
            side=str(getattr(deal_data, "tradeSide", "")) or None,
            volume=lots,
            execution_price=(
                float(getattr(deal_data, "executionPrice", 0.0) or 0.0)
                if getattr(deal_data, "executionPrice", None) is not None
                else None
            ),
            commission=float(getattr(deal_data, "commission", 0.0) or 0.0),
            swap=float(getattr(deal_data, "swap", 0.0) or 0.0),
            timestamp=(int(ts) if isinstance(ts, (int, float)) else None),
        )

    def _parse_order(self, order_data: any, symbol_info: Optional[any]) -> Order:
        """Parse order from protobuf data."""
        from ..enums import TradeSide
        from ..messages.OpenApiModelMessages_pb2 import ProtoOATradeSide
        
        volume_lots = (
            symbol_info.protocol_volume_to_lots(order_data.tradeData.volume)
            if symbol_info else order_data.tradeData.volume / 100.0
        )
        
        return Order(
            id=order_data.orderId,
            symbol_id=order_data.tradeData.symbolId,
            symbol_name=symbol_info.name if symbol_info else None,
            volume=volume_lots,
            side=TradeSide.from_proto(ProtoOATradeSide, order_data.tradeData.tradeSide).name,
            limit_price=getattr(order_data, 'limitPrice', None),
            stop_price=getattr(order_data, 'stopPrice', None),
            stop_loss=getattr(order_data, 'stopLoss', None),
            take_profit=getattr(order_data, 'takeProfit', None),
            client_order_id=getattr(order_data, 'clientOrderId', None),
        )
    
    async def _find_position_by_id(self, position_id: int) -> Optional[Position]:
        """Find position by ID in cache."""
        async with self._positions_lock:
            return next((p for p in self._positions if p.id == position_id), None)
    
    async def _find_order_by_client_id(self, client_order_id: str) -> Optional[Order]:
        """Find order by client order ID in cache."""
        async with self._orders_lock:
            return next(
                (o for o in self._orders if o.client_order_id == client_order_id),
                None
            )
    
    @staticmethod
    def _is_error_response(response: any) -> bool:
        """Check if response is an error."""
        try:
            from ..messages.OpenApiMessages_pb2 import ProtoOAErrorRes
            from ..messages.OpenApiCommonMessages_pb2 import ProtoErrorRes
            return isinstance(response, (ProtoOAErrorRes, ProtoErrorRes))
        except ImportError:
            return False
