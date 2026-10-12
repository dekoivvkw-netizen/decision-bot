# Decision Bot · Revolut X

**Software reale** di trading decisionale: analizza il mercato, decide COMPRA/VENDI/NEUTRO, applica un gate di rischio e propone o registra in **paper trading**.

> Non è un consiglio finanziario. **Non piazza ordini reali in automatico.**

## Link pubblico

https://github.com/dekoivvkw-netizen/decision-bot

(Il repo `trading-bots` resta privato come archivio completo; questo è il pacchetto operativo pubblico.)

## Cosa fa (vero)

1. Legge candele da **Revolut X** (`revx`, sola lettura)
2. Calcola EMA, RSI, ATR, **Bollinger**
3. Decide con due percorsi:
   - **Trend** (primario)
   - **Mean-reversion Bollinger** (secondario)
4. Filtra con **Policy Gate** (allowlist, max notional, rischio, R/R, kill switch)
5. Esito: `PROPOSE` · `PAPER` · `SKIP` · `BLOCKED`
6. **GUI** Streamlit con grafici e statistiche

## Installazione (copia-incolla)

```bash
git clone https://github.com/dekoivvkw-netizen/decision-bot.git
cd decision-bot
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Serve anche la CLI **revx** configurata per i dati live Revolut X.

## Avvio

```bash
# Decisioni in terminale
python -m revolutx_bot decide
python -m revolutx_bot decide --paper

# GUI (browser → http://localhost:8501)
python -m revolutx_bot gui

# Stato policy + paper + audit
python -m revolutx_bot stato
```

## Struttura

```
revolutx_bot/
  decision_engine.py   # decide tutto
  strategy.py          # trend + Bollinger MR
  indicators.py        # EMA RSI ATR BB
  policy.py            # gate rischio
  paper.py             # ledger simulazione
  gui.py               # dashboard grafici
  cli.py               # comandi
config.toml            # coppie, capitale, policy
```

## Configurazione

Modifica `config.toml`:

- `[segnali]` — coppie e modalità (`conservative` / `precise` / `balanced`)
- `[capitale]` — EUR e rischio %
- `[policy]` — kill_switch, max_trade_notional, allowlist

## Sicurezza

- Nessuna chiave API nel codice
- Kill switch in config
- Fail-closed se dati o vincoli mancano
- Paper e audit solo locali (`state/`, non in git)
- Ordini reali solo a mano (comando `revx` stampato nella proposta)

**Prima il controllo, poi l'autonomia.**
