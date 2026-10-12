"""Audit append-only."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOG_DIR = Path(__file__).resolve().parent.parent / "state"
LOG_PATH = LOG_DIR / "audit.jsonl"


def _ensure() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def log_event(event: str, payload: dict[str, Any]) -> None:
    try:
        _ensure()
        rec = {"ts": datetime.now(timezone.utc).isoformat(), "event": event, **payload}
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def log_signal(pair: str, side: str, reason: str, price: float, rsi: float) -> None:
    log_event("signal", {"pair": pair, "side": side, "reason": reason,
                         "price": round(price, 6), "rsi": round(rsi, 2)})


def log_proposal(pair: str, side: str, notional: float, risk: float,
                 accepted: bool, reason: str | None) -> None:
    log_event("proposal", {"pair": pair, "side": side, "notional": round(notional, 2),
                           "risk": round(risk, 2), "accepted": accepted, "reason": reason})
