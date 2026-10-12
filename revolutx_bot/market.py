"""Dati di mercato via CLI revx (sola lettura)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess

import pandas as pd


class RevxError(RuntimeError):
    pass


def revx_bin(path: str = "~/.local/bin/revx") -> str:
    p = os.path.expanduser(os.environ.get("REVX_BIN", path))
    if os.path.exists(p):
        return p
    found = shutil.which("revx")
    if found:
        return found
    raise RevxError(f"revx non trovato ({p}). Installa e configura la CLI Revolut X.")


def run_revx(args: list[str], revx: str = "~/.local/bin/revx", timeout: int = 120) -> str:
    cmd = [revx_bin(revx), *args]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if res.returncode != 0:
        raise RevxError(f"revx {' '.join(args)} fallito: {(res.stderr or res.stdout).strip()[:300]}")
    return res.stdout


def parse_candles(payload: str | dict) -> pd.DataFrame:
    data = json.loads(payload) if isinstance(payload, str) else payload
    rows = data["data"] if isinstance(data, dict) else data
    if not rows:
        raise RevxError("nessuna candela ricevuta")
    df = pd.DataFrame(rows)
    df["start"] = pd.to_datetime(df["start"].astype("int64"), unit="ms", utc=True)
    df = df.set_index("start").sort_index()
    return df.rename(columns=str.capitalize)[["Open", "High", "Low", "Close", "Volume"]].astype(float)


def candles(symbol: str, interval: str, since: str, revx: str = "~/.local/bin/revx") -> pd.DataFrame:
    out = run_revx(["market", "candles", symbol, "--interval", interval, "--since", since, "--json"], revx)
    return parse_candles(out)
