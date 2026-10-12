# Avvio Decision Bot (vero)

Repo pubblico: https://github.com/dekoivvkw-netizen/decision-bot

## 1. Clona e installa

```bash
git clone https://github.com/dekoivvkw-netizen/decision-bot.git
cd decision-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Configura Revolut X (dati live)

Serve la CLI `revx` autenticata sul tuo PC (sola lettura basta per i segnali).

In `config.toml` controlla:

```toml
[revx]
percorso = "~/.local/bin/revx"
```

## 3. Comandi

```bash
# Il bot decide su tutte le coppie
python -m revolutx_bot decide

# Decide e registra in paper se il gate è OK
python -m revolutx_bot decide --paper

# GUI grafici + stats
python -m revolutx_bot gui
# → http://localhost:8501

# Stato policy + paper
python -m revolutx_bot stato
```

Oppure: `bash AVVIA.sh`

## Sicurezza

- Nessun ordine automatico sul broker
- Kill switch in `config.toml` → `[policy] kill_switch = true`
- Paper e audit solo in cartella locale `state/`
