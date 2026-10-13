# DECISION BOT — MASTER
Documento unico: tutto il progetto in un file.
Repo: https://github.com/dekoivvkw-netizen/decision-bot
Data: 2026-10-13

---

## 1. COS'È

Decision Bot v1.1.0 — bot di trading che:
- legge candele da Revolut X (sola lettura, via CLI revx)
- calcola indicatori: EMA, RSI, ATR, Bollinger (20, ±2σ)
- decide COMPRA / VENDI / NEUTRO con due percorsi:
  1) TREND (priorità): EMA + RSI + conferme + ATR vivo
  2) MEAN-REVERSION (secondario, solo se trend NEUTRO): RSI oversold/overbought + prezzo fuori banda Bollinger
- applica un Policy Gate deterministico (allowlist, notional, risk %, R/R, kill switch)
- registra proposte in paper ledger + audit.jsonl
- NON piazza ordini reali: solo stampa, paper o blocco

---

## 2. ARCHITETTURA

COGNITIVO                         OPERATIVO
─────────                         ─────────
indicatori / Bollinger       →    policy gate
strategy.decide              →    constraints broker
  ├─ trend (1°)              →    proposal (solo stampa)
  └─ mean-reversion (2°)     →    paper ledger
                                  audit.jsonl
                                  status / GUI

Regola guida multi-agente: un solo ruolo cognitivo (decide), tutto il resto deterministico.

---

## 3. COMPONENTI

| Componente | File / comando | Funzione |
|------------|---------------|----------|
| Decision engine | revolutx_bot/decision_engine.py | decide COMPRA/VENDI/NEUTRO |
| Indicatori | revolutx_bot/indicators.py | EMA, RSI, ATR, Bollinger |
| Strategia | revolutx_bot/strategy.py | trend + mean-reversion |
| Policy gate | revolutx_bot/policy.py | allowlist, notional, risk, R/R, kill switch |
| Audit | revolutx_bot/audit.py | log append-only state/audit.jsonl |
| Paper ledger | revolutx_bot/paper.py | ordini simulati, chiusura TP/SL |
| CLI | python -m revolutx_bot | decide, proponi, paper, stato, paper-chiudi |
| GUI | python -m revolutx_bot gui | Streamlit: dashboard, grafici, paper, audit |
| Config | config.toml | coppie, capitale, policy, percorso revx |
| CI | .github/workflows/ci.yml | pytest su ogni push |
| Loop | decide --paper --loop 15 | analisi ogni 15 min |

---

## 4. SOGLIE MEAN-REVERSION

| Modalità | Oversold | Overbought |
|----------|----------|------------|
| conservative | 25 | 75 |
| precise | 28 | 72 |
| balanced | 30 | 70 |

---

## 5. COMANDI (sul server)

cd decision-bot
source .venv/bin/activate

# una scansione
python -m revolutx_bot decide

# registra in paper se il gate è OK
python -m revolutx_bot decide --paper

# loop continuo ogni 15 minuti
python -m revolutx_bot decide --paper --loop 15

# GUI (browser)
python -m revolutx_bot gui
# oppure in rete locale:
streamlit run revolutx_bot/gui.py --server.address 0.0.0.0 --server.port 8501

# paper ledger
python -m revolutx_bot paper

# chiudi un paper a target / stop / prezzo manuale
python -m revolutx_bot paper-chiudi --indice 1 --target
python -m revolutx_bot paper-chiudi --coppia ETH-EUR --stop
python -m revolutx_bot paper-chiudi --indice 1 --prezzo 5.25

# panoramica: policy, kill switch, paper, audit
python -m revolutx_bot stato

# test
pytest -q

---

## 6. CONFIG.TOML (esempio)

[general]
capital = 1000.0
mode = "conservative"

[policy]
allowlist = ["BTC-EUR", "ETH-EUR", "DOT-EUR", "ATOM-EUR"]
max_trade_notional = 150.0
max_risk_pct = 2.0
min_rr_ratio = 1.2
kill_switch = false

