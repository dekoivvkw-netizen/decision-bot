"""Policy / Gate deterministico."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .config import Config, PolicyConfig


@dataclass
class Policy:
    max_trade_notional: float = 150.0
    max_position_pct: float = 50.0
    max_risk_pct: float = 2.0
    min_rr_ratio: float = 1.2
    max_spread_bps: float = 50.0
    proposal_ttl_minutes: int = 15
    asset_allowlist: tuple[str, ...] = ("BTC-EUR", "ETH-EUR", "DOT-EUR", "ATOM-EUR")
    kill_switch: bool = False

    def check_pair(self, pair: str) -> Optional[str]:
        if pair not in self.asset_allowlist:
            return f"coppia {pair} non in allowlist"
        return None

    def check_proposal(self, *, pair: str, side: str, notional: float, risk: float,
                       capital: float, rr: float, spread_bps: Optional[float] = None) -> Optional[str]:
        if self.kill_switch:
            return "Kill switch attivo: nessuna proposta accettata"
        err = self.check_pair(pair)
        if err:
            return err
        if notional > self.max_trade_notional:
            return f"notional {notional:.2f} > max {self.max_trade_notional}"
        if capital > 0 and (notional / capital * 100) > self.max_position_pct:
            return f"posizione {notional/capital*100:.1f}% > max {self.max_position_pct}%"
        if capital > 0 and (risk / capital * 100) > self.max_risk_pct:
            return f"rischio {risk/capital*100:.1f}% > max {self.max_risk_pct}%"
        if rr < self.min_rr_ratio:
            return f"R/R {rr:.2f} < minimo {self.min_rr_ratio}"
        if spread_bps is not None and spread_bps > self.max_spread_bps:
            return f"spread {spread_bps:.1f} bps > max {self.max_spread_bps}"
        return None


def default_policy() -> Policy:
    return Policy()


def policy_from_config(cfg: "Config") -> Policy:
    p = cfg.policy
    return Policy(
        max_trade_notional=p.max_trade_notional,
        max_position_pct=p.max_position_pct,
        max_risk_pct=p.max_risk_pct,
        min_rr_ratio=p.min_rr_ratio,
        max_spread_bps=p.max_spread_bps,
        proposal_ttl_minutes=p.proposal_ttl_minutes,
        asset_allowlist=p.asset_allowlist,
        kill_switch=p.kill_switch,
    )
