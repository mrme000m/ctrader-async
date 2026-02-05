"""
Account management API.
"""

from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING

from ..models import AccountInfo

if TYPE_CHECKING:
    from ..protocol import ProtocolHandler
    from ..config import ClientConfig

logger = logging.getLogger(__name__)


class AccountAPI:
    """High-level API for account operations.
    
    Example:
        >>> account_api = AccountAPI(protocol, config)
        >>> info = await account_api.get_info()
        >>> print(f"Balance: {info.balance}, Equity: {info.equity}")
    """
    
    def __init__(self, protocol: ProtocolHandler, config: ClientConfig):
        """Initialize account API.
        
        Args:
            protocol: Protocol handler
            config: Client configuration
        """
        self.protocol = protocol
        self.config = config
        self._cached_info: Optional[AccountInfo] = None
    
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
                
                self._cached_info = AccountInfo(
                    account_id=self.config.account_id,
                    balance=trader.balance / divisor,
                    equity=trader.balance / divisor,  # Will be updated with PnL
                    margin=0.0,
                    free_margin=trader.balance / divisor,
                    money_digits=money_digits,
                )
                
                return self._cached_info
            
            raise ValueError("No trader data in response")
        
        except Exception as e:
            logger.error(f"Failed to get account info: {e}", exc_info=True)
            raise
