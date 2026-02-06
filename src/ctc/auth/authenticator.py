"""
Clean async authentication state machine for cTrader.
"""

from __future__ import annotations

import asyncio
import logging
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from ..utils.errors import AuthenticationError

if TYPE_CHECKING:
    from ..protocol import ProtocolHandler
    from ..config import ClientConfig

logger = logging.getLogger(__name__)


class AuthPhase(Enum):
    """Authentication phases.
    
    Attributes:
        DISCONNECTED: Not connected
        APPLICATION_AUTH: Authenticating application
        ACCOUNT_AUTH: Authenticating account
        AUTHENTICATED: Fully authenticated
        FAILED: Authentication failed
    """
    
    DISCONNECTED = auto()
    APPLICATION_AUTH = auto()
    ACCOUNT_AUTH = auto()
    AUTHENTICATED = auto()
    FAILED = auto()
    
    def __str__(self) -> str:
        return self.name


@dataclass
class AuthState:
    """Current authentication state.
    
    Attributes:
        phase: Current authentication phase
        attempts: Number of authentication attempts
        error: Last error message (if any)
        error_code: Last error code (if any)
    """
    
    phase: AuthPhase = AuthPhase.DISCONNECTED
    attempts: int = 0
    error: Optional[str] = None
    error_code: Optional[str] = None
    
    @property
    def is_authenticated(self) -> bool:
        """Check if fully authenticated."""
        return self.phase == AuthPhase.AUTHENTICATED
    
    @property
    def is_failed(self) -> bool:
        """Check if authentication failed."""
        return self.phase == AuthPhase.FAILED


