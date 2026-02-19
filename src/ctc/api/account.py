"""
Account management API.
"""

from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum

from ..models import AccountInfo

if TYPE_CHECKING:
    from ..protocol import ProtocolHandler
    from ..config import ClientConfig

logger = logging.getLogger(__name__)


class CashFlowType(Enum):
    """Types of cash flow operations."""
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    DIVIDEND = "DIVIDEND"
    COMMISSION = "COMMISSION"
    SWAP = "SWAP"
    UNKNOWN = "UNKNOWN"


@dataclass
class CashFlowEntry:
    """Single cash flow entry (deposit, withdrawal, etc.).
    
    Attributes:
        entry_id: Entry identifier
        type: Cash flow type
        amount: Amount (positive for credits, negative for debits)
        balance_after: Account balance after this operation
        timestamp: Entry timestamp
        description: Description/notes
        money_digits: Decimal places for money values
    """
    entry_id: int
    type: CashFlowType
    amount: float
    balance_after: float
    timestamp: int
    description: Optional[str] = None
    money_digits: int = 2
    
    @property
    def datetime(self) -> datetime:
        """Get entry time as datetime."""
        return datetime.fromtimestamp(self.timestamp / 1000.0, tz=timezone.utc)
    
    @property
    def formatted_amount(self) -> str:
        """Get formatted amount with sign."""
        return f"{self.amount:+.{self.money_digits}f}"
    
    @property
    def is_credit(self) -> bool:
        """Check if this is a credit (positive amount)."""
        return self.amount > 0
    
    @property
    def is_debit(self) -> bool:
        """Check if this is a debit (negative amount)."""
        return self.amount < 0


@dataclass
class FullAccountInfo:
    """Complete account information including margin and risk metrics.
    
    This provides a comprehensive view of the trading account with all
    available financial and risk data.
    
    Attributes:
        account_id: Account identifier
        balance: Account balance
        equity: Account equity (balance + unrealized PnL)
        margin: Used margin
        free_margin: Free margin available for trading
        margin_level: Margin level percentage (equity / margin * 100)
        currency: Account currency
        account_type: Account type (HEDGED, NETTED, SPREAD_BETTING)
        leverage: Account leverage (e.g., 100.0 for 1:100)
        money_digits: Decimal places for money values
        # Additional fields
        unrealized_pnl: Total unrealized PnL across all positions
        realized_pnl: Realized PnL for the session
        swap: Total swap charges across all positions
        commission: Total commission charges
        timestamp: Last update timestamp
    """
    
    account_id: int
    balance: float
    equity: float
    margin: float
    free_margin: float
    currency: str
    account_type: str
    money_digits: int = 2
    margin_level: Optional[float] = None
    leverage: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    realized_pnl: Optional[float] = None
    swap: Optional[float] = None
    commission: Optional[float] = None
    timestamp: Optional[int] = None
    
    @property
    def last_update_datetime(self) -> Optional[datetime]:
        """Get last update time as datetime (UTC, timezone-aware)."""
        if self.timestamp:
            return datetime.fromtimestamp(self.timestamp / 1000.0, tz=timezone.utc)
        return None
    
    @property
    def formatted_balance(self) -> str:
        """Get formatted balance with proper decimals."""
        return f"{self.balance:.{self.money_digits}f}"
    
    @property
    def formatted_equity(self) -> str:
        """Get formatted equity with proper decimals."""
        return f"{self.equity:.{self.money_digits}f}"
    
    @property
    def formatted_margin(self) -> str:
        """Get formatted margin with proper decimals."""
        return f"{self.margin:.{self.money_digits}f}"
    
    @property
    def formatted_free_margin(self) -> str:
        """Get formatted free margin with proper decimals."""
        return f"{self.free_margin:.{self.money_digits}f}"
    
    @property
    def formatted_margin_level(self) -> str:
        """Get formatted margin level with % sign."""
        if self.margin_level is not None:
            return f"{self.margin_level:.2f}%"
        return "N/A"
    
    @property
    def margin_call_risk(self) -> str:
        """Get margin call risk assessment.
        
        Returns:
            "LOW" if margin level > 150%
            "MEDIUM" if margin level > 100% and <= 150%
            "HIGH" if margin level > 50% and <= 100%
            "CRITICAL" if margin level <= 50%
            "UNKNOWN" if margin level is None
        """
        if self.margin_level is None:
            return "UNKNOWN"
        if self.margin_level > 150:
            return "LOW"
        elif self.margin_level > 100:
            return "MEDIUM"
        elif self.margin_level > 50:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def __repr__(self) -> str:
        return (
            f"<FullAccountInfo "
            f"balance={self.formatted_balance} {self.currency}, "
            f"equity={self.formatted_equity}, "
            f"margin={self.formatted_margin}, "
            f"free_margin={self.formatted_free_margin}, "
            f"margin_level={self.formatted_margin_level}>"
        )


