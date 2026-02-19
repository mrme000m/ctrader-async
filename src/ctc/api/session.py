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
    
    async def refresh_token(self, refresh_token: str) -> dict:
        """Refresh an expired OAuth access token via the protobuf API.

        Uses ``ProtoOARefreshTokenReq`` to obtain a new access token without
        going through the full OAuth redirect flow. Important for long-running
        bots where the initial access token expires.

        Args:
            refresh_token: The OAuth refresh token received during initial auth

        Returns:
            Dict with keys: ``access_token``, ``refresh_token``,
            ``expires_in``, ``token_type``

        Example:
            >>> tokens = await client.session.refresh_token(my_refresh_token)
            >>> # Update client config with new token
            >>> client.config.access_token = tokens['access_token']
        """
        from ..messages.OpenApiMessages_pb2 import (
            ProtoOARefreshTokenReq,
            ProtoOARefreshTokenRes,
        )

        req = ProtoOARefreshTokenReq()
        req.refreshToken = refresh_token

        response = await self.protocol.send_request(
            req,
            timeout=self.config.request_timeout,
            request_type="RefreshToken",
        )

        if not isinstance(response, ProtoOARefreshTokenRes):
            raise ValueError(f"Unexpected response type: {type(response)}")

        result = {
            "access_token": getattr(response, "accessToken", ""),
            "refresh_token": getattr(response, "refreshToken", ""),
            "expires_in": getattr(response, "expiresIn", 0),
            "token_type": getattr(response, "tokenType", "Bearer"),
        }

        logger.info("Access token refreshed successfully")
        return result

    async def get_ctid_profile(self) -> dict:
        """Get the cTID user profile for the current access token.

        Uses ``ProtoOAGetCtidProfileByTokenReq`` to retrieve user identity
        information associated with the OAuth access token. Useful for
        multi-user applications to identify which cTID account is connected.

        Returns:
            Dict with keys: ``user_id``, ``nickname``, ``email``,
            ``first_name``, ``last_name``, ``phone``, ``gender``,
            ``preferred_lang``, ``utm_source``

        Example:
            >>> profile = await client.session.get_ctid_profile()
            >>> print(f"Connected as: {profile['nickname']} ({profile['email']})")
        """
        from ..messages.OpenApiMessages_pb2 import (
            ProtoOAGetCtidProfileByTokenReq,
            ProtoOAGetCtidProfileByTokenRes,
        )

        req = ProtoOAGetCtidProfileByTokenReq()
        req.accessToken = self.config.access_token

        response = await self.protocol.send_request(
            req,
            timeout=self.config.request_timeout,
            request_type="GetCtidProfileByToken",
        )

        if not isinstance(response, ProtoOAGetCtidProfileByTokenRes):
            raise ValueError(f"Unexpected response type: {type(response)}")

        profile_proto = getattr(response, "profile", None)
        if profile_proto is None:
            raise ValueError("No profile in response")

        result = {
            "user_id": getattr(profile_proto, "userId", None),
            "nickname": getattr(profile_proto, "nickname", ""),
            "email": getattr(profile_proto, "email", ""),
            "first_name": getattr(profile_proto, "firstName", ""),
            "last_name": getattr(profile_proto, "lastName", ""),
            "phone": getattr(profile_proto, "phone", ""),
            "gender": getattr(profile_proto, "gender", ""),
            "preferred_lang": getattr(profile_proto, "preferredLang", ""),
            "utm_source": getattr(profile_proto, "utmSource", ""),
        }

        logger.info(f"Retrieved cTID profile for user_id={result['user_id']}")
        return result

    async def get_server_version(self) -> str:
        """Get the cTrader Open API server version.
        
        Returns:
            Server version string (e.g., "168")
            
        Example:
            >>> version = await client.session.get_server_version()
            >>> print(f"Server version: {version}")
        """
        from ..messages.OpenApiMessages_pb2 import (
            ProtoOAVersionReq,
            ProtoOAVersionRes,
        )
        
        # Build request
        req = ProtoOAVersionReq()
        
        # Send request
        response = await self.protocol.send_request(
            req,
            timeout=self.config.request_timeout,
            request_type="Version"
        )
        
        if not isinstance(response, ProtoOAVersionRes):
            raise ValueError(f"Unexpected response type: {type(response)}")
        
        version = getattr(response, 'version', 'unknown')
        logger.info(f"Server version: {version}")
        return version
