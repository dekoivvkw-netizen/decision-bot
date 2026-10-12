"""Motore decisionale unificato."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from . import constraints as C
from . import paper, proposal
from .audit import log_event, log_proposal, log_signal
from .config import Config
from .policy import Policy, policy_from_config
from .signals import Signal, signal_for

DecisionAction = Literal["SKIP", "PROPOSE", "PAPER", "BLOCKED", "ERROR"]


@dataclass
class Decision:
    pair: str
    action: DecisionAction
    side: str
    reason: str
    signal: Signal | None = None
    proposal: proposal.Proposal | None = None
    path: str = ""

    def line(self) -> str:
        icon = {"SKIP": "·", "PROPOSE": "★", "PAPER": "◆", "BLOCKED": "✕", "ERROR": "!"}.get(self.action, "?")
        base = f"{icon} {self.pair:10} | {self.action:7} | {self.side:7} | {self.reason}"
        if self.path:
            base += f" | path={self.path}"
        return base


def _path(reason: str) -> str:
    if "mean-reversion" in reason.lower():
        return "mean-reversion"
    return "trend" if reason else "none"


def decide_pair(pair, cfg, *, capital=None, pol=None, record_paper=False, skip_constraints=False):
    capital = capital if capital is not None else cfg.capital_eur
    pol = pol or policy_from_config(cfg)
    pair = pair.upper()
    try:
        sig = signal_for(pair, cfg)
    except Exception as e:
        log_event("decision_error", {"pair": pair, "error": str(e)[:200]})
        return Decision(pair, "ERROR", "ERROR", str(e)[:200])
    path = _path(sig.reason)
    log_signal(pair, sig.side, sig.reason, sig.price, sig.rsi)
    if sig.side == "NEUTRO":
        return Decision(pair, "SKIP", "NEUTRO", sig.reason, sig, path=path)
    cons = None
    if not skip_constraints:
        try:
            cons = C.fetch([pair], cfg.revx_path)[pair]
        except Exception as e:
            return Decision(pair, "BLOCKED", sig.side, f"vincoli: {e}", sig, path=path)
    prop = proposal.build(sig, capital, cfg.risk_per_trade_pct, cfg.max_position_pct, cons, policy=pol)
    if prop is None:
        return Decision(pair, "SKIP", sig.side, sig.reason, sig, path=path)
    accepted = prop.errore is None and prop.policy_reason is None
    log_proposal(pair, prop.side, prop.notional, prop.risk, accepted, prop.errore or prop.policy_reason)
    if not accepted:
        return Decision(pair, "BLOCKED", sig.side, prop.errore or prop.policy_reason or "rifiutato", sig, prop, path)
    if record_paper:
        paper.record_proposal(
            pair=prop.pair, side=prop.side, qty=prop.qty, limit=prop.limit,
            stop=prop.stop, target=prop.target, notional=prop.notional,
            risk=prop.risk, reason=sig.reason, capital=capital,
        )
        return Decision(pair, "PAPER", sig.side, f"paper — {sig.reason}", sig, prop, path)
    return Decision(pair, "PROPOSE", sig.side, sig.reason, sig, prop, path)


def decide_all(cfg, pairs=None, *, capital=None, record_paper=False):
    pol = policy_from_config(cfg)
    capital = capital if capital is not None else cfg.capital_eur
    return [decide_pair(p, cfg, capital=capital, pol=pol, record_paper=record_paper)
            for p in ([x.upper() for x in pairs] if pairs else cfg.pairs)]


def render_report(decisions, cfg, capital=None):
    capital = capital if capital is not None else cfg.capital_eur
    pol = policy_from_config(cfg)
    lines = [
        f"══════════════════════════════════════════════",
        f"  DECISION BOT  {datetime.now():%Y-%m-%d %H:%M}  mode={cfg.mode}",
        f"  capitale={capital:g} EUR  kill_switch={pol.kill_switch}",
        f"══════════════════════════════════════════════",
    ]
    counts = {}
    for d in decisions:
        lines.append(d.line())
        counts[d.action] = counts.get(d.action, 0) + 1
        if d.proposal and d.action in ("PROPOSE", "PAPER"):
            lines.append(d.proposal.render())
            lines.append("")
    lines.append("──────────────────────────────────────────────")
    lines.append(f"  {counts}")
    lines.append("  Nessun ordine reale. Non è un consiglio finanziario.")
    return "\n".join(lines)
