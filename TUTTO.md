# Decision Bot — tutto in un file

Scarica questo repo sul Z Fold7 / PC / VPS.
Link: https://github.com/dekoivvkw-netizen/decision-bot

> Non è un consiglio finanziario. Il bot **non piazza ordini reali**. Solo analisi + paper.

---

## 1. Cosa serve

| Cosa | Dove |
|------|------|
| VPS Linux (~5–6 €/mese) | Contabo Cloud VPS 4 → https://www.contabo.com |
| Oppure PC acceso | laptop |
| Termius (SSH) | Play Store sul Fold7 |
| Browser | Chrome / Samsung Internet |
| CLI `revx` autenticata | sul VPS o PC (sola lettura Revolut X) |
| Questo repo | git clone |

---

## 2. Compra VPS (dal Fold7)

1. Chrome → https://www.contabo.com  
2. Cloud VPS 4 (4 vCPU, 8 GB RAM)  
3. Paga (carta / PayPal)  
4. Mail: **IP** + password **root**

Alternativa: https://www.hetzner.com/cloud → CX23 (~6 €/mese)

---

## 3. Collegati (Termius)

1. Play Store → **Termius**  
2. Nuovo host → IP del server, user `root`, password  
3. Connetti

---

## 4. Installazione (incolla in Termius)

```bash
apt update && apt upgrade -y
apt install -y python3 python3-venv python3-pip git nginx apache2-utils ufw
adduser --disabled-password --gecos "" bot
su - bot
git clone https://github.com/dekoivvkw-netizen/decision-bot.git
cd decision-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.toml.example config.toml   # se esiste, altrimenti usa config.toml già presente
exit
```

---

## 5. Config (`config.toml`)

```toml
[segnali]
coppie = ["DOT-EUR", "ATOM-EUR", "ETH-EUR", "BTC-EUR"]
modalita = "conservative"   # conservative | precise | balanced
intervallo_veloce = "15m"
storico_veloce = "5d"
intervallo_lento = "1h"
storico_lento = "20d"

[capitale]
eur = 100.0
rischio_per_trade_pct = 1.0
max_posizione_pct = 50.0

[policy]
max_trade_notional = 150.0
max_position_pct = 50.0
max_risk_pct = 2.0
min_rr_ratio = 1.2
max_spread_bps = 50.0
proposal_ttl_minutes = 15
kill_switch = false
allowlist = ["BTC-EUR", "ETH-EUR", "DOT-EUR", "ATOM-EUR"]

[revx]
percorso = "~/.local/bin/revx"
```

- `kill_switch = true` → blocca tutte le proposte  
- Credenziali **solo** in `revx`, mai in questo file  

---

## 6. revx sul server

Installa e autentica la CLI Revolut X **sul VPS** (stesso procedimento del PC).  
Senza `revx` non ci sono candele live → niente segnali reali.

---

## 7. Bot sempre acceso (systemd)

```bash
cat > /etc/systemd/system/decision-bot.service << 'EOF'
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
EOF

systemctl daemon-reload
systemctl enable --now decision-bot
systemctl status decision-bot
```

---

## 8. GUI + password (Nginx)

```bash
cat > /etc/systemd/system/decision-gui.service << 'EOF'
[Unit]
Description=Decision Bot GUI
After=network.target

[Service]
User=bot
WorkingDirectory=/home/bot/decision-bot
ExecStart=/home/bot/decision-bot/.venv/bin/streamlit run revolutx_bot/gui.py --server.port 8501 --server.address 127.0.0.1 --browser.gatherUsageStats false
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl enable --now decision-gui

htpasswd -c /etc/nginx/.htpasswd tuo_utente

cat > /etc/nginx/sites-available/decision-bot << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        auth_basic "Decision Bot";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
EOF

ln -sf /etc/nginx/sites-available/decision-bot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
ufw allow 22,80,443/tcp
ufw --force enable
nginx -t && systemctl reload nginx
```

Dal Fold7: Chrome → `http://IP-DEL-SERVER` → login → Dashboard.

---

## 9. Comandi utili

```bash
su - bot
cd decision-bot && source .venv/bin/activate

python -m revolutx_bot decide
python -m revolutx_bot decide --paper
python -m revolutx_bot decide --paper --loop 15
python -m revolutx_bot paper
python -m revolutx_bot paper-chiudi --indice 1 --target
python -m revolutx_bot stato
python -m revolutx_bot gui

systemctl status decision-bot
journalctl -u decision-bot -f
```

---

## 10. Cosa fa il bot

```
revx (lettura) → EMA/RSI/ATR/Bollinger
  → decide: TREND oppure MEAN-REVERSION
  → policy gate (allowlist, notional, rischio, R/R, kill switch)
  → PROPOSE | PAPER | SKIP | BLOCKED
  → state/paper.jsonl + state/audit.jsonl
```

Ordini **reali**: solo a mano in Revolut, se accetti la proposta stampata.

---

## 11. Sicurezza

- Non esporre la porta 8501 su internet (solo 127.0.0.1 + Nginx + password)
- `kill_switch = true` quando non operi
- Backup cartella `state/`
- Chiavi solo in revx, mai in Git

---

## 12. Dove comprare / link

| Cosa | Link |
|------|------|
| VPS Contabo | https://www.contabo.com |
| VPS Hetzner | https://www.hetzner.com/cloud |
| Repo bot | https://github.com/dekoivvkw-netizen/decision-bot |
| Termius | Play Store |
| Termux (opzionale) | Play Store |

**Prima il controllo, poi l'autonomia.**
