from app.indicators import enrich, adjust_split
from app.market import history
from decimal import Decimal as D


def test_indicators_prefix_invariance_and_warmup():
    h = history("sim:BTC-EUR", "1u")
    full = enrich(h)
    prefix = enrich({**h, "rows": h["rows"][:60]})
    assert full["rows"][:60] == prefix["rows"]
    assert full["rows"][12]["atr14"] is None and full["rows"][13]["atr14"] is not None
    assert full["rows"][13]["rsi14"] is None and full["rows"][14]["rsi14"] is not None
    assert all(0 <= D(r["rsi14"]) <= 100 for r in full["rows"] if r["rsi14"])
    assert (
        full["rows"][32]["macd_signal"] is None
        and full["rows"][33]["macd_signal"] is not None
    )


def test_flat_series_rsi_and_vwap_zero_volume():
    rows = [
        {
            "time": 1704067200 + i * 60,
            "open": "100",
            "high": "100",
            "low": "100",
            "close": "100",
            "volume": "0",
            "sma20": None,
        }
        for i in range(40)
    ]
    r = enrich({"rows": rows})["rows"][-1]
    assert r["rsi14"] == "50.00000000" and r["atr14"] == "0E-8" and r["vwap"] is None
    assert rows[-1]["close"] == "100"


def test_split_adjustment_preserves_raw_and_notional():
    raw = [
        {
            "time": 1,
            "open": "100",
            "high": "102",
            "low": "99",
            "close": "101",
            "volume": "1000",
        }
    ]
    adjusted = adjust_split(raw, 2, "2", "1")
    assert raw[0]["close"] == "101" and adjusted[0]["close"] == "50.5"
    assert D(raw[0]["close"]) * D(raw[0]["volume"]) == D(adjusted[0]["close"]) * D(
        adjusted[0]["volume"]
    )
