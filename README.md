# Decision Bot · Revolut X

**Software reale e pubblico** di trading decisionale.

> Non è un consiglio finanziario. **Non piazza ordini reali in automatico.**

**https://github.com/dekoivvkw-netizen/decision-bot**

## Installazione

```bash
git clone https://github.com/dekoivvkw-netizen/decision-bot.git
cd decision-bot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Serve la CLI **revx** per i dati live Revolut X.

## Comandi

| Comando | Cosa fa |
|---------|---------|
| `python -m revolutx_bot decide` | Analizza e decide |
| `python -m revolutx_bot decide --paper` | Decide + paper se gate OK |
| `python -m revolutx_bot gui` | Dashboard grafici (localhost:8501) |
| `python -m revolutx_bot stato` | Policy + paper + audit |
| `python -m revolutx_bot segnali` | Solo segnali |
| `bash AVVIA.sh` | Menu interattivo |

Guide: [START.md](START.md) · [LOOP.md](LOOP.md)

## Architettura

```
revx (lettura) → indicatori (EMA/RSI/ATR/BB)
               → decide (trend | mean-reversion)
               → policy gate
               → PROPOSE | PAPER | SKIP | BLOCKED
               → audit + GUI
```

## Test

```bash
pip install pytest
python -m pytest -q
```

## Sicurezza

- Kill switch in `config.toml`
- Allowlist coppie
- Max notional / rischio / R/R
- Ordini reali solo a mano via comando stampato

**Prima il controllo, poi l'autonomia.**
