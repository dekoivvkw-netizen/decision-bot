"""GUI Streamlit Decision Bot."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Decision Bot", page_icon="◆", layout="wide")

from revolutx_bot import decision_engine, paper
from revolutx_bot.config import load
from revolutx_bot.indicators import prepare
from revolutx_bot.market import RevxError, candles
from revolutx_bot.policy import policy_from_config
from revolutx_bot.signals import signal_for


def main():
    st.title("◆ Decision Bot")
    st.caption("Revolut X · decide · paper · grafici — simulazione")
    try:
        cfg = load()
    except Exception as e:
        st.error(str(e))
        st.stop()

    page = st.sidebar.radio("Menu", ["Dashboard", "Decisioni", "Grafici", "Paper"])
    eq = paper.load_equity(cfg.capital_eur)
    pol = policy_from_config(cfg)

    if page == "Dashboard":
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Capitale", f"{eq.capital:.2f}€")
        c2.metric("Cash", f"{eq.cash:.2f}€")
        c3.metric("PnL", f"{eq.realized_pnl:+.2f}€")
        c4.metric("Open/Closed", f"{eq.open_orders}/{eq.closed_orders}")
        st.caption(f"mode={cfg.mode} kill_switch={pol.kill_switch}")
        orders = paper.list_orders(200)
        if orders:
            df = pd.DataFrame(orders)
            if "status" in df.columns:
                closed = df[df["status"] == "closed"]
                if not closed.empty and "pnl" in closed.columns:
                    closed = closed.copy()
                    closed["pnl"] = pd.to_numeric(closed["pnl"], errors="coerce").fillna(0)
                    st.subheader("PnL trade chiusi")
                    st.bar_chart(closed.set_index("pair")["pnl"] if "pair" in closed else closed["pnl"])

    elif page == "Decisioni":
        pairs = st.multiselect("Coppie", cfg.pairs, default=list(cfg.pairs))
        paper_on = st.checkbox("Registra in paper")
        if st.button("Esegui Decision Bot", type="primary") and pairs:
            with st.spinner("Analisi…"):
                decs = decision_engine.decide_all(cfg, pairs, record_paper=paper_on)
            for d in decs:
                st.write(d.line())
                if d.proposal and d.action in ("PROPOSE", "PAPER"):
                    st.code(d.proposal.render())

    elif page == "Grafici":
        pair = st.selectbox("Coppia", cfg.pairs)
        if st.button("Carica"):
            try:
                df = prepare(candles(pair, "15m", "5d", cfg.revx_path))
                st.line_chart(df[["Close", "EMA20", "EMA50", "BB_UPPER", "BB_LOWER"]])
                st.line_chart(df[["RSI"]])
                st.success(signal_for(pair, cfg).line())
            except Exception as e:
                st.error(str(e))

    else:
        st.code(paper.summary(cfg.capital_eur))
        orders = paper.list_orders(100)
        if orders:
            st.dataframe(pd.DataFrame(orders).iloc[::-1], use_container_width=True)


main()
