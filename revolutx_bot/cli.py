"""CLI Decision Bot."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from . import __version__, decision_engine, paper, status
from .config import load
from .policy import policy_from_config
from .signals import signal_for


def cmd_gui(args, cfg) -> int:
    root = Path(__file__).resolve().parent.parent
    gui = root / "revolutx_bot" / "gui.py"
    cmd = [sys.executable, "-m", "streamlit", "run", str(gui),
           "--server.headless", "true", "--browser.gatherUsageStats", "false"]
    print("GUI → http://localhost:8501")
    try:
        return subprocess.call(cmd, cwd=str(root))
    except FileNotFoundError:
        print("pip install streamlit", file=sys.stderr)
        return 1


def cmd_decide(args, cfg) -> int:
    capital = args.capitale or cfg.capital_eur
    pairs = [p.upper() for p in (args.coppie or cfg.pairs)]
    decisions = decision_engine.decide_all(
        cfg, pairs, capital=capital, record_paper=bool(args.paper)
    )
    print(decision_engine.render_report(decisions, cfg, capital))
    return 1 if any(d.action == "ERROR" for d in decisions) else 0


def cmd_segnali(args, cfg) -> int:
    rc = 0
    for pair in ([p.upper() for p in args.coppie] or cfg.pairs):
        try:
            print(signal_for(pair, cfg).line())
        except Exception as e:
            print(f"{pair} | ERRORE | {e}")
            rc = 1
    return rc


def cmd_paper(args, cfg) -> int:
    print(paper.summary(args.capitale or cfg.capital_eur))
    return 0


def cmd_paper_chiudi(args, cfg) -> int:
    outcome = "stop" if args.stop else ("price" if args.prezzo is not None else "target")
    try:
        row = paper.close_order(index=args.indice, pair=args.coppia, outcome=outcome,
                                price=args.prezzo, capital=args.capitale or cfg.capital_eur)
        print(f"CHIUSO {row.get('pair')} pnl={row.get('pnl')}")
    except ValueError as e:
        print(f"ERRORE: {e}")
        return 1
    return 0


def cmd_stato(args, cfg) -> int:
    print(status.render(cfg.capital_eur, cfg))
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="revolutx_bot")
    p.add_argument("--version", action="version", version=__version__)
    p.add_argument("--config")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("gui"); s.set_defaults(func=cmd_gui)
    s = sub.add_parser("decide")
    s.add_argument("coppie", nargs="*")
    s.add_argument("--capitale", type=float)
    s.add_argument("--paper", action="store_true")
    s.set_defaults(func=cmd_decide)
    s = sub.add_parser("segnali"); s.add_argument("coppie", nargs="*"); s.set_defaults(func=cmd_segnali)
    s = sub.add_parser("paper"); s.add_argument("--capitale", type=float); s.set_defaults(func=cmd_paper)
    s = sub.add_parser("paper-chiudi")
    s.add_argument("--indice", type=int); s.add_argument("--coppia")
    s.add_argument("--target", action="store_true"); s.add_argument("--stop", action="store_true")
    s.add_argument("--prezzo", type=float); s.add_argument("--capitale", type=float)
    s.set_defaults(func=cmd_paper_chiudi)
    s = sub.add_parser("stato"); s.set_defaults(func=cmd_stato)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        cfg = load(args.config)
    except Exception as e:
        print(f"Config: {e}", file=sys.stderr)
        return 2
    return args.func(args, cfg)
