from __future__ import annotations

import asyncio
import logging
from typing import Dict, Optional, TYPE_CHECKING

from ..models import Asset, AssetClass

if TYPE_CHECKING:
    from ..protocol import ProtocolHandler
    from ..config import ClientConfig

logger = logging.getLogger(__name__)


class AssetCatalog:
    """Loads and caches assets (currencies) from the broker."""

    def __init__(self, protocol: ProtocolHandler, config: ClientConfig):
        self.protocol = protocol
        self.config = config
        self._assets_by_id: Dict[int, Asset] = {}
        self._assets_by_name: Dict[str, Asset] = {}
        self._lock = asyncio.Lock()
        self._loaded = False

    async def load(self) -> None:
        from ..messages.OpenApiMessages_pb2 import ProtoOAAssetListReq

        req = ProtoOAAssetListReq()
        req.ctidTraderAccountId = self.config.account_id

        res = await self.protocol.send_request(
            req,
            timeout=self.config.request_timeout,
            request_type="AssetList",
        )

        assets = getattr(res, "asset", [])
        async with self._lock:
            self._assets_by_id.clear()
            self._assets_by_name.clear()
            for a in assets:
                asset = Asset(
                    id=int(getattr(a, "assetId")),
                    name=str(getattr(a, "name")),
                    display_name=getattr(a, "displayName", None),
                    digits=getattr(a, "digits", None),
                )
                self._assets_by_id[asset.id] = asset
                self._assets_by_name[asset.name.upper()] = asset
            self._loaded = True

        logger.info("Loaded %s assets", len(self._assets_by_id))

    async def get_asset_by_id(self, asset_id: int) -> Optional[Asset]:
        if not self._loaded:
            await self.load()
        async with self._lock:
            return self._assets_by_id.get(int(asset_id))

    async def get_asset(self, name: str) -> Optional[Asset]:
        if not self._loaded:
            await self.load()
        async with self._lock:
            return self._assets_by_name.get(str(name).upper())

    async def get_all(self) -> list[Asset]:
        if not self._loaded:
            await self.load()
        async with self._lock:
            return list(self._assets_by_id.values())
    
    async def get_asset_classes(self) -> list[AssetClass]:
        """Get list of all asset classes.
        
        Asset classes group assets by type (e.g., Currencies, Commodities,
        Indices, Stocks, Cryptocurrencies).
        
        Returns:
            List of AssetClass objects
            
        Example:
            >>> classes = await client.assets.get_asset_classes()
            >>> for asset_class in classes:
            ...     print(f"{asset_class.name}: {len(asset_class.asset_ids)} assets")
        """
        from ..messages.OpenApiMessages_pb2 import (
            ProtoOAAssetClassListReq,
            ProtoOAAssetClassListRes,
        )
        
        # Build request
        req = ProtoOAAssetClassListReq()
        req.ctidTraderAccountId = self.config.account_id
        
        # Send request
        res = await self.protocol.send_request(
            req,
            timeout=self.config.request_timeout,
            request_type="AssetClassList",
        )
        
        if not isinstance(res, ProtoOAAssetClassListRes):
            raise ValueError(f"Unexpected response type: {type(res)}")
        
        # Parse asset classes
        classes = []
        if hasattr(res, 'assetClass'):
            for ac in res.assetClass:
                asset_class_id = getattr(ac, 'id', None)
                name = getattr(ac, 'name', None)
                
                if asset_class_id is None or name is None:
                    continue
                
                # Get asset IDs in this class
                asset_ids = []
                if hasattr(ac, 'assetId'):
                    asset_ids = list(ac.assetId)
                
                classes.append(AssetClass(
                    id=asset_class_id,
                    name=name,
                    asset_ids=asset_ids
                ))
        
        logger.info("Retrieved %s asset classes", len(classes))
        return classes
