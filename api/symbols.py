"""
Symbol catalog management.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, Dict, TYPE_CHECKING

from ..models import Symbol
from ..utils.errors import SymbolNotFoundError

if TYPE_CHECKING:
    from ..protocol import ProtocolHandler
    from ..config import ClientConfig

logger = logging.getLogger(__name__)


class SymbolCatalog:
    """Manage trading symbols catalog.
    
    Provides access to symbol information with caching.
    
    Example:
        >>> catalog = SymbolCatalog(protocol, config)
        >>> await catalog.load()
        >>> symbol = await catalog.get_symbol("EURUSD")
        >>> print(f"EURUSD digits: {symbol.digits}")
    """
    
    def __init__(self, protocol: ProtocolHandler, config: ClientConfig):
        """Initialize symbol catalog.
        
        Args:
            protocol: Protocol handler
            config: Client configuration
        """
        self.protocol = protocol
        self.config = config
        
        self._symbols_by_name: Dict[str, Symbol] = {}
        self._symbols_by_id: Dict[int, Symbol] = {}
        self._lock = asyncio.Lock()
        self._loaded = False
    
    async def load(self):
        """Load all symbols from server."""
        try:
            from ..messages.OpenApiMessages_pb2 import ProtoOASymbolsListReq
            
            req = ProtoOASymbolsListReq()
            req.ctidTraderAccountId = self.config.account_id
            
            response = await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="SymbolsList"
            )
            
            async with self._lock:
                self._symbols_by_name.clear()
                self._symbols_by_id.clear()
                
                for symbol_data in getattr(response, 'symbol', []):
                    symbol = self._parse_symbol(symbol_data)
                    self._symbols_by_name[symbol.name.upper()] = symbol
                    self._symbols_by_id[symbol.id] = symbol
                
                self._loaded = True
            
            logger.info(f"Loaded {len(self._symbols_by_name)} symbols")
        
        except Exception as e:
            logger.error(f"Failed to load symbols: {e}", exc_info=True)
            raise
    
    async def get_symbol(self, symbol_name: str) -> Optional[Symbol]:
        """Get symbol by name.
        
        Args:
            symbol_name: Symbol name (e.g., "EURUSD")
            
        Returns:
            Symbol object or None if not found
        """
        if not self._loaded:
            await self.load()
        
        async with self._lock:
            return self._symbols_by_name.get(symbol_name.upper())
    
    async def get_symbol_by_id(self, symbol_id: int) -> Optional[Symbol]:
        """Get symbol by ID.
        
        Args:
            symbol_id: Symbol ID
            
        Returns:
            Symbol object or None if not found
        """
        if not self._loaded:
            await self.load()
        
        async with self._lock:
            return self._symbols_by_id.get(symbol_id)
    
    async def get_symbol_name(self, symbol_id: int) -> Optional[str]:
        """Get symbol name by ID.
        
        Args:
            symbol_id: Symbol ID
            
        Returns:
            Symbol name or None if not found
        """
        symbol = await self.get_symbol_by_id(symbol_id)
        return symbol.name if symbol else None
    
    async def get_all(self) -> list[Symbol]:
        """Get all symbols.
        
        Returns:
            List of all symbols
        """
        if not self._loaded:
            await self.load()
        
        async with self._lock:
            return list(self._symbols_by_name.values())
    
    async def search(self, pattern: str) -> list[Symbol]:
        """Search symbols by pattern.
        
        Args:
            pattern: Search pattern (case-insensitive)
            
        Returns:
            List of matching symbols
        """
        if not self._loaded:
            await self.load()
        
        pattern = pattern.strip().upper()

        async with self._lock:
            return [
                symbol
                for symbol in self._symbols_by_name.values()
                if pattern and pattern in symbol.name.upper()
            ]
    
    def _parse_symbol(self, symbol_data: any) -> Symbol:
        """Parse symbol from protobuf data."""
        return Symbol(
            id=symbol_data.symbolId,
            name=getattr(symbol_data, 'symbolName', ''),
            digits=getattr(symbol_data, 'digits', 5),
            enabled=getattr(symbol_data, 'enabled', True),
            pip_position=getattr(symbol_data, 'pipPosition', None),
            lot_size=getattr(symbol_data, 'lotSize', 100000 * 100),
            min_volume=getattr(symbol_data, 'minVolume', None),
            max_volume=getattr(symbol_data, 'maxVolume', None),
            volume_step=getattr(symbol_data, 'volumeStep', None),
        )
