"""Fuzzy symbol resolution utilities.

Provides functions for resolving symbols with suffixes, aliases, and partial matches.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..api.symbols import SymbolCatalog
    from ..models import Symbol

logger = logging.getLogger(__name__)


async def resolve_symbol(
    catalog: "SymbolCatalog",
    name: str,
    *,
    suffixes: list[str] = None,
    aliases: dict[str, list[str]] = None,
) -> Optional["Symbol"]:
    """Resolve a symbol name with fuzzy matching.
    
    Tries direct match first, then suffix variants, then alias expansion.
    This handles broker-specific symbol naming (e.g., XAUUSD.m, EURUSD.cash).
    
    Args:
        catalog: Symbol catalog to search
        name: Symbol name to resolve
        suffixes: List of suffixes to try (default: [".m", ".cash", ".raw", ".p", ".ecn"])
        aliases: Optional dict of aliases (e.g., {"GOLD": ["XAUUSD"], "SILVER": ["XAGUSD"]})
        
    Returns:
        Resolved Symbol or None if not found
        
    Example:
        >>> # Try to find XAUUSD with various suffixes
        >>> symbol = await resolve_symbol(
        ...     catalog=client.symbols,
        ...     name="XAUUSD",
        ...     suffixes=[".m", ".cash", ""]
        ... )
        >>> 
        >>> # Use aliases for common names
        >>> symbol = await resolve_symbol(
        ...     catalog=client.symbols,
        ...     name="GOLD",
        ...     aliases={"GOLD": ["XAUUSD", "GOLD"], "SILVER": ["XAGUSD"]}
        ... )
    """
    if suffixes is None:
        suffixes = [".m", ".cash", ".raw", ".p", ".ecn", "", "_m", "_cash", "_raw"]
    
    name_upper = name.upper().strip()
    
    # 1. Try direct match
    symbol = await catalog.get_symbol(name_upper)
    if symbol:
        return symbol
    
    # 2. Try alias expansion
    if aliases:
        aliases_upper = {k.upper(): [v.upper() for v in vals] for k, vals in aliases.items()}
        if name_upper in aliases_upper:
            for alias in aliases_upper[name_upper]:
                symbol = await catalog.get_symbol(alias)
                if symbol:
                    logger.debug(f"Resolved {name} via alias to {alias}")
                    return symbol
    
    # 3. Try with suffixes
    for suffix in suffixes:
        variant = name_upper + suffix
        symbol = await catalog.get_symbol(variant)
        if symbol:
            logger.debug(f"Resolved {name} via suffix to {variant}")
            return symbol
    
    # 4. Try removing common suffixes if name has them
    for suffix in [".m", ".cash", ".raw", ".p", ".ecn"]:
        if name_upper.endswith(suffix):
            base = name_upper[:-len(suffix)]
            symbol = await catalog.get_symbol(base)
            if symbol:
                logger.debug(f"Resolved {name} by removing suffix to {base}")
                return symbol
    
    logger.warning(f"Could not resolve symbol: {name}")
    return None


async def find_similar_symbols(
    catalog: "SymbolCatalog",
    pattern: str,
    *,
    max_results: int = 10,
) -> list["Symbol"]:
    """Find symbols similar to a pattern.
    
    Searches for symbols containing the pattern or similar names.
    
    Args:
        catalog: Symbol catalog to search
        pattern: Search pattern
        max_results: Maximum results to return
        
    Returns:
        List of matching symbols
    """
    all_symbols = await catalog.get_all()
    pattern_upper = pattern.upper()
    
    matches = []
    for sym in all_symbols:
        score = 0
        name_upper = sym.name.upper()
        
        # Exact match
        if name_upper == pattern_upper:
            score = 100
        # Starts with pattern
        elif name_upper.startswith(pattern_upper):
            score = 80
        # Contains pattern
        elif pattern_upper in name_upper:
            score = 60
        # Pattern contains symbol name (for short symbols)
        elif len(name_upper) >= 3 and name_upper in pattern_upper:
            score = 40
        
        if score > 0:
            matches.append((score, sym))
    
    # Sort by score descending
    matches.sort(key=lambda x: x[0], reverse=True)
    
    return [sym for _, sym in matches[:max_results]]
