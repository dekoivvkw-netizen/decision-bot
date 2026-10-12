"""Vincoli coppia da revx (sola lettura)."""

from __future__ import annotations

import json
import math
import time
from dataclasses import asdict, dataclass
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from pathlib import Path

from .market import run_revx

CACHE_PATH = Path(__file__).resolve().parent.parent / "state" / "vincoli_coppie.json"
CACHE_TTL_S = 24 * 3600


@dataclass(frozen=True)
class PairConstraints:
    pair: str
    base_step: float
    quote_step: float
    min_order_size: float
    min_order_size_quote: float
    max_order_size: float = math.inf
    status: str = "active"


def parse_pairs(payload):
    data = json.loads(payload) if isinstance(payload, str) else payload
    rows = data.get("data", data) if isinstance(data, dict) else data
    out = {}
    for r in rows:
        pair = r["symbol"].replace("/", "-").upper()
        out[pair] = PairConstraints(
            pair=pair,
            base_step=float(r["base_step"]),
            quote_step=float(r["quote_step"]),
            min_order_size=float(r["min_order_size"]),
            min_order_size_quote=float(r["min_order_size_quote"]),
            max_order_size=float(r.get("max_order_size", math.inf)),
            status=r.get("status", "active"),
        )
    return out


def fetch(pairs, revx="~/.local/bin/revx", cache=CACHE_PATH, refresh=False):
    pairs = [p.upper() for p in pairs]
    cached = {}
    if not refresh and cache and cache.exists():
        try:
            raw = json.loads(cache.read_text())
            if time.time() - raw.get("salvato", 0) <= CACHE_TTL_S:
                cached = raw.get("coppie", {})
        except Exception:
            pass
    missing = [p for p in pairs if p not in cached]
    if missing:
        out = run_revx(["market", "pairs", "--filter", ",".join(missing), "--json"], revx)
        for k, v in parse_pairs(out).items():
            cached[k] = asdict(v)
        if cache:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps({"salvato": time.time(), "coppie": cached}, indent=2))
    result = {}
    for p in pairs:
        if p not in cached:
            raise ValueError(f"coppia {p} non trovata")
        result[p] = PairConstraints(**cached[p])
    return result


def round_down(x, step):
    s = Decimal(str(step))
    return float((Decimal(str(x)) / s).to_integral_value(rounding=ROUND_DOWN) * s)


def round_near(x, step):
    s = Decimal(str(step))
    return float((Decimal(str(x)) / s).to_integral_value(rounding=ROUND_HALF_UP) * s)


def decimals(step):
    return max(0, -Decimal(str(step)).normalize().as_tuple().exponent)


def fit_order(c, qty, limit):
    q, p = round_down(qty, c.base_step), round_near(limit, c.quote_step)
    if q < c.min_order_size:
        return q, p, f"quantità {q} sotto minimo {c.min_order_size}"
    if q * p < c.min_order_size_quote:
        return q, p, f"controvalore sotto minimo {c.min_order_size_quote}"
    return q, p, None