class Authenticator:
    """Clean async authentication state machine.
    
    Handles the two-phase cTrader authentication:
    1. Application authentication (OAuth client credentials)
    2. Account authentication (access token + account ID)
    
    Example:
        >>> authenticator = Authenticator(config, protocol_handler)
        >>> success = await authenticator.authenticate()
        >>> if success:
        ...     print("Authenticated successfully")
    """
    
    def __init__(self, config: ClientConfig, protocol: ProtocolHandler):
        """Initialize authenticator.
        
        Args:
            config: Client configuration
            protocol: Protocol handler for sending requests
        """
        self.config = config
        self.protocol = protocol
        self.state = AuthState()
    
    async def authenticate(self, *, max_attempts: int = 3) -> bool:
        """Run full authentication flow with retries.
        
        Args:
            max_attempts: Maximum number of authentication attempts
            
        Returns:
            True if authenticated successfully, False otherwise
            
        Raises:
            AuthenticationError: If authentication fails after all attempts
        """
        self.state.phase = AuthPhase.APPLICATION_AUTH
        self.state.attempts = 0
        self.state.error = None
        self.state.error_code = None
        
        while self.state.attempts < max_attempts:
            try:
                # Phase 1: Application authentication
                logger.info(f"Authenticating application (attempt {self.state.attempts + 1}/{max_attempts})...")
                
                if not await self._authenticate_application():
                    self.state.attempts += 1
                    if self.state.attempts < max_attempts:
                        delay = 2 ** self.state.attempts  # Exponential backoff
                        logger.warning(f"Application auth failed, retrying in {delay}s...")
                        await asyncio.sleep(delay)
                    continue
                
                logger.info("Application authenticated successfully")
                
                # Phase 2: Account authentication
                self.state.phase = AuthPhase.ACCOUNT_AUTH
                logger.info("Authenticating account...")
                
                if not await self._authenticate_account():
                    self.state.attempts += 1
                    if self.state.attempts < max_attempts:
                        delay = 2 ** self.state.attempts
                        logger.warning(f"Account auth failed, retrying in {delay}s...")
                        await asyncio.sleep(delay)
                    continue
                
                # Success!
                self.state.phase = AuthPhase.AUTHENTICATED
                self.state.attempts = 0
                logger.info("Account authenticated successfully")
                return True
            
            except Exception as e:
                self.state.error = str(e)
                self.state.attempts += 1
                logger.error(f"Authentication error: {e}")
                
                if self.state.attempts >= max_attempts:
                    break
                
                delay = 2 ** self.state.attempts
                await asyncio.sleep(delay)
        
        # Authentication failed
        self.state.phase = AuthPhase.FAILED
        
        error_msg = (
            f"Authentication failed after {self.state.attempts} attempts"
            f"{': ' + self.state.error if self.state.error else ''}"
        )
        
        raise AuthenticationError(
            error_msg,
            code=self.state.error_code,
            attempts=self.state.attempts
        )
    
    async def _authenticate_application(self) -> bool:
        """Perform application authentication.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            from ..messages.OpenApiMessages_pb2 import (
                ProtoOAApplicationAuthReq,
                ProtoOAApplicationAuthRes,
            )
            
            req = ProtoOAApplicationAuthReq()
            req.clientId = self.config.client_id
            req.clientSecret = self.config.client_secret
            
            # Send request and wait for response
            response = await self.protocol.send_request(
                req,
                timeout=self.config.auth_timeout,
                request_type="ApplicationAuth"
            )
            
            # Check if response is an error
            if self._is_error_response(response):
                self.state.error = self._get_error_description(response)
                self.state.error_code = self._get_error_code(response)

                # Some servers respond with an error when the application is already authorized.
                # Treat that as a success so repeated connects work.
                if (self.state.error and "already authorized" in self.state.error.lower()):
                    logger.info("Application already authorized; continuing")
                    return True

                logger.error(f"Application auth error: {self.state.error}")
                return False
            
            # Success if we got a valid response
            if isinstance(response, ProtoOAApplicationAuthRes):
                return True
            
            # Treat any other response as success (some servers may not send explicit response)
            return True
        
        except asyncio.TimeoutError:
            self.state.error = "Application authentication timeout"
            logger.error(self.state.error)
            return False
        
        except Exception as e:
            self.state.error = f"Application authentication failed: {e}"
            logger.error(self.state.error, exc_info=True)
            return False
    
    async def _authenticate_account(self) -> bool:
        """Perform account authentication.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            from ..messages.OpenApiMessages_pb2 import (
                ProtoOAAccountAuthReq,
                ProtoOAAccountAuthRes,
            )
            
            req = ProtoOAAccountAuthReq()
            req.ctidTraderAccountId = self.config.account_id
            req.accessToken = self.config.access_token
            
            # Send request and wait for response
            response = await self.protocol.send_request(
                req,
                timeout=self.config.auth_timeout,
                request_type="AccountAuth"
            )
            
            # Check if response is an error
            if self._is_error_response(response):
                self.state.error = self._get_error_description(response)
                self.state.error_code = self._get_error_code(response)
                logger.error(f"Account auth error: {self.state.error}")
                return False
            
            # Success if we got a valid response
            if isinstance(response, ProtoOAAccountAuthRes):
                return True
            
            return True
        
        except asyncio.TimeoutError:
            self.state.error = "Account authentication timeout"
            logger.error(self.state.error)
            return False
        
        except Exception as e:
            self.state.error = f"Account authentication failed: {e}"
            logger.error(self.state.error, exc_info=True)
            return False
    
    @staticmethod
    def _is_error_response(response: any) -> bool:
        """Check if response is an error.
        
        Args:
            response: Response message
            
        Returns:
            True if error response, False otherwise
        """
        try:
            from ..messages.OpenApiMessages_pb2 import ProtoOAErrorRes
            from ..messages.OpenApiCommonMessages_pb2 import ProtoErrorRes
            
            return isinstance(response, (ProtoOAErrorRes, ProtoErrorRes))
        except ImportError:
            return False
    
    @staticmethod
    def _get_error_code(response: any) -> Optional[str]:
        """Extract error code from error response.
        
        Args:
            response: Error response message
            
        Returns:
            Error code or None
        """
        return getattr(response, 'errorCode', None)
    
    @staticmethod
    def _get_error_description(response: any) -> Optional[str]:
        """Extract error description from error response.
        
        Args:
            response: Error response message
            
        Returns:
            Error description or None
        """
        return getattr(response, 'description', None) or str(getattr(response, 'errorCode', 'Unknown error'))
    
    def reset(self):
        """Reset authentication state."""
        self.state = AuthState()
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<Authenticator phase={self.state.phase}, attempts={self.state.attempts}>"
