"""Segnali COMPRA/VENDI/NEUTRO."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import market
from .config import Config
from .indicators import prepare
from .strategy import decide, levels


@dataclass
class Signal:
    pair: str
    side: str
    reason: str
    price: float
    rsi: float
    atr: float
    trend_fast: str
    trend_slow: str
    stop: float | None = None
    target: float | None = None

    def line(self) -> str:
        s = (f"{self.pair} | {self.side} | prezzo {self.price:.4f} | RSI {self.rsi:.1f} | "
             f"15m {self.trend_fast} | 1h {self.trend_slow} | {self.reason}")
        if self.stop is not None:
            s += f" | stop {self.stop:.4f} target {self.target:.4f}"
        return s


def evaluate(pair: str, fast: pd.DataFrame, slow: pd.DataFrame, mode: str) -> Signal:
    f, s = prepare(fast), prepare(slow)
    if len(f) < 3 or len(s) < 1:
        raise ValueError("storico insufficiente")
    side, reason, last = decide(f, s, mode)
    sig = Signal(pair, side, reason, float(last["Close"]), float(last["RSI"]), float(last["ATR"]),
                 str(last["Trend"]), str(s.iloc[-1]["Trend"]))
    if side != "NEUTRO":
        sig.stop, sig.target = levels(last, side, mode)
    return sig


def signal_for(pair: str, cfg: Config) -> Signal:
    fast = market.candles(pair, cfg.fast_interval, cfg.fast_since, cfg.revx_path)
    slow = market.candles(pair, cfg.slow_interval, cfg.slow_since, cfg.revx_path)
    return evaluate(pair, fast, slow, cfg.mode)
