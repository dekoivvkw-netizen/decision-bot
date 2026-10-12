"""Test indicatori senza rete / revx."""

import numpy as np
import pandas as pd

from revolutx_bot.indicators import prepare, bollinger, rsi
from revolutx_bot.strategy import mean_reversion_signal, raw_signal, MODES


def _fake_ohlcv(n=120, start=100.0):
    rng = np.random.default_rng(42)
    close = start + np.cumsum(rng.normal(0, 0.5, n))
    high = close + rng.uniform(0.1, 1.0, n)
    low = close - rng.uniform(0.1, 1.0, n)
    open_ = close + rng.normal(0, 0.2, n)
    vol = rng.uniform(10, 100, n)
    idx = pd.date_range("2024-01-01", periods=n, freq="15min", tz="UTC")
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": vol},
        index=idx,
    )


def test_prepare_has_columns():
    df = prepare(_fake_ohlcv())
    for c in ["EMA20", "EMA50", "RSI", "ATR", "ATR_MED", "BB_MID", "BB_UPPER", "BB_LOWER", "Trend"]:
        assert c in df.columns
    assert len(df) > 20


def test_rsi_bounds():
    s = pd.Series(np.linspace(10, 50, 100))
    r = rsi(s).dropna()
    assert r.min() >= 0
    assert r.max() <= 100


def test_bollinger_order():
    s = pd.Series(np.linspace(1, 50, 80))
    mid, up, lo = bollinger(s)
    ok = mid.dropna().index
    assert (up.loc[ok] >= mid.loc[ok]).all()
    assert (mid.loc[ok] >= lo.loc[ok]).all()


def test_modes_exist():
    assert "conservative" in MODES
    assert "precise" in MODES
    assert "balanced" in MODES
