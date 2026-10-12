"""Proposta d'ordine — solo stampa, mai eseguita."""

from __future__ import annotations

from dataclasses import dataclass

from .constraints import PairConstraints, decimals, fit_order, round_near
from .policy import Policy, default_policy
from .signals import Signal


@dataclass
class Proposal:
    pair: str
    side: str
    qty: float
    limit: float
    stop: float
    target: float
    notional: float
    risk: float
    qty_dec: int = 6
    px_dec: int = 4
    errore: str | None = None
    policy_reason: str | None = None

    def render(self) -> str:
        base, quote = self.pair.split("-")
        q, px = self.qty_dec, self.px_dec
        if self.errore:
            return f"PROPOSTA RIFIUTATA — {self.pair}: {self.errore}"
        if self.policy_reason:
            return f"PROPOSTA BLOCCATA DA POLICY — {self.pair}: {self.policy_reason}"
        rr = abs(self.target - self.limit) / abs(self.limit - self.stop) if abs(self.limit - self.stop) else 0
        return "\n".join([
            f"PROPOSTA (NON ESEGUITA) — {self.pair}",
            f"  lato     : {self.side.upper()}",
            f"  quantità : {self.qty:.{q}f} {base}  (~{self.notional:.2f} {quote})",
            f"  limite   : {self.limit:.{px}f}",
            f"  stop     : {self.stop:.{px}f}",
            f"  target   : {self.target:.{px}f}",
            f"  rischio  : ~{self.risk:.2f}  R/R {rr:.2f}",
            f"  revx order place {self.pair} {self.side} --qty {self.qty:.{q}f} --limit {self.limit:.{px}f} --post-only",
            "  (comando da lanciare A MANO solo se sei d'accordo)",
        ])


def build(sig, capital, risk_pct, max_pos_pct, constraints=None, policy=None):
    if sig.side == "NEUTRO" or sig.stop is None or sig.target is None:
        return None
    dist = abs(sig.price - sig.stop)
    if dist <= 0:
        return None
    qty = (capital * risk_pct / 100.0) / dist
    max_n = capital * max_pos_pct / 100.0
    if qty * sig.price > max_n:
        qty = max_n / sig.price
    limit, stop, target = sig.price, sig.stop, sig.target
    qty_dec, px_dec, err = 6, 4, None
    if constraints is not None:
        qty, limit, err = fit_order(constraints, qty, limit)
        stop = round_near(stop, constraints.quote_step)
        target = round_near(target, constraints.quote_step)
        qty_dec, px_dec = decimals(constraints.base_step), decimals(constraints.quote_step)
    notional = qty * limit
    risk = qty * abs(limit - stop)
    rr = abs(target - limit) / abs(limit - stop) if abs(limit - stop) else 0.0
    pol = policy or default_policy()
    policy_reason = pol.check_proposal(
        pair=sig.pair, side=sig.side, notional=notional, risk=risk, capital=capital, rr=rr
    )
    return Proposal(
        pair=sig.pair, side="buy" if sig.side == "COMPRA" else "sell",
        qty=qty, limit=limit, stop=stop, target=target,
        notional=notional, risk=risk, qty_dec=qty_dec, px_dec=px_dec,
        errore=err, policy_reason=policy_reason,
    )
