import pytest

from ctc.api.assets import AssetCatalog
from ctc.api.symbols import SymbolCatalog
from ctc.models import Asset


class DummyProtocol:
    def __init__(self, response):
        self._response = response

    async def send_request(self, req, *, timeout=30.0, request_type=None, hooks=None):
        return self._response


class DummyConfig:
    account_id = 1
    request_timeout = 1.0


class DummyAssetRes:
    def __init__(self):
        self.asset = []


class DummyAsset:
    def __init__(self, assetId, name, displayName=None, digits=None):
        self.assetId = assetId
        self.name = name
        self.displayName = displayName
        self.digits = digits


@pytest.mark.asyncio
async def test_asset_catalog_loads_assets():
    res = DummyAssetRes()
    res.asset = [DummyAsset(1, "USD", "US Dollar", 2), DummyAsset(2, "BTC", "Bitcoin", 8)]
    catalog = AssetCatalog(DummyProtocol(res), DummyConfig())
    await catalog.load()

    usd = await catalog.get_asset("usd")
    assert isinstance(usd, Asset)
    assert usd.id == 1
    assert usd.digits == 2

    btc = await catalog.get_asset_by_id(2)
    assert btc.name == "BTC"


class DummySymbolsRes:
    def __init__(self):
        self.symbol = []


class DummySymbolPB:
    def __init__(self, **kw):
        self.__dict__.update(kw)


@pytest.mark.asyncio
async def test_symbol_parsing_includes_asset_ids():
    # We test parser directly (no network)
    res = DummySymbolsRes()
    res.symbol = [
        DummySymbolPB(
            symbolId=100,
            symbolName="BTCUSD",
            digits=2,
            enabled=True,
            baseAssetId=2,
            quoteAssetId=1,
            lotSize=1 * 100,
            pipPosition=2,
            minVolume=1,
            maxVolume=1000000,
            volumeStep=1,
        )
    ]

    cat = SymbolCatalog(DummyProtocol(res), DummyConfig())
    # monkeypatch _loaded state to avoid calling load() via get_symbol
    await cat.load()
    sym = await cat.get_symbol("BTCUSD")
    assert sym is not None
    assert sym.base_asset_id == 2
    assert sym.quote_asset_id == 1
