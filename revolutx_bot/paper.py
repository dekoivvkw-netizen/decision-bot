"""Paper trading ledger locale."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATE_DIR = Path(__file__).resolve().parent.parent / "state"
LEDGER_PATH = STATE_DIR / "paper.jsonl"
EQUITY_PATH = STATE_DIR / "paper_equity.json"


def _ensure():
    STATE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class PaperOrder:
    ts: str
    pair: str
    side: str
    qty: float
    limit: float
    stop: float
    target: float
    notional: float
    risk: float
    reason: str
    status: str = "open"
    pnl: float = 0.0
    exit_price: float | None = None
    closed_at: str | None = None
    close_reason: str | None = None


@dataclass
class EquityState:
    capital: float = 100.0
    cash: float = 100.0
    realized_pnl: float = 0.0
    open_orders: int = 0
    closed_orders: int = 0
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def load_equity(default_capital=100.0):
    _ensure()
    if not EQUITY_PATH.exists():
        return EquityState(capital=default_capital, cash=default_capital)
    try:
        data = json.loads(EQUITY_PATH.read_text())
        return EquityState(**{k: data[k] for k in EquityState.__dataclass_fields__ if k in data})
    except Exception:
        return EquityState(capital=default_capital, cash=default_capital)


def save_equity(eq):
    _ensure()
    eq.updated_at = datetime.now(timezone.utc).isoformat()
    EQUITY_PATH.write_text(json.dumps(asdict(eq), indent=2))


def _read_all():
    if not LEDGER_PATH.exists():
        return []
    rows = []
    for line in LEDGER_PATH.read_text().splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def _write_all(rows):
    _ensure()
    with LEDGER_PATH.open("w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def record_proposal(*, pair, side, qty, limit, stop, target, notional, risk, reason, capital=100.0):
    order = PaperOrder(
        ts=datetime.now(timezone.utc).isoformat(), pair=pair, side=side,
        qty=qty, limit=limit, stop=stop, target=target, notional=notional,
        risk=risk, reason=reason,
    )
    _ensure()
    with LEDGER_PATH.open("a") as f:
        f.write(json.dumps(asdict(order), ensure_ascii=False) + "\n")
    eq = load_equity(capital)
    eq.open_orders += 1
    if side == "buy":
        eq.cash = max(0.0, eq.cash - notional)
    save_equity(eq)
    return order


def list_orders(limit=50):
    return _read_all()[-limit:]


def list_open():
    return [(i, r) for i, r in enumerate(_read_all()) if r.get("status", "open") == "open"]


def close_order(*, index=None, pair=None, outcome="target", price=None, capital=100.0):
    rows = _read_all()
    open_idx = [(i, r) for i, r in enumerate(rows) if r.get("status", "open") == "open"]
    if not open_idx:
        raise ValueError("nessun ordine open")
    if index is not None:
        if index < 1 or index > len(open_idx):
            raise ValueError(f"indice {index} fuori range")
        gi, row = open_idx[index - 1]
    elif pair:
        chosen = None
        for i, r in reversed(open_idx):
            if r.get("pair") == pair.upper():
                chosen = (i, r)
                break
        if not chosen:
            raise ValueError(f"nessun open per {pair}")
        gi, row = chosen
    else:
        gi, row = open_idx[-1]
    entry, side, qty = float(row["limit"]), row["side"], float(row["qty"])
    if outcome == "target":
        exit_px, close_reason = float(row["target"]), "target"
    elif outcome == "stop":
        exit_px, close_reason = float(row["stop"]), "stop"
    elif outcome == "price":
        if price is None:
            raise ValueError("serve prezzo")
        exit_px, close_reason = float(price), f"prezzo {price}"
    else:
        raise ValueError(outcome)
    pnl = (exit_px - entry) * qty if side == "buy" else (entry - exit_px) * qty
    row.update(status="closed", pnl=round(pnl, 6), exit_price=exit_px,
               closed_at=datetime.now(timezone.utc).isoformat(), close_reason=close_reason)
    rows[gi] = row
    _write_all(rows)
    eq = load_equity(capital)
    eq.open_orders = max(0, eq.open_orders - 1)
    eq.closed_orders += 1
    eq.realized_pnl = round(eq.realized_pnl + pnl, 6)
    eq.cash = round(eq.cash + (float(row["notional"]) + pnl if side == "buy" else pnl), 6)
    save_equity(eq)
    return row


def summary(capital=100.0):
    eq = load_equity(capital)
    lines = [
        f"PAPER capital={eq.capital:.2f} cash={eq.cash:.2f} pnl={eq.realized_pnl:.2f}",
        f"  open={eq.open_orders} closed={eq.closed_orders}",
    ]
    for n, (_, o) in enumerate(list_open(), 1):
        lines.append(f"  [{n}] {o.get('pair')} {o.get('side')} @ {o.get('limit')}")
    return "\n".join(lines)