class AccountAPI:
    """High-level API for account operations.
    
    Example:
        >>> account_api = AccountAPI(protocol, config)
        >>> info = await account_api.get_info()
        >>> print(f"Balance: {info.balance}, Equity: {info.equity}")
    """
    
    def __init__(self, protocol: ProtocolHandler, config: ClientConfig, client=None):
        """Initialize account API.
        
        Args:
            protocol: Protocol handler
            config: Client configuration
            client: Parent client instance (optional, for accessing trading data)
        """
        self.protocol = protocol
        self.config = config
        self._client = client
        self._cached_info: Optional[AccountInfo] = None
        self._cached_full_info: Optional[FullAccountInfo] = None
        self.hooks = None
    
    async def get_info(self, *, refresh: bool = False) -> AccountInfo:
        """Get account information.
        
        Args:
            refresh: Force refresh from server
            
        Returns:
            Account information
        """
        if not refresh and self._cached_info:
            return self._cached_info
        
        try:
            from ..messages.OpenApiMessages_pb2 import ProtoOATraderReq
            
            req = ProtoOATraderReq()
            req.ctidTraderAccountId = self.config.account_id
            
            response = await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="Trader"
            )
            
            if hasattr(response, 'trader'):
                trader = response.trader
                money_digits = getattr(trader, 'moneyDigits', 2)
                divisor = 10 ** money_digits
                
                # Account type (HEDGED / NETTED / SPREAD_BETTING) if available
                account_type = None
                try:
                    from ..messages.OpenApiModelMessages_pb2 import ProtoOAAccountType

                    if hasattr(trader, "accountType"):
                        account_type = ProtoOAAccountType.Name(int(getattr(trader, "accountType")))
                except Exception:
                    account_type = None

                self._cached_info = AccountInfo(
                    account_id=self.config.account_id,
                    balance=trader.balance / divisor,
                    equity=trader.balance / divisor,  # Will be updated with PnL
                    margin=0.0,
                    free_margin=trader.balance / divisor,
                    money_digits=money_digits,
                    account_type=account_type,
                )
                
                return self._cached_info
            
            raise ValueError("No trader data in response")
        
        except Exception as e:
            logger.error(f"Failed to get account info: {e}", exc_info=True)
            raise
    
    async def get_full_account_info(self, *, refresh: bool = False) -> FullAccountInfo:
        """Get complete account information with margin and risk metrics.
        
        This method fetches comprehensive account data including:
        - Basic account info (balance, equity, margin, free margin)
        - Margin level percentage
        - Leverage information
        - Unrealized PnL across all positions
        - Swap and commission totals
        
        Args:
            refresh: Force refresh from server
            
        Returns:
            FullAccountInfo with complete account details
            
        Example:
            >>> info = await client.account.get_full_account_info()
            >>> print(f"Balance: {info.formatted_balance}")
            >>> print(f"Margin Level: {info.formatted_margin_level}")
            >>> print(f"Risk Level: {info.margin_call_risk}")
        """
        if not refresh and self._cached_full_info:
            return self._cached_full_info
        
        try:
            from ..messages.OpenApiMessages_pb2 import ProtoOATraderReq
            
            req = ProtoOATraderReq()
            req.ctidTraderAccountId = self.config.account_id
            
            response = await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="Trader"
            )
            
            if not hasattr(response, 'trader'):
                raise ValueError("No trader data in response")
            
            trader = response.trader
            money_digits = getattr(trader, 'moneyDigits', 2)
            divisor = 10 ** money_digits
            
            # Account type
            account_type = "UNKNOWN"
            try:
                from ..messages.OpenApiModelMessages_pb2 import ProtoOAAccountType
                if hasattr(trader, "accountType"):
                    account_type = ProtoOAAccountType.Name(int(getattr(trader, "accountType")))
            except Exception:
                pass
            
            # Currency (deposit asset)
            currency = "USD"  # Default
            try:
                if hasattr(trader, 'depositAssetId'):
                    # Try to resolve currency from asset catalog if available
                    if self._client and hasattr(self._client, 'assets'):
                        asset = await self._client.assets.get_asset_by_id(trader.depositAssetId)
                        if asset:
                            currency = asset.name
            except Exception:
                pass
            
            # Get position data to calculate totals
            total_unrealized_pnl = 0.0
            total_swap = 0.0
            total_commission = 0.0
            total_margin = 0.0
            
            try:
                if self._client and hasattr(self._client, 'trading'):
                    positions = await self._client.trading.get_positions()
                    for pos in positions:
                        total_unrealized_pnl += getattr(pos, 'pnl_net_unrealized', 0.0)
                        total_swap += getattr(pos, 'swap', 0.0)
                        total_commission += getattr(pos, 'commission', 0.0)
            except Exception as e:
                logger.debug(f"Could not fetch position data: {e}")
            
            # Calculate equity and margin metrics
            balance = trader.balance / divisor
            equity = balance + total_unrealized_pnl
            
            # Get used margin from trader data if available, otherwise estimate
            if hasattr(trader, 'marginUsed'):
                total_margin = trader.marginUsed / divisor
            
            # Calculate free margin
            free_margin = equity - total_margin
            
            # Calculate margin level
            margin_level = None
            if total_margin > 0:
                margin_level = (equity / total_margin) * 100.0
            
            # Leverage
            leverage = None
            if hasattr(trader, 'leverageInCents'):
                leverage = trader.leverageInCents / 100.0
            elif hasattr(trader, 'leverage'):
                leverage = float(trader.leverage)
            
            self._cached_full_info = FullAccountInfo(
                account_id=self.config.account_id,
                balance=balance,
                equity=equity,
                margin=total_margin,
                free_margin=free_margin,
                margin_level=margin_level,
                currency=currency,
                account_type=account_type,
                leverage=leverage,
                money_digits=money_digits,
                unrealized_pnl=total_unrealized_pnl,
                swap=total_swap,
                commission=total_commission,
                timestamp=int(datetime.now(timezone.utc).timestamp() * 1000)
            )
            
            return self._cached_full_info
            
        except Exception as e:
            logger.error(f"Failed to get full account info: {e}", exc_info=True)
            raise
    
    async def refresh_cache(self) -> None:
        """Refresh all cached account information.
        
        This fetches fresh data from the server and updates both
        the basic and full account info caches.
        """
        self._cached_info = None
        self._cached_full_info = None
        await self.get_info(refresh=True)
        await self.get_full_account_info(refresh=True)
        logger.debug("Account cache refreshed")
    
    async def get_margin_status(self) -> dict:
        """Get a quick margin status summary.
        
        Returns:
            Dict with margin status information:
            {
                'margin_level': float or None,
                'free_margin': float,
                'used_margin': float,
                'equity': float,
                'margin_call_risk': str,
                'can_trade': bool
            }
        """
        info = await self.get_full_account_info()
        
        # Determine if account can trade
        can_trade = info.free_margin > 0 and (info.margin_level is None or info.margin_level > 100)
        
        return {
            'margin_level': info.margin_level,
            'free_margin': info.free_margin,
            'used_margin': info.margin,
            'equity': info.equity,
            'margin_call_risk': info.margin_call_risk,
            'can_trade': can_trade
        }
    
    async def get_cash_flow_history(
        self,
        from_timestamp: Optional[int] = None,
        to_timestamp: Optional[int] = None,
        days: Optional[int] = None,
        max_rows: int = 1000
    ) -> list[CashFlowEntry]:
        """Get cash flow history (deposits, withdrawals, dividends).
        
        Retrieves the history of money movements in the account including
        deposits, withdrawals, dividends, and other cash operations.
        
        Args:
            from_timestamp: Start time in milliseconds (optional)
            to_timestamp: End time in milliseconds (optional)
            days: Get entries from last N days (alternative to timestamps)
            max_rows: Maximum number of entries to return (default: 1000)
            
        Returns:
            List of CashFlowEntry objects
            
        Example:
            >>> # Get cash flow from last 30 days
            >>> entries = await client.account.get_cash_flow_history(days=30)
            >>> for entry in entries:
            ...     print(f"{entry.datetime}: {entry.type.value} {entry.formatted_amount}")
            >>> 
            >>> # Calculate total deposits
            >>> deposits = [e for e in entries if e.type == CashFlowType.DEPOSIT]
            >>> total_deposits = sum(e.amount for e in deposits)
        """
        from ..messages.OpenApiMessages_pb2 import (
            ProtoOACashFlowHistoryListReq,
            ProtoOACashFlowHistoryListRes,
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
        req = ProtoOACashFlowHistoryListReq()
        req.ctidTraderAccountId = self.config.account_id
        req.fromTimestamp = from_timestamp
        req.toTimestamp = to_timestamp
        
        entries = []
        has_more = True
        
        # Pagination loop
        while has_more and len(entries) < max_rows:
            req.maxRows = min(100, max_rows - len(entries))  # Request in chunks
            
            # Send request
            response = await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="CashFlowHistoryList"
            )
            
            if not isinstance(response, ProtoOACashFlowHistoryListRes):
                raise ValueError(f"Unexpected response type: {type(response)}")
            
            # Parse response
            money_digits = getattr(response, 'moneyDigits', 2)
            divisor = 10 ** money_digits
            
            if hasattr(response, 'depositWithdraw'):
                for entry_proto in response.depositWithdraw:
                    entry_id = getattr(entry_proto, 'depositWithdrawId', 0)
                    
                    # Determine type from changeBalanceType
                    change_type = getattr(entry_proto, 'changeBalanceType', None)
                    cf_type = CashFlowType.UNKNOWN
                    if change_type:
                        type_name = str(change_type)
                        if 'DEPOSIT' in type_name:
                            cf_type = CashFlowType.DEPOSIT
                        elif 'WITHDRAWAL' in type_name:
                            cf_type = CashFlowType.WITHDRAWAL
                        elif 'DIVIDEND' in type_name:
                            cf_type = CashFlowType.DIVIDEND
                        elif 'COMMISSION' in type_name:
                            cf_type = CashFlowType.COMMISSION
                        elif 'SWAP' in type_name:
                            cf_type = CashFlowType.SWAP
                    
                    # Parse amounts
                    amount = getattr(entry_proto, 'amount', 0) / divisor
                    balance_after = getattr(entry_proto, 'balance', 0) / divisor
                    timestamp = getattr(entry_proto, 'createTimestamp', 0)
                    description = getattr(entry_proto, 'description', None)
                    
                    entries.append(CashFlowEntry(
                        entry_id=entry_id,
                        type=cf_type,
                        amount=amount,
                        balance_after=balance_after,
                        timestamp=timestamp,
                        description=description,
                        money_digits=money_digits
                    ))
            
            # Check for more data
            has_more = getattr(response, 'hasMore', False)
            if has_more and entries:
                # Update fromTimestamp to get next page
                last_entry = entries[-1]
                req.fromTimestamp = last_entry.timestamp + 1
        
        logger.info(f"Retrieved {len(entries)} cash flow entries")
        return entries[:max_rows]
