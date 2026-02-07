"""
Session Management API.

Provides methods for:
- Account discovery
- Multi-account support
- Session logout
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional
from dataclasses import dataclass

if TYPE_CHECKING:
    from ..protocol import ProtocolHandler
    from ..config import ClientConfig

logger = logging.getLogger(__name__)


@dataclass
class AccountSummary:
    """Summary of a trading account.
    
    Attributes:
        account_id: Account identifier
        account_type: Account type (e.g., "LIVE", "DEMO")
        broker_name: Broker name
        is_live: Whether this is a live account
        currency: Account currency
    """
    
    account_id: int
    account_type: str
    broker_name: str = ""
    is_live: bool = False
    currency: str = ""


class SessionAPI:
    """Session management API.
    
    Provides methods for managing authentication sessions,
    discovering accounts, and handling multi-account scenarios.
    
    Example:
        >>> # Get all accounts accessible with current token
        >>> accounts = await client.session.get_available_accounts()
        >>> for account in accounts:
        ...     print(f"Account {account.account_id}: {account.account_type}")
        >>> 
        >>> # Logout from current account
        >>> await client.session.logout()
    """
    
    def __init__(
        self,
        protocol: ProtocolHandler,
        config: ClientConfig,
        client=None
    ):
        """Initialize Session API.
        
        Args:
            protocol: Protocol handler
            config: Client configuration
            client: Parent client instance (optional)
        """
        self.protocol = protocol
        self.config = config
        self._client = client
    
    async def get_available_accounts(self) -> list[AccountSummary]:
        """Get list of accounts accessible with current access token.
        
        Useful for multi-account applications where a single token
        can access multiple trading accounts.
        
        Returns:
            List of AccountSummary objects
            
        Example:
            >>> accounts = await client.session.get_available_accounts()
            >>> for account in accounts:
            ...     print(f"Account {account.account_id}: {account.account_type}")
            ...     print(f"  Broker: {account.broker_name}")
            ...     print(f"  Is Live: {account.is_live}")
        """
        from ..messages.OpenApiMessages_pb2 import (
            ProtoOAGetAccountListByAccessTokenReq,
            ProtoOAGetAccountListByAccessTokenRes,
        )
        
        # Build request
        req = ProtoOAGetAccountListByAccessTokenReq()
        req.accessToken = self.config.access_token
        
        # Send request
        response = await self.protocol.send_request(
            req,
            timeout=self.config.request_timeout,
            request_type="GetAccountListByAccessToken"
        )
        
        if not isinstance(response, ProtoOAGetAccountListByAccessTokenRes):
            raise ValueError(f"Unexpected response type: {type(response)}")
        
        # Parse accounts
        accounts = []
        
        if hasattr(response, 'ctidTraderAccount'):
            for account_proto in response.ctidTraderAccount:
                account_id = getattr(account_proto, 'ctidTraderAccountId', None)
                if account_id is None:
                    continue
                
                # Determine account type
                is_live = getattr(account_proto, 'isLive', False)
                account_type = "LIVE" if is_live else "DEMO"
                
                # Get broker name if available
                broker_name = getattr(account_proto, 'brokerName', '')
                
                # Get currency if available
                # Note: Currency might not be in account list response
                # Would need separate account info call to get it
                
                accounts.append(AccountSummary(
                    account_id=account_id,
                    account_type=account_type,
                    broker_name=broker_name,
                    is_live=is_live,
                    currency=""  # Would need separate call
                ))
        
        logger.info(f"Retrieved {len(accounts)} accounts")
        return accounts
    
    async def logout(self) -> None:
        """Logout from the current trading account.
        
        Explicitly ends the account session. The connection will remain
        open but account-specific operations will no longer work.
        
        Example:
            >>> await client.session.logout()
            >>> print("Logged out successfully")
        """
        from ..messages.OpenApiMessages_pb2 import (
            ProtoOAAccountLogoutReq,
            ProtoOAAccountLogoutRes,
        )
        
        # Build request
        req = ProtoOAAccountLogoutReq()
        req.ctidTraderAccountId = self.config.account_id
        
        # Send request
        response = await self.protocol.send_request(
            req,
            timeout=self.config.request_timeout,
            request_type="AccountLogout"
        )
        
        if not isinstance(response, ProtoOAAccountLogoutRes):
            raise ValueError(f"Unexpected response type: {type(response)}")
        
        logger.info(f"Logged out from account {self.config.account_id}")
    
    async def switch_account(self, account_id: int) -> bool:
        """Switch to a different trading account.
        
        Note: This requires reconnecting with the new account ID.
        For proper account switching, create a new client instance.
        
        Args:
            account_id: New account ID to switch to
            
        Returns:
            True if switch initiated successfully
            
        Example:
            >>> # Get available accounts
            >>> accounts = await client.session.get_available_accounts()
            >>> 
            >>> # To properly switch accounts, create new client
            >>> new_client = CTraderClient(
            ...     client_id=client_id,
            ...     client_secret=client_secret,
            ...     access_token=access_token,
            ...     account_id=accounts[1].account_id,  # Different account
            ...     host_type="demo"
            ... )
        """
        # Account switching requires full reconnect
        # This is more of a helper/documentation method
        logger.warning(
            f"Account switching requires creating a new client instance. "
            f"Current account: {self.config.account_id}, Target: {account_id}"
        )
        
        if self._client is None:
            raise RuntimeError("Session API not attached to client")
        
        # Update config for future reconnects
        self.config.account_id = account_id
        
        # Note: Actual reconnect logic would need to be triggered
        # For now, we just update the config
        return True
