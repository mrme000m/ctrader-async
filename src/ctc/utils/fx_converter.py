from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from ..api.assets import AssetCatalog
from ..api.symbols import SymbolCatalog
from ..models import Symbol
from .conversions import AssetConverter
from .tick_store import TickStore

logger = logging.getLogger(__name__)


@dataclass
class ConversionPath:
    symbol: str
    inverted: bool = False


class DefaultAssetConverter(AssetConverter):
    """Convert between assets using available symbols + last ticks.

    Resolution order:
    1) direct pair (FROM/TO) symbol
    2) inverse pair (TO/FROM) symbol (invert price)
    3) via bridge currency (default USD): FROM->BRIDGE and BRIDGE->TO

    Notes:
    - Requires symbols to expose base_asset_id / quote_asset_id.
    - Requires last ticks for the chosen symbols in TickStore.
    - The symbol-pair lookup cache is built lazily on the first conversion call
      and invalidated whenever ``invalidate_cache()`` is called (e.g. after a
      ``market.symbol_changed`` event).
    """

    def __init__(
        self,
        *,
        symbols: SymbolCatalog,
        assets: AssetCatalog,
        ticks: TickStore,
        bridge_asset: str = "USD",
    ):
        self.symbols = symbols
        self.assets = assets
        self.ticks = ticks
        self.bridge_asset = bridge_asset.upper()
        # Cache: (base_asset_name_upper, quote_asset_name_upper) -> symbol_name
        self._pair_cache: Optional[dict] = None

    def invalidate_cache(self) -> None:
        """Invalidate the symbol-pair lookup cache.

        Call this after a ``market.symbol_changed`` event so the next
        conversion rebuilds the index from the refreshed symbol catalog.
        """
        self._pair_cache = None

    async def _ensure_cache(self) -> dict:
        """Build (or return cached) mapping of (base, quote) -> symbol_name."""
        if self._pair_cache is not None:
            return self._pair_cache

        cache: dict = {}
        all_syms = await self.symbols.get_all()
        for s in all_syms:
            if not s.base_asset_id or not s.quote_asset_id:
                continue
            base_asset = await self.assets.get_asset_by_id(int(s.base_asset_id))
            quote_asset = await self.assets.get_asset_by_id(int(s.quote_asset_id))
            if base_asset and quote_asset:
                key = (base_asset.name.upper(), quote_asset.name.upper())
                # Only store first match (symbol catalog may have duplicates)
                if key not in cache:
                    cache[key] = s.name
        self._pair_cache = cache
        return cache

    async def _find_symbol_for_pair(self, base: str, quote: str) -> Optional[str]:
        cache = await self._ensure_cache()
        return cache.get((base.upper(), quote.upper()))

    async def _resolve_path(self, from_asset: str, to_asset: str) -> Optional[ConversionPath]:
        from_u = from_asset.upper()
        to_u = to_asset.upper()

        direct = await self._find_symbol_for_pair(from_u, to_u)
        if direct:
            return ConversionPath(symbol=direct, inverted=False)

        inv = await self._find_symbol_for_pair(to_u, from_u)
        if inv:
            return ConversionPath(symbol=inv, inverted=True)

        return None

    async def _rate(self, from_asset: str, to_asset: str) -> float:
        if from_asset.upper() == to_asset.upper():
            return 1.0

        path = await self._resolve_path(from_asset, to_asset)
        if path:
            mid = await self.ticks.mid(path.symbol)
            if mid is None or mid <= 0:
                raise ValueError(f"No tick available for conversion symbol {path.symbol}")
            return (1.0 / mid) if path.inverted else mid

        # Bridge
        b = self.bridge_asset
        p1 = await self._resolve_path(from_asset, b)
        p2 = await self._resolve_path(b, to_asset)
        if not p1 or not p2:
            raise ValueError(f"No conversion path for {from_asset}->{to_asset} (bridge={b})")

        r1 = await self._rate(from_asset, b)
        r2 = await self._rate(b, to_asset)
        return r1 * r2

    def convert(self, *, amount: float, from_asset: str, to_asset: str) -> float:
        raise RuntimeError("DefaultAssetConverter.convert is async; call convert_async")

    async def convert_async(self, *, amount: float, from_asset: str, to_asset: str) -> float:
        rate = await self._rate(from_asset, to_asset)
        return float(amount) * float(rate)
