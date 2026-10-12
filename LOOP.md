# Loop continuo (24/7) — Decision Bot

Il bot **non** apre ordini reali in automatico. Il loop ripete solo analisi / paper.

## Opzione A — CLI loop

```bash
cd decision-bot
source .venv/bin/activate
# ogni 15 minuti, registra paper se gate OK
python -m revolutx_bot decide --paper
# (se vuoi loop nativo, usa nohup + while)
while true; do
  python -m revolutx_bot decide --paper
  sleep 900
done
```

In background:

```bash
nohup bash -c 'while true; do python -m revolutx_bot decide --paper; sleep 900; done' > bot.log 2>&1 &
```

## Opzione B — cron (Linux/Mac)

```cron
*/15 * * * * cd /path/to/decision-bot && .venv/bin/python -m revolutx_bot decide --paper >> /path/to/bot.log 2>&1
```

## Opzione C — GUI sempre aperta

```bash
python -m revolutx_bot gui
```

Dalla pagina **Decisioni** puoi rilanciare a mano.

## Kill switch

In `config.toml`:

```toml
[policy]
kill_switch = true
```

Nessuna proposta/paper accettata finché resta `true`.

## Log

- `state/audit.jsonl` — ogni segnale/proposta
- `state/paper.jsonl` — ledger simulato
- `state/paper_equity.json` — equity
