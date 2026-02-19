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
    
    async def get_categories(self) -> list[str]:
        """Get list of all symbol categories.
        
        Symbol categories group symbols by type (e.g., "Forex", "Commodities",
        "Indices", "Crypto", "Stocks").
        
        Returns:
            List of unique category names
            
        Example:
            >>> categories = await client.symbols.get_categories()
            >>> for category in categories:
            ...     print(f"Category: {category}")
        """
        try:
            from ..messages.OpenApiMessages_pb2 import (
                ProtoOASymbolCategoryListReq,
                ProtoOASymbolCategoryListRes,
            )
            
            # Build request
            req = ProtoOASymbolCategoryListReq()
            req.ctidTraderAccountId = self.config.account_id
            
            # Send request
            response = await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="SymbolCategoryList"
            )
            
            if not isinstance(response, ProtoOASymbolCategoryListRes):
                raise ValueError(f"Unexpected response type: {type(response)}")
            
            # Parse categories
            categories = []
            if hasattr(response, 'symbolCategory'):
                for cat in response.symbolCategory:
                    if hasattr(cat, 'name'):
                        categories.append(cat.name)
            
            logger.info(f"Retrieved {len(categories)} symbol categories")
            return categories
        
        except Exception as e:
            logger.error(f"Failed to get symbol categories: {e}", exc_info=True)
            # Fallback: extract from loaded symbols
            if self._loaded:
                async with self._lock:
                    categories = set()
                    for symbol in self._symbols_by_name.values():
                        if symbol.category_name:
                            categories.add(symbol.category_name)
                    return sorted(list(categories))
            return []
    
    async def get_symbols_by_category(self, category_name: str) -> list[Symbol]:
        """Get all symbols in a specific category.
        
        Args:
            category_name: Category name (e.g., "Forex", "Commodities")
            
        Returns:
            List of symbols in the category
            
        Example:
            >>> # Get all Forex symbols
            >>> forex_symbols = await client.symbols.get_symbols_by_category("Forex")
            >>> for symbol in forex_symbols:
            ...     print(f"{symbol.name}: {symbol.description}")
        """
        if not self._loaded:
            await self.load()
        
        category_name = category_name.strip()
        
        async with self._lock:
            return [
                symbol
                for symbol in self._symbols_by_name.values()
                if symbol.category_name and symbol.category_name.lower() == category_name.lower()
            ]
    
    async def get_symbol_details_by_id(self, symbol_id: int) -> Optional[Symbol]:
        """Fetch full symbol details from the server by ID.

        Unlike ``get_symbol_by_id()`` which uses the local cache only, this
        method issues a ``ProtoOASymbolByIdReq`` to get the complete and
        up-to-date symbol specification from the server, then updates the
        cache with the result.

        Args:
            symbol_id: Symbol identifier

        Returns:
            Symbol object with full details, or None if not found

        Example:
            >>> sym = await client.symbols.get_symbol_details_by_id(1)
            >>> print(f"{sym.name}: digits={sym.digits}, lot_size={sym.lot_size}")
        """
        try:
            from ..messages.OpenApiMessages_pb2 import (
                ProtoOASymbolByIdReq,
                ProtoOASymbolByIdRes,
            )

            req = ProtoOASymbolByIdReq()
            req.ctidTraderAccountId = self.config.account_id
            req.symbolId.append(int(symbol_id))

            response = await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="SymbolById",
            )

            if not isinstance(response, ProtoOASymbolByIdRes):
                raise ValueError(f"Unexpected response type: {type(response)}")

            symbols = list(getattr(response, "symbol", []) or [])
            if not symbols:
                return None

            symbol = self._parse_symbol(symbols[0])

            # Update the cache with the fresh data
            async with self._lock:
                self._symbols_by_id[symbol.id] = symbol
                if symbol.name:
                    self._symbols_by_name[symbol.name.upper()] = symbol

            return symbol

        except Exception as e:
            logger.error(f"Failed to get symbol details for id={symbol_id}: {e}", exc_info=True)
            raise

    async def get_conversion_symbols(self, first_asset_id: int, last_asset_id: int) -> list[Symbol]:
        """Get symbols usable for converting one asset into another.

        Uses ``ProtoOASymbolsForConversionReq`` and returns the matching
        light symbols from server response.

        Args:
            first_asset_id: Source asset identifier
            last_asset_id: Target asset identifier

        Returns:
            List of conversion-capable symbols (may be empty)

        Example:
            >>> syms = await client.symbols.get_conversion_symbols(1, 2)
            >>> print([s.name for s in syms])
        """
        try:
            from ..messages.OpenApiMessages_pb2 import ProtoOASymbolsForConversionReq

            req = ProtoOASymbolsForConversionReq()
            req.ctidTraderAccountId = self.config.account_id
            req.firstAssetId = int(first_asset_id)
            req.lastAssetId = int(last_asset_id)

            response = await self.protocol.send_request(
                req,
                timeout=self.config.request_timeout,
                request_type="SymbolsForConversion",
            )

            if not hasattr(response, "symbol"):
                raise ValueError(f"Unexpected response type: {type(response)}")

            output: list[Symbol] = []
            for symbol_data in getattr(response, "symbol", []) or []:
                output.append(self._parse_symbol(symbol_data))

            return output
        except Exception as e:
            logger.error(
                f"Failed to get conversion symbols ({first_asset_id} -> {last_asset_id}): {e}",
                exc_info=True,
            )
            raise

    def _parse_symbol(self, symbol_data: any) -> Symbol:
        """Parse symbol from protobuf data."""
        return Symbol(
            id=symbol_data.symbolId,
            name=getattr(symbol_data, 'symbolName', ''),
            digits=getattr(symbol_data, 'digits', 5),
            enabled=getattr(symbol_data, 'enabled', True),
            category_name=getattr(symbol_data, 'categoryName', None),
            base_asset_id=getattr(symbol_data, 'baseAssetId', None),
            quote_asset_id=getattr(symbol_data, 'quoteAssetId', None),
            description=getattr(symbol_data, 'description', None),
            pip_position=getattr(symbol_data, 'pipPosition', None),
            price_tick_size=(getattr(symbol_data, 'priceTickSize', 0) / 100000.0) if getattr(symbol_data, 'priceTickSize', 0) else None,
            lot_size=getattr(symbol_data, 'lotSize', 100000 * 100),
            min_volume=getattr(symbol_data, 'minVolume', None),
            max_volume=getattr(symbol_data, 'maxVolume', None),
            volume_step=getattr(symbol_data, 'volumeStep', None),
            enable_short_selling=getattr(symbol_data, 'enableShortSelling', None),
            guaranteed_stop_loss=getattr(symbol_data, 'guaranteedStopLoss', None),
            swap_long=getattr(symbol_data, 'swapLong', None),
            swap_short=getattr(symbol_data, 'swapShort', None),
            leverage_id=getattr(symbol_data, 'leverageId', None) or None,
        )
