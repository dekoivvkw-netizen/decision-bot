"""Caricamento config.toml."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "config.toml"


@dataclass
class PolicyConfig:
    max_trade_notional: float = 150.0
    max_position_pct: float = 50.0
    max_risk_pct: float = 2.0
    min_rr_ratio: float = 1.2
    max_spread_bps: float = 50.0
    proposal_ttl_minutes: int = 15
    kill_switch: bool = False
    asset_allowlist: tuple[str, ...] = ("BTC-EUR", "ETH-EUR", "DOT-EUR", "ATOM-EUR")


@dataclass
class Config:
    pairs: list[str] = field(default_factory=lambda: ["DOT-EUR", "ATOM-EUR", "ETH-EUR", "BTC-EUR"])
    mode: str = "conservative"
    fast_interval: str = "15m"
    fast_since: str = "5d"
    slow_interval: str = "1h"
    slow_since: str = "20d"
    capital_eur: float = 100.0
    risk_per_trade_pct: float = 1.0
    max_position_pct: float = 50.0
    revx_path: str = "~/.local/bin/revx"
    policy: PolicyConfig = field(default_factory=PolicyConfig)


def load(path: str | Path | None = None) -> Config:
    p = Path(path) if path else DEFAULT_PATH
    if not p.exists():
        return Config()
    data = tomllib.loads(p.read_text(encoding="utf-8"))
    sig, cap, pol = data.get("segnali", {}), data.get("capitale", {}), data.get("policy", {})
    allow = pol.get("allowlist")
    if allow is None:
        allowlist = PolicyConfig().asset_allowlist
    elif isinstance(allow, str):
        allowlist = tuple(x.strip().upper() for x in allow.split(",") if x.strip())
    else:
        allowlist = tuple(str(x).upper() for x in allow)
    policy_cfg = PolicyConfig(
        max_trade_notional=float(pol.get("max_trade_notional", 150.0)),
        max_position_pct=float(pol.get("max_position_pct", cap.get("max_posizione_pct", 50.0))),
        max_risk_pct=float(pol.get("max_risk_pct", 2.0)),
        min_rr_ratio=float(pol.get("min_rr_ratio", 1.2)),
        max_spread_bps=float(pol.get("max_spread_bps", 50.0)),
        proposal_ttl_minutes=int(pol.get("proposal_ttl_minutes", 15)),
        kill_switch=bool(pol.get("kill_switch", False)),
        asset_allowlist=allowlist,
    )
    cfg = Config(
        pairs=list(sig.get("coppie", Config().pairs)),
        mode=sig.get("modalita", "conservative"),
        fast_interval=sig.get("intervallo_veloce", "15m"),
        fast_since=sig.get("storico_veloce", "5d"),
        slow_interval=sig.get("intervallo_lento", "1h"),
        slow_since=sig.get("storico_lento", "20d"),
        capital_eur=float(cap.get("eur", 100.0)),
        risk_per_trade_pct=float(cap.get("rischio_per_trade_pct", 1.0)),
        max_position_pct=float(cap.get("max_posizione_pct", 50.0)),
        revx_path=data.get("revx", {}).get("percorso", "~/.local/bin/revx"),
        policy=policy_cfg,
    )
    from .strategy import MODES
    if cfg.mode not in MODES:
        raise ValueError(f"modalità sconosciuta: {cfg.mode}")
    return cfg
