"""Trend primario + mean-reversion Bollinger secondario."""

from __future__ import annotations

import pandas as pd

MODES = {
    "precise": {
        "rsi_buy": (42, 62), "rsi_sell": (38, 58), "sl": 1.8, "tp": 2.6, "confirm": 2,
        "mr_oversold": 28, "mr_overbought": 72, "mr_enabled": True,
    },
    "conservative": {
        "rsi_buy": (42, 55), "rsi_sell": (45, 58), "sl": 2.0, "tp": 3.0, "confirm": 2,
        "mr_oversold": 25, "mr_overbought": 75, "mr_enabled": True,
    },
    "balanced": {
        "rsi_buy": (40, 65), "rsi_sell": (35, 60), "sl": 1.6, "tp": 2.2, "confirm": 1,
        "mr_oversold": 30, "mr_overbought": 70, "mr_enabled": True,
    },
}
ATR_MIN_RATIO = 0.85


def raw_signal(row: pd.Series, mode: str) -> str:
    cfg = MODES[mode]
    r = float(row["RSI"])
    if row["Trend"] == "BULLISH" and cfg["rsi_buy"][0] <= r <= cfg["rsi_buy"][1]:
        return "COMPRA"
    if row["Trend"] == "BEARISH" and cfg["rsi_sell"][0] <= r <= cfg["rsi_sell"][1]:
        return "VENDI"
    return "NEUTRO"


def mean_reversion_signal(row: pd.Series, mode: str) -> str | None:
    cfg = MODES[mode]
    if not cfg.get("mr_enabled") or "BB_LOWER" not in row.index:
        return None
    r, close = float(row["RSI"]), float(row["Close"])
    if r <= cfg["mr_oversold"] and close <= float(row["BB_LOWER"]) * 1.001:
        return "COMPRA"
    if r >= cfg["mr_overbought"] and close >= float(row["BB_UPPER"]) * 0.999:
        return "VENDI"
    return None


def decide(fast: pd.DataFrame, slow: pd.DataFrame, mode: str):
    cfg = MODES[mode]
    last, hour = fast.iloc[-1], slow.iloc[-1]
    votes = [raw_signal(fast.iloc[i], mode) for i in range(-cfg["confirm"], 0)]
    agreed = len(set(votes)) == 1 and votes[0] != "NEUTRO"
    volatile = float(last["ATR"]) >= float(last["ATR_MED"]) * ATR_MIN_RATIO
    aligned = (votes[0] == "COMPRA" and hour["Trend"] == "BULLISH") or (
        votes[0] == "VENDI" and hour["Trend"] == "BEARISH"
    )
    if agreed and volatile and aligned:
        return votes[0], (
            f"15m {votes[0]} x{cfg['confirm']} candele, 1h {hour['Trend']}, "
            f"RSI {float(last['RSI']):.1f}, ATR ok"
        ), last
    mr = mean_reversion_signal(last, mode)
    if mr and volatile:
        return mr, (
            f"mean-reversion {mr}: RSI {float(last['RSI']):.1f} + Bollinger, ATR ok"
        ), last
    why = []
    if not agreed:
        why.append("15m non confermato")
    if not volatile:
        why.append("volatilità bassa")
    if votes[0] != "NEUTRO" and not aligned:
        why.append(f"1h è {hour['Trend']}, non allineato")
    if not why:
        why.append("nessun segnale")
    return "NEUTRO", "; ".join(why), last


def levels(row: pd.Series, side: str, mode: str):
    cfg = MODES[mode]
    p, a = float(row["Close"]), float(row["ATR"])
    if side == "COMPRA":
        return p - cfg["sl"] * a, p + cfg["tp"] * a
    if side == "VENDI":
        return p + cfg["sl"] * a, p - cfg["tp"] * a
    raise ValueError(side)
