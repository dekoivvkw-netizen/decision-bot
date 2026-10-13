# Wolf Scout — API + Mobile

## 1. Chiave eBay (gratis)
1. Vai su https://developer.ebay.com
2. Crea account developer → **Application Keys**
3. Copia **App ID (Client ID)** sandbox o production
4. Per l’Italia usa production + `EBAY_GLOBAL_ID=EBAY-IT`

## 2. Sul VPS
```bash
cd /home/bot
# cartella wolf-scout da questo repo
python3 -m venv .venv-scout
source .venv-scout/bin/activate
pip install -r requirements-scout.txt

export EBAY_APP_ID="IL_TUO_APP_ID"
export EBAY_GLOBAL_ID="EBAY-IT"

python scout_api.py
# porta 8787
```

### systemd
```ini
[Unit]
Description=Wolf Scout API
After=network.target

[Service]
User=bot
WorkingDirectory=/home/bot/decision-bot/wolf-scout
Environment=EBAY_APP_ID=INSERISCI
Environment=EBAY_GLOBAL_ID=EBAY-IT
ExecStart=/home/bot/decision-bot/wolf-scout/.venv-scout/bin/python scout_api.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 3. Nginx
```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8787/api/;
}
location /health {
    proxy_pass http://127.0.0.1:8787/health;
}
```

## 4. Mobile Fold7
Apri `wolf-scout-mobile.html` e imposta:
`API_BASE = http://IP:8787` oppure `https://tuo-dominio`

## Endpoint
- `GET /health`
- `GET /api/scout?q=borsetta+pelle&min=20&max=80&limit=20`

Rivendita stimata: moltiplicatore `SCOUT_RESALE_MULT` (default 2.0).
