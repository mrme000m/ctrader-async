from ctc.models import Symbol, Asset
from ctc.utils.conversions import (
    lots_to_base_units,
    base_units_to_lots,
    lots_to_quote_notional,
    quote_notional_to_lots,
    round_money,
)


def test_lots_base_units_roundtrip():
    sym = Symbol(id=1, name="EURUSD", digits=5, lot_size=100_000 * 100)
    assert lots_to_base_units(sym, 1.0) == 100_000.0
    assert abs(base_units_to_lots(sym, 250_000.0) - 2.5) < 1e-12


def test_quote_notional_roundtrip():
    # 1 lot = 1 BTC
    sym = Symbol(id=1, name="BTCUSD", digits=2, lot_size=1 * 100)
    notional = lots_to_quote_notional(sym, lots=0.002, price=50_000)
    assert abs(notional - 100.0) < 1e-12
    lots = quote_notional_to_lots(sym, quote_notional=100.0, price=50_000)
    assert abs(lots - 0.002) < 1e-12


def test_round_money_uses_asset_digits():
    usd = Asset(id=1, name="USD", digits=2)
    assert round_money(1.239, usd) == 1.24
