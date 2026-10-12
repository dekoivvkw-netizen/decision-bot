"""Decision path offline con candele sintetiche."""

import numpy as np
import pandas as pd

from revolutx_bot.indicators import prepare
from revolutx_bot.signals import evaluate
from revolutx_bot.strategy import decide


def _ohlcv(n=150, drift=0.05):
    rng = np.random.default_rng(7)
    close = 100 + np.cumsum(rng.normal(drift, 0.3, n))
    idx = pd.date_range("2024-06-01", periods=n, freq="15min", tz="UTC")
    return pd.DataFrame(
        {
            "Open": close,
            "High": close + 0.5,
            "Low": close - 0.5,
            "Close": close,
            "Volume": np.ones(n) * 50,
        },
        index=idx,
    )


def test_evaluate_returns_signal():
    fast = _ohlcv()
    slow = _ohlcv(n=80, drift=0.08)
    # subsample slow as if 1h
    slow = slow.iloc[::4]
    sig = evaluate("DOT-EUR", fast, slow, "conservative")
    assert sig.side in ("COMPRA", "VENDI", "NEUTRO")
    assert sig.pair == "DOT-EUR"
    assert isinstance(sig.reason, str)


def test_decide_tuple():
    f = prepare(_ohlcv())
    s = prepare(_ohlcv(n=80))
    side, reason, last = decide(f, s, "balanced")
    assert side in ("COMPRA", "VENDI", "NEUTRO")
    assert "Close" in last.index
