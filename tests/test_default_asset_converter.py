import pytest

from ctc.api.assets import AssetCatalog
from ctc.api.symbols import SymbolCatalog
from ctc.models import Tick
from ctc.utils.tick_store import TickStore
from ctc.utils.fx_converter import DefaultAssetConverter


class DummyProtocol:
    def __init__(self, res):
        self._res = res

    async def send_request(self, req, *, timeout=30.0, request_type=None, hooks=None):
        return self._res


class DummyConfig:
    account_id = 1
    request_timeout = 1.0


class DummyAssetRes:
    def __init__(self, assets):
        self.asset = assets


class DummyAsset:
    def __init__(self, assetId, name, digits=2):
        self.assetId = assetId
        self.name = name
        self.displayName = name
        self.digits = digits


class DummySymbolsRes:
    def __init__(self, symbols):
        self.symbol = symbols


class DummySymbolPB:
    def __init__(self, **kw):
        self.__dict__.update(kw)


@pytest.mark.asyncio
async def test_converter_direct_and_inverted_and_bridge():
    # Assets: USD(1), EUR(2), JPY(3)
    assets_res = DummyAssetRes([
        DummyAsset(1, "USD", 2),
        DummyAsset(2, "EUR", 2),
        DummyAsset(3, "JPY", 0),
    ])
    assets = AssetCatalog(DummyProtocol(assets_res), DummyConfig())
    await assets.load()

    # Symbols: EURUSD (base=EUR quote=USD), USDJPY (base=USD quote=JPY)
    syms_res = DummySymbolsRes([
        DummySymbolPB(symbolId=10, symbolName="EURUSD", digits=5, enabled=True, baseAssetId=2, quoteAssetId=1, pipPosition=4, lotSize=100000*100, minVolume=1, maxVolume=1000000, volumeStep=1),
        DummySymbolPB(symbolId=11, symbolName="USDJPY", digits=3, enabled=True, baseAssetId=1, quoteAssetId=3, pipPosition=2, lotSize=100000*100, minVolume=1, maxVolume=1000000, volumeStep=1),
    ])
    symbols = SymbolCatalog(DummyProtocol(syms_res), DummyConfig())
    await symbols.load()

    ticks = TickStore()
    await ticks.set(Tick(symbol_id=10, symbol_name="EURUSD", bid=1.10, ask=1.12, timestamp=0))
    await ticks.set(Tick(symbol_id=11, symbol_name="USDJPY", bid=150.0, ask=151.0, timestamp=0))

    conv = DefaultAssetConverter(symbols=symbols, assets=assets, ticks=ticks, bridge_asset="USD")

    # direct EUR->USD uses EURUSD mid = 1.11
    eur_to_usd = await conv.convert_async(amount=10, from_asset="EUR", to_asset="USD")
    assert abs(eur_to_usd - 11.1) < 1e-9

    # inverted USD->EUR uses 1/mid
    usd_to_eur = await conv.convert_async(amount=11.1, from_asset="USD", to_asset="EUR")
    assert abs(usd_to_eur - 10.0) < 1e-9

    # bridged EUR->JPY = (EUR->USD) * (USD->JPY)
    eur_to_jpy = await conv.convert_async(amount=1, from_asset="EUR", to_asset="JPY")
    # EURUSD mid 1.11, USDJPY mid 150.5 => 167.055
    assert abs(eur_to_jpy - (1.11 * 150.5)) < 1e-9
