"""Indicatori tecnici: EMA, RSI, ATR, Bollinger."""

from __future__ import annotations

import numpy as np
import pandas as pd


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def rsi(s: pd.Series, n: int = 14) -> pd.Series:
    d = s.diff()
    up = d.clip(lower=0).rolling(n).mean()
    down = (-d.clip(upper=0)).rolling(n).mean()
    return 100 - 100 / (1 + up / down.replace(0, np.nan))


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    prev = df["Close"].shift(1)
    tr = pd.concat(
        [df["High"] - df["Low"], (df["High"] - prev).abs(), (df["Low"] - prev).abs()],
        axis=1,
    ).max(axis=1)
    return tr.rolling(n).mean()


def bollinger(s: pd.Series, n: int = 20, k: float = 2.0):
    mid = s.rolling(n).mean()
    std = s.rolling(n).std()
    return mid, mid + k * std, mid - k * std


def trend(df: pd.DataFrame) -> np.ndarray:
    return np.where(
        (df["EMA20"] > df["EMA50"]) & (df["Close"] > df["EMA20"]),
        "BULLISH",
        np.where(
            (df["EMA20"] < df["EMA50"]) & (df["Close"] < df["EMA20"]),
            "BEARISH",
            "SIDEWAYS",
        ),
    )


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["EMA20"] = ema(out["Close"], 20)
    out["EMA50"] = ema(out["Close"], 50)
    out["RSI"] = rsi(out["Close"])
    out["ATR"] = atr(out)
    out["ATR_MED"] = out["ATR"].rolling(50).median()
    mid, upper, lower = bollinger(out["Close"])
    out["BB_MID"], out["BB_UPPER"], out["BB_LOWER"] = mid, upper, lower
    out["Trend"] = trend(out)
    return out.dropna()
