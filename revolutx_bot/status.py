"""Stato operativo."""

from __future__ import annotations

from .audit import LOG_PATH
from .paper import summary as paper_summary
from .policy import default_policy, policy_from_config


def render(capital=100.0, cfg=None):
    pol = policy_from_config(cfg) if cfg else default_policy()
    lines = [
        "=== STATO DECISION BOT ===",
        f"kill_switch={pol.kill_switch}  max_notional={pol.max_trade_notional}",
        f"allowlist={', '.join(pol.asset_allowlist)}",
        "",
        paper_summary(capital),
        f"\nAudit: {LOG_PATH} exists={LOG_PATH.exists()}",
    ]
    return "\n".join(lines)