[revx]
# percorso CLI revx già autenticata (sola lettura)
cli_path = "revx"

---

## 7. SETUP VPS (Contabo Cloud VPS 4, ~5,50 €/mese)

1. Compra su https://www.contabo.com (piano Cloud VPS 4, Ubuntu 24.04).
   Ricevi IP pubblico + password root.
2. Sul Fold7: Play Store → Termius (gratis). Nuova connessione:
   host = IP, utente = root, password = quella ricevuta.
3. Sul server, incolla:

   apt update && apt upgrade -y
   apt install -y python3 python3-venv python3-pip git nginx apache2-utils
   adduser --disabled-password --gecos "" bot
   su - bot
   git clone https://github.com/dekoivvkw-netizen/decision-bot.git
   cd decision-bot
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

4. Configura revx sul server (stesso metodo del PC, sola lettura).
   NON mettere chiavi API in Git né in chat.
5. Crea /etc/systemd/system/decision-bot.service:

   [Unit]
   Description=Decision Bot loop
   After=network.target

   [Service]
   User=bot
   WorkingDirectory=/home/bot/decision-bot
   ExecStart=/home/bot/decision-bot/.venv/bin/python -m revolutx_bot decide --paper --loop 15
   Restart=always
   RestartSec=30

   [Install]
   WantedBy=multi-user.target

   systemctl daemon-reload
   systemctl enable --now decision-bot
   systemctl status decision-bot

6. GUI dietro Nginx + password:
   - systemd decision-gui.service: streamlit run revolutx_bot/gui.py
     --server.port 8501 --server.address 127.0.0.1
   - htpasswd -c /etc/nginx/.htpasswd tuo_utente
   - server Nginx: listen 80, auth_basic, proxy_pass http://127.0.0.1:8501
   - ufw allow 22,80,443/tcp && ufw enable
   - nginx -t && systemctl reload nginx
7. Dal Fold7: Chrome → http://IP-DEL-SERVER (login) → Dashboard / Decisioni / Grafici / Paper.
8. Opzionale: HTTPS con dominio + certbot.

---

## 8. DISPOSITIVI

| Dispositivo | Ruolo |
|-------------|-------|
| VPS (Contabo) | Motore: bot, revx, paper, GUI |
| Samsung Z Fold7 | Schermo/telecomando: browser GUI + Termius SSH + Revolut |
| iPhone | Controllo rapido: browser GUI + chat |
| Laptop (opzionale) | Alternativa al VPS se resta acceso |

Nota: il Fold7 acceso 24/7 NON sostituisce il VPS — Android sospende le app.
Il bot gira sul server; il telefono è solo il pannello di controllo.

---

## 9. SICUREZZA

- Solo 127.0.0.1:8501 esposto, GUI protetta da basic auth
- kill_switch = true se non operi
- Firewall: apri solo 22, 80, 443
- Chiavi revx solo sul server, mai in Git
- Backup periodico di state/ (paper + audit)
- Ordini reali SOLO manuali su Revolut, mai automatici

---

## 10. REGOLE D'ORO

1. Il bot decide e propone. Tu confermi.
2. Nessun ordine reale automatico, mai.
3. Sotto 3 € di utile stimato: non comprare.
4. Non pubblicare difetti non visibili in foto (moda) / non dichiarati (trading).
5. Prima paper stabile, poi kill switch collaudato, poi eventuale live.

---

## 11. LINK

- Repo pubblico: https://github.com/dekoivvkw-netizen/decision-bot
- Repo privato (archivio): https://github.com/dekoivvkw-netizen/trading-bots
- VPS: https://www.contabo.com
- SSH dal Fold7: app Termius
- GUI: http://IP-DEL-SERVER

---

Fine del MASTER. Tutto il progetto è qui.
