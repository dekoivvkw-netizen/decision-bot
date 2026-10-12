#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  .venv/bin/pip install -U pip
  .venv/bin/pip install -r requirements.txt
fi
echo "1) decide  2) decide --paper  3) gui  4) stato"
read -r c
case "$c" in
  1) .venv/bin/python -m revolutx_bot decide ;;
  2) .venv/bin/python -m revolutx_bot decide --paper ;;
  3) .venv/bin/python -m revolutx_bot gui ;;
  4) .venv/bin/python -m revolutx_bot stato ;;
  *) echo "scelta non valida" ;;
esac
